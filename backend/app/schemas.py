# app/schemas.py
from pydantic import BaseModel
from typing import Optional
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
