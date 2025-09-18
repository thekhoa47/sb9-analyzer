from __future__ import annotations
from sqlalchemy.orm import declarative_base
from ._mixins import UUIDPKMixin, TimestampMixin
from sqlalchemy import MetaData

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

# Create the base declarative base
Base = declarative_base(metadata=metadata)


class BaseModel(UUIDPKMixin, TimestampMixin, Base):
    """Abstract base model with UUID primary key and timestamp fields."""

    __abstract__ = True

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', None)}>"
