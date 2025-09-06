from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime, timezone
import uuid

from sqlalchemy import String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel

if TYPE_CHECKING:
    from .saved_search import SavedSearch


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ListingSeen(BaseModel):
    __tablename__ = "listings_seen"

    listing_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    saved_search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("saved_searches.id", ondelete="CASCADE"),
        nullable=False,
    )

    saved_search: Mapped[SavedSearch] = relationship(
        "SavedSearch",
        back_populates="seen",
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint(
            "listing_key", "saved_search_id", name="uq_listings_seen_key_search"
        ),
    )
