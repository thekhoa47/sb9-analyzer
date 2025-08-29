# app/routers/messenger_webhook.py
from __future__ import annotations
import hmac, hashlib, json
from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.db import SessionLocal
from app.models import Client   # adjust to your paths

router = APIRouter(prefix="/webhooks/messenger", tags=["messenger"])

@router.get("")
async def verify(mode: str, challenge: str, verify_token: str):
    if mode == "subscribe" and verify_token == settings.VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

def _verify_signature(request: Request, body: bytes):
    sig = request.headers.get("X-Hub-Signature-256")
    if not sig or not settings.APP_SECRET:
        return
    mac = hmac.new(settings.APP_SECRET.encode(), msg=body, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=403, detail="Bad signature")

@router.post("")
async def receive(request: Request):
    body = await request.body()
    _verify_signature(request, body)
    data = json.loads(body.decode("utf-8"))

    # Example event shape:
    # { "object":"page","entry":[{"messaging":[{"sender":{"id":"<PSID>"},"message":{"text":"hi"}}]}]}
    if data.get("object") != "page":
        return {"status": "ignored"}

    db = SessionLocal()
    try:
        for entry in data.get("entry", []):
            for m in entry.get("messaging", []):
                psid = m.get("sender", {}).get("id")
                if not psid:
                    continue
                # TODO: resolve who this is (e.g., by email/phone you already know)
                # For demo: upsert a Client row with this psid
                # (Add your own matching logic; this just shows where to store PSID)
                # client = db.query(Client).filter_by(messenger_psid=psid).first()
                # if not client:
                #     client = Client(name="Messenger lead", messenger_psid=psid, messenger_opt_in=True)
                #     db.add(client); db.commit()
                # Optionally reply here.
        return {"status": "ok"}
    finally:
        db.close()
