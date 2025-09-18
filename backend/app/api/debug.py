from fastapi import APIRouter
from app.services.sb9 import collect_polygon_points


router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/sb9")
def debug_sb9(address: str):
    result = collect_polygon_points(address)
    return result
