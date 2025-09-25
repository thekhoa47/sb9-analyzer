# app/routers/messenger_webhook.py
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from app.core import settings

log = logging.getLogger("sb9.messenger")
router = APIRouter(prefix="/webhooks/messenger", tags=["messenger"])

# --- GET: Verification (FB calls this once when you click "Verify and Save") ---


@router.get("", response_class=PlainTextResponse)
@router.get("", response_class=PlainTextResponse)  # handle trailing slash too
async def verify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        # MUST return the raw challenge as text/plain
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


# --- POST: Message events (deliveries, incoming messages, postbacks, etc.) ---


def _verify_signature(request: Request, body: bytes):
    sig = request.headers.get("X-Hub-Signature-256")
    if not sig:
        return  # Meta may not send during dev; skip hard fail
    if not settings.APP_SECRET:
        return
    mac = hmac.new(settings.APP_SECRET.encode(), msg=body, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=403, detail="Bad signature")


@router.post("")
@router.post("")
async def receive(request: Request):
    body = await request.body()
    _verify_signature(request, body)
    data = json.loads(body.decode("utf-8"))

    if data.get("object") != "page":
        return {"status": "ignored"}

    # Handle entries/messages
    for entry in data.get("entry", []):
        for m in entry.get("messaging", []):
            psid = m.get("sender", {}).get("id")
            text = (m.get("message") or {}).get("text")
            log.info("Incoming message from %s: %r", psid, text)
            # TODO: upsert client with this PSID, respond, etc.

    # Return 200 fast so Meta is happy
    return {"status": "ok"}
