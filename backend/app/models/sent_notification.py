from __future__ import annotations
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, TYPE_CHECKING
import uuid
from .base import BaseModel
from .enums import (
    NotificationChannel,
    NotificationChannelEnum,
    NotificationStatus,
    NotificationStatusEnum,
)

if TYPE_CHECKING:
    from .client import Client
    from .listing import Listing
    from .saved_search import SavedSearch


class SentNotification(BaseModel):
    __tablename__ = "sent_notifications"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
    )
    saved_search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("saved_searches.id", ondelete="CASCADE"),
        nullable=False,
    )

    channel: Mapped[NotificationChannel] = mapped_column(
        NotificationChannelEnum, nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        NotificationStatusEnum, nullable=False, default="sent"
    )
    sent_to: Mapped[str] = mapped_column(String, nullable=False)  # email/phone/psid
    body: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(String)

    client: Mapped["Client"] = relationship(
        "Client", back_populates="sent_notifications"
    )
    listing: Mapped["Listing"] = relationship(
        "Listing", back_populates="sent_notifications"
    )
    saved_search: Mapped["SavedSearch"] = relationship(
        "SavedSearch", back_populates="sent_notifications"
    )
