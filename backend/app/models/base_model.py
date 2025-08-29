# app/models/base_model.py
from .base import Base
from ._mixins import UUIDPKMixin, TimestampMixin

class BaseModel(UUIDPKMixin, TimestampMixin, Base):
    """Abstract base model – inherit this in your real models."""
    __abstract__ = True

    # optional conveniences
    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={getattr(self, 'id', None)}>"
