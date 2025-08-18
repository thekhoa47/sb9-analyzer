import uuid
import enum
from sqlalchemy import Column, TIMESTAMP, text, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class SB9Label(str, enum.Enum):
    YES = "YES"
    NO = "NO"
    UNCERTAIN = "UNCERTAIN"


class SB9Result(Base):
    __tablename__ = "sb9_results"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    predicted_label = Column(SAEnum(SB9Label, name="sb9_label", create_type=False), nullable=False)
    human_label     = Column(SAEnum(SB9Label, name="sb9_label", create_type=False))

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True))

    property = relationship("Property", back_populates="result", uselist=False)


# Indexes
Index("idx_sb9_results_predicted", SB9Result.predicted_label)
Index("idx_sb9_results_human", SB9Result.human_label)
Index("idx_sb9_results_created", SB9Result.property_id, SB9Result.created_at.desc())
