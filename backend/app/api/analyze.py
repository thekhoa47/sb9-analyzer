from fastapi import APIRouter
from app.services.sb9_2 import find_house_containment_split_feet
from app.services.sb9 import collect_polygon_points

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("")
def analyze_saved_search(address: str):
    data = collect_polygon_points(address)
    return find_house_containment_split_feet(data.get("parcel"), data.get("building"))
