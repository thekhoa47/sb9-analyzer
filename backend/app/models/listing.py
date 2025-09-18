from __future__ import annotations
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Boolean, DateTime, Numeric, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .base import BaseModel
from .enums import ListingStatus, ListingStatusEnum

if TYPE_CHECKING:
    from .property import Property
    from .saved_search_match import SavedSearchMatch
    from .search_listing_analysis import SearchListingAnalysis
    from .sent_notification import SentNotification


class Listing(BaseModel):
    __tablename__ = "listings"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ListingStatus] = mapped_column(
        ListingStatusEnum, nullable=False, default=ListingStatus.ACTIVE
    )
    listing_price: Mapped[Optional[float]] = mapped_column(Numeric)
    listing_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    source: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String)

    property: Mapped["Property"] = relationship("Property", back_populates="listings")
    matches: Mapped[List["SavedSearchMatch"]] = relationship(
        "SavedSearchMatch", back_populates="listing", cascade="all, delete-orphan"
    )
    analyses: Mapped[List["SearchListingAnalysis"]] = relationship(
        "SearchListingAnalysis", back_populates="listing", cascade="all, delete-orphan"
    )
    sent_notifications: Mapped[List["SentNotification"]] = relationship(
        "SentNotification", back_populates="listing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            None,
            "source",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )
