from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime


class FoundListing(BaseModel):
    source: str = "zillow"
    external_id: str | None = None
    url: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    zip: str
    listing_price: int | None = None
    listing_date: datetime | None = None  # ISO date string
    status: str | None = (
        None  # "ACTIVE" | "PENDING" | "COMING_SOON" | "CANCELED" | "SOLD"
    )
    bedrooms: int | None = None
    bathrooms: float | None = None
    year_built: int | None = None


class FindListingsResult(BaseModel):
    listings: list[FoundListing] = Field(default_factory=list)


class ListingAnalysisJSON(BaseModel):
    llm_analysis: str
    llm_summary: str
    verdict: str  # "good" | "neutral" | "bad"
