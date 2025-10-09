from __future__ import annotations
from fastapi import APIRouter
from app.services.sb9_2 import find_house_containment_split_feet
from app.services.analyze_address import get_geoms_from_address

router = APIRouter(
    prefix="/analyze-geoms-from-address", tags=["analyze-geoms-from-address"]
)


@router.post("")
def analyze_geoms_from_address(address: str):
    data = get_geoms_from_address(address)
    return find_house_containment_split_feet(data.get("parcel"), data.get("house"))
