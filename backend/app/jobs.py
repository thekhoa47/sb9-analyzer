# app/jobs.py
from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import SavedSearch, Listing, SentNotification, Client
from app.models.enums import NotificationChannel
from app.services.reso import poll_reso
from app.services.analyze_listing import analyze_listing
from app.services.zillow_redfin import fetch_listings_via_gpt
from app.services.gmail import GmailSMTPProvider
from app.services.notify import send_sms

log = logging.getLogger("sb9.jobs")

# simple in-memory status
_last = {
    "at": None,  # ISO time of last run
    "searched": 0,  # saved searches processed
    "new": 0,  # new listings found
    "error": None,  # last error message (if any)
}


def _run_saved_search(search: SavedSearch, db: Session) -> int:
    """
    Runs one saved search: poll RESO, analyze, notify, dedupe via Listing,
    advance the cursor. Returns count of new listings processed.
    """
    since_iso = search.cursor_iso or datetime.now(timezone.utc).isoformat()

    listings = poll_reso(
        city=search.city,
        beds_min=search.beds_min,
        baths_min=search.baths_min,
        max_price=search.max_price,
        since_iso=since_iso,
    )

    new_count = 0
    email_items: list[tuple[str, str, str, Optional[str]]] = []  # NEW
    client: Optional[Client] = (
        db.get(Client, search.client_id) if getattr(search, "client_id", None) else None
    )

    for L in listings:
        key = str(L.get("ListingKey") or L.get("ListingId") or "")
        if not key:
            continue

        # dedupe per saved_search
        exists = (
            db.query(Listing)
            .filter_by(listing_key=key, saved_search_id=search.id)
            .first()
        )
        if exists:
            continue

        # analyze
        analysis = analyze_listing(L)
        msg = (
            f"New: {L.get('UnparsedAddress')} • ${int(L.get('ListPrice') or 0):,} "
            f"• Score {analysis['score']}\n{analysis['summary']}"
        )

        # notify (only if channels are set and opted-in)
        if client:
            if client and client.email and client.email_opt_in:
                subject, html, text = _compose_email(L, analysis, search)  # NEW
                email_items.append((client.email, subject, html, text))  # NEW
                db.add(
                    SentNotification(  # NEW: record intent to send
                        channel=NotificationChannel.EMAIL,
                        status="queued",
                        detail="gmail",
                        client_id=client.id,
                        saved_search_id=search.id,
                    )
                )
            if client.phone and client.sms_opt_in:
                sid = send_sms(client.phone, msg)
                db.add(
                    SentNotification(
                        channel=NotificationChannel.SMS,
                        listing_key=key,
                        status="sent",
                        detail=str(sid),
                        client_id=client.id,
                        saved_search_id=search.id,
                    )
                )

        # mark seen & persist
        db.add(Listing(listing_key=key, saved_search_id=search.id))
        db.commit()
        new_count += 1

    # advance cursor AFTER processing
    search.cursor_iso = datetime.now(timezone.utc).isoformat()
    db.commit()

    # === SEND EMAILS in one batch for this search ===
    if email_items:
        provider = GmailSMTPProvider()  # NEW
        # If no running loop (e.g., Windows Task Scheduler), asyncio.run is perfect.
        # If you later run under AsyncIOScheduler loop, this still works in trigger_poll_once().
        asyncio.run(provider.send_bulk(email_items, concurrency=3))  # NEW

        # Update notification rows to 'sent'
        for item in email_items:
            to_email, subject, *_ = item
            db.query(SentNotification).filter_by(
                channel="email", saved_search_id=search.id, status="queued"
            ).update({"status": "sent", "detail": f"gmail to {to_email}"})
        db.commit()

    return new_count


def _run_saved_search_gpt(search: SavedSearch, db: Session) -> int:
    """
    Same logic as _run_saved_search, but fetches listings from GPT instead of RESO.
    """
    listings = fetch_listings_via_gpt(search)
    new_count = 0
    email_items: list[dict] = []
    client: Optional[Client] = (
        db.get(Client, search.client_id) if getattr(search, "client_id", None) else None
    )

    for L in listings:
        key = str(L.get("ListingKey") or L.get("UnparsedAddress") or "")
        if not key:
            continue

        # dedupe
        exists = (
            db.query(Listing)
            .filter_by(listing_key=key, saved_search_id=search.id)
            .first()
        )
        if exists:
            continue

        # analyze
        analysis = analyze_listing(L)
        msg = (
            f"New: {L.get('UnparsedAddress')} • ${int(L.get('ListPrice') or 0):,} "
            f"• Score {analysis['score']}\n{analysis['summary']}"
        )

        # notify
        if client:
            if client.email and client.email_opt_in:
                subject, html, text = _compose_email(L, analysis, search)  # NEW
                email_items.append(
                    {
                        "to": client.email,
                        "subject": subject,
                        "html": html,
                        "text": text,
                        "listing_key": key,
                    }
                )

        # mark seen
        db.add(Listing(listing_key=key, saved_search_id=search.id))
        db.commit()
        new_count += 1

    # update cursor (optional — doesn’t apply well to GPT since it’s not time-sliced)
    search.cursor_iso = datetime.now(timezone.utc).isoformat()
    db.commit()

    if email_items:
        provider = GmailSMTPProvider()
        to_send = [
            (i["to"], i["subject"], i["html"], i.get("text")) for i in email_items
        ]

        try:
            asyncio.run(provider.send_bulk(to_send, concurrency=3))

            for i in email_items:
                db.add(
                    SentNotification(
                        channel="email",
                        status="sent",
                        listing_key=i["listing_key"],
                        detail=f"gmail to {i['to']}",
                        client_id=client.id,
                        saved_search_id=search.id,
                    )
                )
            db.commit()

        except Exception as e:
            for i in email_items:
                db.add(
                    SentNotification(
                        channel="email",
                        status="failed",
                        listing_key=i["listing_key"],
                        detail=f"gmail error: {e}",
                        client_id=client.id,
                        saved_search_id=search.id,
                    )
                )
            db.commit()
            raise

    return new_count


def _compose_email(
    listing: dict, analysis: dict, search: SavedSearch
) -> tuple[str, str, str]:
    title = listing.get("UnparsedAddress") or listing.get("ListingKey") or "New Listing"
    price = int(listing.get("ListPrice") or 0)
    subject = f"[Deal Alert] {title} • ${price:,} • Score {analysis.get('score')}"

    summary = analysis.get("summary") or ""
    address = listing.get("UnparsedAddress", "Address N/A")
    url = listing.get("ListingURL") or listing.get("Url") or ""  # if you have one
    html = f"""
    <div style="font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;max-width:640px;margin:auto">
      <h2 style="margin:0 0 8px">{address}</h2>
      <p style="margin:0 0 8px"><strong>List Price:</strong> ${price:,}</p>
      <p style="white-space:pre-wrap">{summary}</p>
      {f'<p><a href="{url}">View listing</a></p>' if url else ""}
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>
      <p style="color:#666;font-size:12px">You’re receiving this because you opted in to email alerts.</p>
    </div>
    """
    text = f"""{address}
List Price: ${price:,}

{summary}

{("View listing: " + url) if url else ""}""".strip()
    return subject, html, text
