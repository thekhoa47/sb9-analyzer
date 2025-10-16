# app/services/notifications.py
from __future__ import annotations

import os
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable
from uuid import UUID

import aiosmtplib
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client as TwilioClient

import app.models as m
from app.core.config import settings


# =========================
# SMS via Twilio
# =========================

_twilio_client: TwilioClient | None = None
if settings.TWILIO_SID and settings.TWILIO_TOKEN:
    _twilio_client = TwilioClient(settings.TWILIO_SID, settings.TWILIO_TOKEN)


def send_sms_sync(to: str, body: str) -> str:
    """
    Synchronous Twilio send. Returns message SID or 'skipped'.
    """
    if not (_twilio_client and settings.TWILIO_FROM):
        return "skipped"
    msg = _twilio_client.messages.create(to=to, from_=settings.TWILIO_FROM, body=body)
    return msg.sid


async def send_sms(to: str, body: str) -> str:
    """
    Async wrapper so we don't block the event loop on HTTP I/O from Twilio.
    """
    return await asyncio.to_thread(send_sms_sync, to, body)


# =========================
# Email via Gmail SMTP
# =========================


class GmailSMTPProvider:
    def __init__(self):
        self.host = "smtp.gmail.com"
        self.port = 587
        self.username = os.environ.get("GMAIL_USER")
        self.password = os.environ.get("GMAIL_PASS")
        self.from_email = os.environ.get("EMAIL_FROM")
        self.from_name = os.environ.get("EMAIL_FROM_NAME", "Deal Alerts")

    async def send(
        self, to_email: str, subject: str, html: str, text: str | None = None
    ):
        if not (self.username and self.password and self.from_email):
            # Treat missing creds as a no-op rather than raising in prod paths
            return "skipped"

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if text:
            msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            start_tls=True,
            username=self.username,
            password=self.password,
        )
        return "sent"

    async def send_bulk(
        self, items: Iterable[tuple[str, str, str, str | None]], concurrency: int = 5
    ):
        # items: (to_email, subject, html, text)
        sem = asyncio.Semaphore(concurrency)

        async def worker(i: tuple[str, str, str, str | None]):
            async with sem:
                to_email, subject, html, text = i
                await self.send(to_email, subject, html, text)

        await asyncio.gather(*(worker(i) for i in items))


_gmail = GmailSMTPProvider()


async def send_email(
    to: str, subject: str, body_text: str, body_html: str | None = None
):
    """
    Convenience wrapper. If body_html not provided, derive a minimal HTML from text.
    """
    html = (
        body_html
        or f"<pre style='font: 14px/1.4 -apple-system, Segoe UI, Roboto, Helvetica, Arial'>{body_text}</pre>"
    )
    return await _gmail.send(to_email=to, subject=subject, html=html, text=body_text)


# =========================
# High-level notification orchestrator
# =========================


def _compose_summary(
    listing: m.Listing, sla: m.SearchListingAnalysis
) -> tuple[str, str]:
    """
    Returns (text, html)
    """
    text = f"""
        New promising listing ${listing.listing_price}
        {listing.property.address_line1} {listing.property.address_line2},
        {listing.property.city}, {listing.property.state} {listing.property.zip}
        
        {sla.llm_summary}
        """
    html = f"""
        <html>
        <body style="font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial; line-height:1.45">
            <p>✅ <strong>New promising listing</strong></p>
            <p>
            {listing.property.address_line1} {listing.property.address_line2} <br/>
            {listing.property.city}, {listing.property.state} {listing.property.zip}<br/>
            <strong>Price:</strong> ${listing.listing_price}
            </p>
            <p><strong>Summary</strong><br/>{sla.llm_summary}</p>
            <p><strong>Reasons</strong>{sla.llm_analysis}</p>
        </body>
        </html>
    """
    return text, html


async def notify_client_for_good_listing(
    *,
    session: AsyncSession,
    saved_search_id: UUID,
    listing_id: UUID,
    search_listing_analysis_id: UUID,
) -> None:
    """
    Sends notifications to the client for a 'good' listing verdict,
    honoring ClientNotificationPreference and ensuring idempotency
    via ListingNotification (client_id, listing_id) uniqueness.
    """
    saved_search = await session.get(m.SavedSearch, saved_search_id)
    listing = await session.get(
        m.Listing, listing_id, options=[joinedload(m.Listing.property)]
    )
    sla = await session.get(m.SearchListingAnalysis, search_listing_analysis_id)
    # Resolve client
    client = await session.get(m.Client, saved_search.client_id)
    if not client:
        return

    # Idempotency: if already notified, skip
    existing = (
        await session.execute(
            select(m.SentNotification).where(
                and_(
                    m.SentNotification.client_id == client.id,
                    m.SentNotification.listing_id == listing_id,
                    m.SentNotification.saved_search_id == saved_search.id,
                )
            )
        )
    ).scalar_one_or_none()
    if existing:
        return

    # Load preferences (email / sms)
    prefs = (
        (
            await session.execute(
                select(m.ClientNotificationPreference).where(
                    m.ClientNotificationPreference.client_id == client.id
                )
            )
        )
        .scalars()
        .all()
    )

    # Compose message
    text, html = _compose_summary(listing, sla)
    subject = "New promising listing"

    # Dispatch by channel, only if enabled and contact info exists
    for p in prefs:
        if not p.enabled:
            continue
        if p.channel == "EMAIL" and getattr(client, "email", None):
            await send_email(
                to=client.email, subject=subject, body_text=text, body_html=html
            )
            session.add(
                m.SentNotification(
                    client_id=client.id,
                    listing_id=listing_id,
                    saved_search_id=saved_search.id,
                    channel="EMAIL",
                    status="SENT",
                    to=client.email,
                    body=text,
                )
            )

        if p.channel == "sms" and getattr(client, "phone", None):
            await send_sms(to=client.phone, body=text)
            session.add(
                m.SentNotification(
                    client_id=client.id,
                    listing_id=listing_id,
                    saved_search_id=saved_search.id,
                    channel="SMS",
                    status="SENT",
                    to=client.email,
                    body=text,
                )
            )

    await session.commit()
