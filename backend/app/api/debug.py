from fastapi import APIRouter, Depends
from app.services.analyze_address import get_geoms_from_address
from app.services.sb9 import get_property_geoms
from app.services.sb9_2 import find_house_containment_split_feet
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_async_session
from app.schemas.property import PropertyOut
from app.models import Property

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/sb9")
def debug_sb9(address: str):
    result = get_geoms_from_address(address)
    return result


@router.post("/process-property-test")
async def debug_process_property(
    property_id,
    session: AsyncSession = Depends(get_async_session),
):
    pwg = await get_property_geoms(property_id=property_id, session=session)
    await find_house_containment_split_feet(
        session=session,
        property_id=property_id,
        parcel_xy=pwg.parcel,
        house_xy=pwg.house,
    )
    await session.commit()
    return {"done": True}


@router.get("/get-property/{property_id}", response_model=PropertyOut)
async def debug_get_property(
    property_id,
    session: AsyncSession = Depends(get_async_session),
):
    prop = await session.get(Property, property_id)
    return prop
