from fastapi import APIRouter, Depends, HTTPException
from app.core import get_db
from app.models import SavedSearch
from app.schemas.saved_search import SavedSearchIn, SavedSearchOut
from sqlalchemy.orm import Session

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])


# --- Saved Searches ---
@router.post("/saved-searches", response_model=SavedSearchOut)
def create_saved_search(payload: SavedSearchIn, db: Session = Depends(get_db)):
    s = SavedSearch(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return SavedSearchOut(**{**payload.model_dump(), "id": s.id})


@router.get("/saved-searches/{search_id}", response_model=SavedSearchOut)
def get_saved_search(search_id: int, db: Session = Depends(get_db)):
    s = db.get(SavedSearch, search_id)
    if not s:
        raise HTTPException(404)
    return SavedSearchOut(
        id=s.id,
        name=s.name,
        # city=s.city,
        # radius_miles=s.radius_miles,
        beds_min=s.beds_min,
        baths_min=s.baths_min,
        max_price=s.max_price,
        client_id=s.client_id,
        # cursor_iso=s.cursor_iso,
    )
