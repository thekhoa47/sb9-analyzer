from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
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
    pass


class SavedSearchFieldOut(SavedSearchFieldIn):
    id: UUID
    saved_search_id: UUID
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class SavedSearchBase(BaseModel):
    name: str
    beds_min: int = 1
    baths_min: int = 1
    max_price: int | None = None
    analysis_note: str | None = None
    is_active: bool = True


class SavedSearchOut(SavedSearchBase):
    id: UUID
    client_id: UUID
    created_at: datetime
    updated_at: datetime | None
    fields: list[SavedSearchFieldOut] | None
    model_config = ConfigDict(from_attributes=True)


class SavedSearchIn(SavedSearchBase):
    fields: list[SavedSearchFieldIn] = Field(default_factory=list)
