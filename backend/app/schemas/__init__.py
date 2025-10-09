# app/schemas.py
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class PrepImageRequest(BaseModel):
    address: str


class ParcelStats(BaseModel):
    area_m2: float
    perimeter_m: float


class MaskResult(BaseModel):
    # Mirror your properties table (plus image_url), not user input:
    id: UUID
    address: str
    city: str | None
    state: str | None
    zip: str | None
    beds: int | None
    baths: int | None
    year_built: int | None
    living_area: int | None
    lot_area: int | None
    image_url: str
    # Optional helper for UI
    parcel_stats: ParcelStats | None


class PredictReq(BaseModel):
    url: str  # public image URL you already store in R2 (or anywhere)


class PredictResp(BaseModel):
    label: str
    confidence: float
    probs: dict


class ReloadReq(BaseModel):
    bucket: str | None
    key: str | None


class AnalyzeResponse(MaskResult):
    predicted_label: str  # "YES" / "NO"


class PropertyOut(BaseModel):
    id: UUID
    address: str
    city: str | None
    state: str | None
    zip: str | None
    beds: int | None
    baths: int | None
    year_built: int | None
    living_area: int | None
    lot_area: int | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class Sb9ResultsOut(BaseModel):
    id: UUID
    property_id: UUID
    predicted_label: str
    human_label: str | None
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class ResultWithProperty(Sb9ResultsOut):
    property: PropertyOut
    model_config = ConfigDict(from_attributes=True)


class ResultsPage(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ResultWithProperty]
