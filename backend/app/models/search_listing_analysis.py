from __future__ import annotations
from .base import BaseModel
from typing import Optional, TYPE_CHECKING

import uuid
from sqlalchemy import ForeignKey, DateTime, Text, text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

if TYPE_CHECKING:
    from .saved_search import SavedSearch
    from .listing import Listing
    from .property_analysis import PropertyAnalysis


class SearchListingAnalysis(BaseModel):
    __tablename__ = "search_listing_analysis"

    saved_search_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("saved_searches.id", ondelete="CASCADE"), nullable=False
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False
    )
    property_analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID, ForeignKey("property_analysis.id", ondelete="SET NULL")
    )

    criteria_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    listing_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    llm_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    llm_summary: Mapped[Optional[str]] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # keep as TEXT for flexibility
    notified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    saved_search: Mapped["SavedSearch"] = relationship(back_populates="analyses")
    listing: Mapped["Listing"] = relationship(back_populates="analyses")
    property_analysis: Mapped[Optional["PropertyAnalysis"]] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "saved_search_id", "listing_id", name="unique_search_listing_analysis"
        ),
    )
