from __future__ import annotations
from .base import BaseModel
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import Index, String, Float, Integer
from typing import Optional, TYPE_CHECKING
from geoalchemy2 import Geometry
from geoalchemy2.types import WKBElement


if TYPE_CHECKING:
    from .listing import Listing
    from .property_analysis import PropertyAnalysis


class Property(BaseModel):
    __tablename__ = "properties"

    address_line1: Mapped[str] = mapped_column(String, nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    zip: Mapped[str] = mapped_column(String, nullable=False)
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[float]] = mapped_column(Float)
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    house_geometry: Mapped[Optional[WKBElement]] = mapped_column(
        Geometry("POLYGON", srid=2230)
    )
    lot_geometry: Mapped[Optional[WKBElement]] = mapped_column(
        Geometry("POLYGON", srid=2230)
    )

    listings: Mapped[Optional[Listing]] = relationship(
        "Listing",
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )
    analysis: Mapped[Optional[PropertyAnalysis]] = relationship(
        "PropertyAnalysis",
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    __table_args__ = (
        Index(
            "unique_property_without_address2",
            "address_line1",
            "city",
            "state",
            "zip",
            unique=True,
            postgresql_where="address_line2 IS NULL",
        ),
        Index(
            "unique_property_with_address2",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip",
            unique=True,
            postgresql_where="address_line2 IS NOT NULL",
        ),
    )
