from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

if TYPE_CHECKING:
    from .saved_search import SavedSearch


class SavedSearchField(BaseModel):
    __tablename__ = "saved_search_fields"

    saved_search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("saved_searches.id", ondelete="CASCADE"),
        nullable=False,
    )
    search_field: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)

    saved_search: Mapped["SavedSearch"] = relationship(
        "SavedSearch", back_populates="fields"
    )

    __table_args__ = (
        UniqueConstraint("saved_search_id", "search_field", "value"),
        Index(None, "search_field", "value"),
    )
