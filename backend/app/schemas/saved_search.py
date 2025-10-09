from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class SavedSearchMatchIn(BaseModel):
    saved_search_id: UUID
    listing_id: UUID


class SavedSearchMatchOut(SavedSearchMatchIn):
    id: UUID
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class SavedSearchFieldBase(BaseModel):
    search_field: str
    value: str


class SavedSearchFieldIn(SavedSearchFieldBase):
    saved_search_id: UUID


class SavedSearchFieldOut(SavedSearchFieldIn):
    id: UUID
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class SavedSearchBase(BaseModel):
    client_id: UUID
    name: str
    beds_min: int = 1
    baths_min: int = 1
    max_price: int | None = None
    analysis_note: str | None = None


class SavedSearchSummary(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class SavedSearchOut(SavedSearchBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None
    fields: list[SavedSearchFieldOut]
    matches: list[SavedSearchMatchOut]
    model_config = ConfigDict(from_attributes=True)


class SavedSearchIn(SavedSearchBase):
    fields: list[SavedSearchFieldIn]
