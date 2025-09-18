# models/enums.py
import sqlalchemy as sa
from enum import Enum as PyEnum


class ListingStatus(PyEnum):
    ACTIVE = "ACTIVE"
    COMING_SOON = "COMING_SOON"
    PENDING = "PENDING"
    SOLD = "SOLD"
    CANCELED = "CANCELED"


class NotificationChannel(PyEnum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    MESSENGER = "MESSENGER"


class NotificationStatus(PyEnum):
    SENT = "SENT"
    FAILED = "FAILED"


ListingStatusEnum = sa.Enum(
    ListingStatus, name="listing_status", native_enum=True, create_type=False
)
NotificationChannelEnum = sa.Enum(
    NotificationChannel,
    name="notification_channel",
    native_enum=True,
    create_type=False,
)
NotificationStatusEnum = sa.Enum(
    NotificationStatus, name="notification_status", native_enum=True, create_type=False
)
