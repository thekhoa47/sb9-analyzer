import uuid
from sqlalchemy import (
    Column, Integer, Text, CheckConstraint, TIMESTAMP, text, CHAR
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from .base import Base


class Property(Base):
    __tablename__ = "properties"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address        = Column(Text, nullable=False)
    city           = Column(Text)
    state          = Column(CHAR(2), CheckConstraint("state ~ '^[A-Z]{2}$'"))
    zip            = Column(CHAR(5), CheckConstraint("zip ~ '^[0-9]{5}$'"))

    parcel_geom     = Column(Geometry("POLYGON", srid=4326))
    parcel_centroid = Column(Geometry("POINT", srid=4326))

    beds        = Column(Integer)
    baths       = Column(Integer, CheckConstraint("baths >= 0"))  # replace with Numeric(3,1) if you want exact match
    year_built  = Column(Integer, CheckConstraint("year_built BETWEEN 1800 AND 2100"))
    living_area = Column(Integer, CheckConstraint("living_area >= 0"))
    lot_area    = Column(Integer, CheckConstraint("lot_area >= 0"))

    image_url   = Column(Text)

    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at  = Column(TIMESTAMP(timezone=True))

    # one-to-one relationship with SB9Result
    result = relationship(
        "SB9Result",
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# Indexes
from sqlalchemy import Index
Index(
    "ux_properties_addr",
    func.lower(Property.address),
    func.lower(Property.city),
    func.lower(Property.state),
    Property.zip,
    unique=True,
)
Index("idx_properties_centroid", Property.parcel_centroid, postgresql_using="gist")
Index("idx_properties_geom", Property.parcel_geom, postgresql_using="gist")
