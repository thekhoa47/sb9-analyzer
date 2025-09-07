from fastapi import APIRouter, Depends
from app.core import get_db
from app.schemas import PrepImageRequest, MaskResult
from app.services import prepare_property
from sqlalchemy.orm import Session

router = APIRouter(prefix="/prep-image", tags=["prep-image"])


@router.post("/", response_model=MaskResult)
def prep_image(
    req: PrepImageRequest,
    db: Session = Depends(get_db),
):
    *_, mask = prepare_property(db, req.address)
    return mask
