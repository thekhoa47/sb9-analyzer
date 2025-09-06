# app/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
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
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    year_built: Optional[int] = None
    living_area: Optional[int] = None
    lot_area: Optional[int] = None
    image_url: str
    # Optional helper for UI
    parcel_stats: Optional[ParcelStats] = None


class PredictReq(BaseModel):
    url: str  # public image URL you already store in R2 (or anywhere)


class PredictResp(BaseModel):
    label: str
    confidence: float
    probs: dict


class ReloadReq(BaseModel):
    bucket: Optional[str] = None
    key: Optional[str] = None


class AnalyzeResponse(MaskResult):
    predicted_label: str  # "YES" / "NO"


class PropertyOut(BaseModel):
    id: UUID
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    year_built: Optional[int] = None
    living_area: Optional[int] = None
    lot_area: Optional[int] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class Sb9ResultsOut(BaseModel):
    id: UUID
    property_id: UUID
    predicted_label: str
    human_label: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ResultWithProperty(Sb9ResultsOut):
    property: PropertyOut
    model_config = ConfigDict(from_attributes=True)


class ResultsPage(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ResultWithProperty]


from pydantic import BaseModel


class ClientIn(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    messenger_psid: str | None = None
    sms_opt_in: bool = False
    email_opt_in: bool = False
    messenger_opt_in: bool = False


class ClientOut(ClientIn):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class SavedSearchIn(BaseModel):
    name: str
    city: str
    radius_miles: int = 50
    beds_min: int = 0
    baths_min: int = 0
    max_price: int | None = None


class SavedSearchOut(SavedSearchIn):
    id: UUID
    client_id: UUID
    cursor_iso: str | None = None


class ClientsWithSearchesOut(ClientOut):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    # Pull from the ORM attribute `searches`, output as `listing_preferences`
    listing_preferences: List[SavedSearchOut] = Field(
        default_factory=list, alias="searches"
    )


class OnboardNewClientIn(ClientIn):
    listing_preferences: List[SavedSearchIn]


class OnboardNewClientOut(BaseModel):
    client: ClientOut
    saved_searches: List[SavedSearchOut]
