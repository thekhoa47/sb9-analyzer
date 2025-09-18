from __future__ import annotations

from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel  # -> your abstract base with UUID/timestamps

if TYPE_CHECKING:
    from .saved_search import SavedSearch
    from .sent_notification import SentNotification
    from .client_notification_preference import ClientNotificationPreference


class Client(BaseModel):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    address: Mapped[Optional[str]] = mapped_column(String)

    saved_searches: Mapped[List[SavedSearch]] = relationship(
        "SavedSearch", back_populates="client", cascade="all, delete-orphan"
    )
    notification_preferences: Mapped[List[ClientNotificationPreference]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    sent_notifications: Mapped[List[SentNotification]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
