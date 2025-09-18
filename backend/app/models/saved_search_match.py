from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

if TYPE_CHECKING:
    from .saved_search import SavedSearch
    from .listing import Listing


class SavedSearchMatch(BaseModel):
    __tablename__ = "saved_search_matches"

    saved_search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("saved_searches.id", ondelete="CASCADE"),
        nullable=False,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
    )

    saved_search: Mapped["SavedSearch"] = relationship(
        "SavedSearch", back_populates="matches"
    )
    listing: Mapped["Listing"] = relationship("Listing", back_populates="matches")

    __table_args__ = (UniqueConstraint("saved_search_id", "listing_id"),)
