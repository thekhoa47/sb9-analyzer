from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel

if TYPE_CHECKING:
    from .client import Client
    from .listing_seen import ListingSeen

class SavedSearch(BaseModel):
    __tablename__ = "saved_searches"

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    city: Mapped[str] = mapped_column(String(80), nullable=False)
    radius_miles: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    beds_min: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    baths_min: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_price: Mapped[int | None] = mapped_column(Integer)

    criteria_json: Mapped[dict | None] = mapped_column(JSONB)
    cursor_iso: Mapped[str | None] = mapped_column(String(40))

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL")
    )

    # Relationships
    client: Mapped[Client | None] = relationship(
        "Client",
        back_populates="searches",
        lazy="joined",
    )

    seen: Mapped[list[ListingSeen]] = relationship(
        "ListingSeen",
        back_populates="saved_search",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
