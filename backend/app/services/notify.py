from twilio.rest import Client as TwilioClient
import requests
from ..config import settings

twilio = TwilioClient(settings.TWILIO_SID, settings.TWILIO_TOKEN)

def send_sms(to: str, body: str) -> str:
    if not (settings.TWILIO_SID and settings.TWILIO_TOKEN and settings.TWILIO_FROM):
        return "skipped"
    msg = twilio.messages.create(to=to, from_=settings.TWILIO_FROM, body=body)
    return msg.sid

def send_messenger(psid: str, text: str) -> str:
    if not (settings.PAGE_TOKEN and psid):
        return "skipped"
    r = requests.post(
        f"https://graph.facebook.com/v21.0/me/messages?access_token={settings.PAGE_TOKEN}",
        json={
            "recipient":{"id":psid},
            "messaging_type":"MESSAGE_TAG",
            "tag":"ACCOUNT_UPDATE",
            "message":{"text":text}
        },
        timeout=15
    )
    if r.ok:
        return "sent"
    return f"failed:{r.status_code}"
