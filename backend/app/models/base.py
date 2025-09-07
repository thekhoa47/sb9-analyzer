from sqlalchemy.orm import declarative_base
from ._mixins import UUIDPKMixin, TimestampMixin

# Create the base declarative base
Base = declarative_base()


class BaseModel(UUIDPKMixin, TimestampMixin, Base):
    """Abstract base model with UUID primary key and timestamp fields."""
    __abstract__ = True

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', None)}>"
