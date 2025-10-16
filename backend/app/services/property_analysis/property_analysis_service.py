from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from geoalchemy2.shape import from_shape
from app.models import Property
from app.schemas.property_analysis import PropertyAnalysisOut, PropertyAnalysisCreate
from app.utils.format_verified_address import format_verified_address
from .eligibility import define_eligibility
from .ocgis import (
    get_location_from_ocgis,
    get_parcel_polygon_from_ocgis,
    get_building_polygon_from_ocgis,
)
from .property_analysis_crud import upsert


async def analyze_property_from_address(
    session: AsyncSession, address_in: str
) -> PropertyAnalysisOut:
    lat, lon, address = get_location_from_ocgis(address_in)

    if lat is None or lon is None:
        raise RuntimeError("Cannot find lat & lon for this property from OC GIS")

    formatted_address = format_verified_address(address)
    base_filters = [
        Property.address_line1 == formatted_address.get("address_line1"),
        Property.city == formatted_address.get("city"),
        Property.state == formatted_address.get("state"),
        Property.zip == formatted_address.get("zip"),
    ]
    addr2_filter = (
        Property.address_line2.is_(None)
        if formatted_address.get("address_line2") is None
        else (Property.address_line2 == formatted_address.get("address_line2"))
    )

    existing_property = (
        await session.execute(
            select(Property)
            .options(joinedload(Property.analysis))
            .where(*base_filters, addr2_filter)
            .limit(1)
        )
    ).scalar_one_or_none()

    if existing_property is not None and existing_property.analysis is not None:
        return PropertyAnalysisOut.model_validate(existing_property.analysis)

    if existing_property is None:
        existing_property = Property(
            address_line1=formatted_address.get("address_line1"),
            address_line2=formatted_address.get("address_line2"),
            city=formatted_address.get("city"),
            state=formatted_address.get("state"),
            zip=formatted_address.get("zip"),
        )
        session.add(existing_property)
        await session.flush()

    parcel_polygon = get_parcel_polygon_from_ocgis(lat, lon)

    if not parcel_polygon:
        raise RuntimeError("Cannot find parcel geometry from OC GIS")

    existing_property.lot_geometry = from_shape(parcel_polygon, srid=2230)

    house_polygon = get_building_polygon_from_ocgis(parcel_polygon)

    if not house_polygon:
        raise RuntimeError("Cannot find building geometry from OC GIS")

    existing_property.house_geometry = from_shape(house_polygon, srid=2230)

    analysis = define_eligibility(parcel_polygon, house_polygon)
    sb9 = analysis.label == "SB9"
    adu = analysis.label in ("SB9", "ADU")
    property_analysis_item = PropertyAnalysisCreate(
        property_id=existing_property.id,
        sb9_possible=sb9,
        adu_possible=adu,
        band_low=analysis.band_low,
        band_high=analysis.band_high,
        split_angle_degree=analysis.angle_deg,
        split_line_geometry=analysis.line,
        image_url=analysis.image_url,
    )

    property_analysis_row = await upsert(session, property_analysis_item)
    await session.commit()
    return PropertyAnalysisOut.model_validate(property_analysis_row)
