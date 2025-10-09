from __future__ import annotations
from pydantic import BaseModel, field_validator
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from uuid import UUID


class ListingTaskPayload(BaseModel):
    listing_id: UUID
    saved_search_id: UUID


class PropertyTaskPayload(BaseModel):
    property_id: UUID
    listing_id: UUID
    saved_search_id: UUID


class PropertyGeoms(BaseModel):
    property_id: UUID
    house: dict
    parcel: dict
    model_config = {"arbitrary_types_allowed": True}

    # Convert before validation so the type matches `dict | None`
    @field_validator("house", "parcel", mode="before")
    @classmethod
    def _geom_to_geojson_before(cls, v):
        if v is None:
            return None
        if isinstance(v, WKBElement):
            return mapping(to_shape(v))
        return v  # already dict
