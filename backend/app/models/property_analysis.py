from __future__ import annotations
from .base import BaseModel
from sqlalchemy import ForeignKey, Integer, Numeric, Boolean, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, TYPE_CHECKING
import uuid
from geoalchemy2 import Geometry
from geoalchemy2.types import WKBElement

if TYPE_CHECKING:
    from .property import Property


class PropertyAnalysis(BaseModel):
    __tablename__ = "property_analysis"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("properties.id"), unique=True, nullable=False
    )
    sb9_possible: Mapped[Optional[bool]] = mapped_column(Boolean)
    adu_possible: Mapped[Optional[bool]] = mapped_column(Boolean)
    band_low: Mapped[Optional[int]] = mapped_column(Integer)
    band_high: Mapped[Optional[int]] = mapped_column(Integer)
    split_angle_degree: Mapped[Optional[float]] = mapped_column(Numeric)
    split_line_geometry: Mapped[Optional[WKBElement]] = mapped_column(
        Geometry("LINESTRING", srid=2230)
    )
    image_url: Mapped[Optional[str]] = mapped_column(String)

    property: Mapped[Property] = relationship(
        back_populates="analysis", uselist=False, single_parent=True
    )
