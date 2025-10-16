from uuid import UUID
from datetime import datetime
from shapely.geometry import LineString, mapping, shape as to_shapely
from pydantic import BaseModel, ConfigDict, field_validator
from shapely import wkb as shapely_wkb
from geoalchemy2.elements import WKBElement


class PropertyAnalysisBase(BaseModel):
    property_id: UUID
    sb9_possible: bool
    adu_possible: bool
    band_low: float | None = None
    band_high: float | None = None
    split_angle_degree: float | None = None
    image_url: str | None = None


class PropertyAnalysisCreate(PropertyAnalysisBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)  # <-- add this
    split_line_geometry: LineString | None = None

    @field_validator("split_line_geometry", mode="before")
    @classmethod
    def _to_linestring(cls, v):
        if v is None or isinstance(v, LineString):
            return v
        if isinstance(v, WKBElement):
            return shapely_wkb.loads(bytes(v.data))
        if isinstance(v, (bytes, bytearray)):
            return shapely_wkb.loads(bytes(v))
        if isinstance(v, str):  # hex
            return shapely_wkb.loads(bytes.fromhex(v))
        if isinstance(v, dict):  # GeoJSON -> LineString
            return to_shapely(v)
        raise TypeError(
            "split_line_geometry must be LineString/WKBElement/bytes/hex/GeoJSON or None"
        )


class PropertyAnalysisOut(PropertyAnalysisBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    split_line_geometry: dict | None = None

    @field_validator("split_line_geometry", mode="before")
    def _normalize_line(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):  # already GeoJSON
            return v
        if isinstance(v, LineString):  # Shapely -> GeoJSON
            return mapping(v)
        if isinstance(v, WKBElement):  # WKBElement -> Shapely -> GeoJSON
            return mapping(shapely_wkb.loads(bytes(v.data)))
        if isinstance(v, (bytes, bytearray)):
            return mapping(shapely_wkb.loads(bytes(v)))
        if isinstance(v, str):  # hex
            return mapping(shapely_wkb.loads(bytes.fromhex(v)))
        raise TypeError(
            "split_line_geometry must be LineString/WKBElement/bytes/hex/GeoJSON or None"
        )
