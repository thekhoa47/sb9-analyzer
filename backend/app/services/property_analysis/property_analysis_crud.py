from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import from_shape

from app.models import PropertyAnalysis  # adjust import
from app.schemas.property_analysis import PropertyAnalysisCreate


def _apply_all(item: PropertyAnalysisCreate, row: PropertyAnalysis) -> None:
    # Always set (including None) so create/update can null fields explicitly
    row.sb9_possible = item.sb9_possible
    row.adu_possible = item.adu_possible
    row.band_low = (
        int(round(item.band_low * 100)) if item.band_low is not None else None
    )
    row.band_high = (
        int(round(item.band_high * 100)) if item.band_high is not None else None
    )
    row.split_angle_degree = (
        float(item.split_angle_degree) if item.split_angle_degree is not None else None
    )
    row.split_line_geometry = (
        from_shape(item.split_line_geometry, srid=2230)
        if item.split_line_geometry is not None
        else None
    )
    row.image_url = item.image_url


async def find_by_property_id(
    session: AsyncSession, property_id: UUID
) -> PropertyAnalysis | None:
    return await session.scalar(
        select(PropertyAnalysis).where(PropertyAnalysis.property_id == property_id)
    )


async def create(
    session: AsyncSession, item: PropertyAnalysisCreate
) -> PropertyAnalysis:
    row = PropertyAnalysis(property_id=item.property_id)
    _apply_all(item, row)
    session.add(row)
    await session.flush()  # assign PKs, surface constraints
    return row


async def update(
    session: AsyncSession, item: PropertyAnalysisCreate
) -> PropertyAnalysis | None:
    row = await find_by_property_id(session, item.property_id)
    if row is None:
        return None
    _apply_all(item, row)
    await session.flush()
    return row


async def upsert(
    session: AsyncSession, item: PropertyAnalysisCreate
) -> PropertyAnalysis:
    existing = await find_by_property_id(session, item.property_id)
    if existing is None:
        return await create(session, item)
    _apply_all(item, existing)
    await session.flush()
    return existing


async def delete(session: AsyncSession, property_id: UUID) -> bool:
    row = await find_by_property_id(session, property_id)
    if row is None:
        return False
    await session.delete(row)
    await session.flush()
    return True
