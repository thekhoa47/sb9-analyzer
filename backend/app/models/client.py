from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel  # -> your abstract base with UUID/timestamps

if TYPE_CHECKING:
    from .saved_search import SavedSearch
    from .sent_notification import SentNotification
    from .client_notification_preference import ClientNotificationPreference


class Client(BaseModel):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    address: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    saved_searches: Mapped[list[SavedSearch]] = relationship(
        "SavedSearch", back_populates="client", cascade="all, delete-orphan"
    )
    notification_preferences: Mapped[list[ClientNotificationPreference]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    sent_notifications: Mapped[list[SentNotification]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
