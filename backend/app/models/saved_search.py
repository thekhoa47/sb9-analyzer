from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import String, Integer, ForeignKey, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .client import Client
    from .saved_search_field import SavedSearchField
    from .saved_search_match import SavedSearchMatch
    from .search_listing_analysis import SearchListingAnalysis
    from .sent_notification import SentNotification


class SavedSearch(BaseModel):
    __tablename__ = "saved_searches"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    beds_min: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    baths_min: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_price: Mapped[int | None] = mapped_column(Integer)
    analysis_note: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    client: Mapped[Client] = relationship("Client", back_populates="saved_searches")
    fields: Mapped[list[SavedSearchField]] = relationship(
        "SavedSearchField", back_populates="saved_search", cascade="all, delete-orphan"
    )
    matches: Mapped[list[SavedSearchMatch]] = relationship(
        "SavedSearchMatch", back_populates="saved_search", cascade="all, delete-orphan"
    )
    analyses: Mapped[list[SearchListingAnalysis]] = relationship(
        "SearchListingAnalysis",
        back_populates="saved_search",
        cascade="all, delete-orphan",
    )
    sent_notifications: Mapped[list[SentNotification]] = relationship(
        "SentNotification", back_populates="saved_search", cascade="all, delete-orphan"
    )
