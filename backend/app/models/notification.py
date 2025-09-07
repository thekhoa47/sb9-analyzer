from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


NotificationChannel = Enum("sms", "email", "messenger", name="notification_channel")
NotificationStatus = Enum("sent", "failed", name="notification_status")


class Notification(BaseModel):
    __tablename__ = "notifications"

    channel: Mapped[str] = mapped_column(NotificationChannel, nullable=False)
    status: Mapped[str] = mapped_column(
        NotificationStatus, nullable=False, default="sent"
    )

    listing_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    detail: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    client_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL")
    )
    saved_search_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("saved_searches.id", ondelete="SET NULL")
    )
