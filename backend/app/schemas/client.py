from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

# SAFE now because saved_search.py does not import client.py
from .saved_search import SavedSearchIn, SavedSearchOut


class ClientNotificationPreferenceBase(BaseModel):
    channel: str
    enabled: bool


class ClientNotificationPreferenceIn(ClientNotificationPreferenceBase):
    pass


class ClientNotificationPreferenceOut(ClientNotificationPreferenceIn):
    id: UUID
    client_id: UUID
    created_at: datetime
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class ClientBase(BaseModel):
    name: str
    email: str | None
    phone: str | None
    address: str | None
    is_active: bool


class ClientOut(ClientBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None
    saved_searches: list[SavedSearchOut]  # concrete type, no forward-ref
    notification_preferences: list[ClientNotificationPreferenceOut]
    model_config = ConfigDict(from_attributes=True)


class ClientIn(ClientBase):
    saved_searches: list[SavedSearchIn]  # concrete type, no forward-ref
    notification_preferences: list[ClientNotificationPreferenceIn]


# class ClientsWithSearchesOut(ClientOut):
#     listing_preferences: list[SavedSearchSummary] | None = Field(
#         default_factory=list,
#         validation_alias=AliasChoices("searches", "listing_preferences"),
#         serialization_alias="listing_preferences",
#     )
#     model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ClientPreferencesOut(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


# 🚫 Remove any model_rebuild() calls here
