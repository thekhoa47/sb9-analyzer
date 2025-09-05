# app/services/email/providers/gmail.py
import os
import asyncio
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Optional

class GmailSMTPProvider:
    def __init__(self):
        self.host = "smtp.gmail.com"
        self.port = 587
        self.username = os.environ["GMAIL_USER"]
        self.password = os.environ["GMAIL_PASS"]
        self.from_email = os.environ["EMAIL_FROM"]
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Deal Alerts")

    async def send(self, to_email: str, subject: str, html: str, text: Optional[str] = None):
        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if text:
            msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        # Send via Gmail SMTP
        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            start_tls=True,
            username=self.username,
            password=self.password,
        )

    async def send_bulk(self, items: Iterable[tuple[str, str, str, Optional[str]]], concurrency: int = 5):
        # items: (to_email, subject, html, text)
        sem = asyncio.Semaphore(concurrency)

        async def worker(i):
            async with sem:
                to_email, subject, html, text = i
                await self.send(to_email, subject, html, text)

        await asyncio.gather(*(worker(i) for i in items))
