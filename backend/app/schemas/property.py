from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from geoalchemy2.elements import WKBElement
from datetime import datetime
from typing import Annotated
from uuid import UUID
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

Coord = tuple[float, float]  # exactly two numbers
LinearRing = Annotated[list[Coord], Field(min_length=4)]
PolygonCoords = Annotated[list[LinearRing], Field(min_length=1)]


class PropertyBase(BaseModel):
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    zip: str
    bedrooms: int | None
    bathrooms: int | None
    year_built: int | None


class PropertyOut(PropertyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None
    house_geometry: dict | None = None
    lot_geometry: dict | None = None
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

    # Convert before validation so the type matches `dict | None`
    @field_validator("house_geometry", "lot_geometry", mode="before")
    @classmethod
    def _geom_to_geojson_before(cls, v):
        if v is None:
            return None
        if isinstance(v, WKBElement):
            return mapping(to_shape(v))
        return v  # already dict
