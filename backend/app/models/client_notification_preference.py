from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Boolean, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from .enums import NotificationChannel, NotificationChannelEnum

if TYPE_CHECKING:
    from .client import Client


class ClientNotificationPreference(BaseModel):
    __tablename__ = "client_notification_preferences"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        NotificationChannelEnum, nullable=False
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    client: Mapped["Client"] = relationship(
        "Client", back_populates="notification_preferences"
    )

    __table_args__ = (UniqueConstraint("client_id", "channel"),)
