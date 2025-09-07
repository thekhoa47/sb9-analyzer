from fastapi import APIRouter, Depends, HTTPException
from app.core import get_db
from app.core.model import model_manager
from app.schemas import PrepImageRequest, AnalyzeResponse
from app.models import SB9Result
from app.services import prepare_property
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session


router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("/", response_model=AnalyzeResponse)
def analyze(
    req: PrepImageRequest,
    db: Session = Depends(get_db),
):
    # 1) prep (short-circuits if property exists; returns deterministic image_url)
    property_id, mask = prepare_property(db, req.address)

    # 2) infer (model loaded once via lifespan)
    if model_manager.model_runner is None:
        raise HTTPException(
            status_code=503,
            detail=f"No geocoding results for '{req.address}'. Please check spelling.",
        )
    label, _conf, _probs = model_manager.model_runner.predict_from_url(mask.image_url)
    # label should be one of your training classes, e.g., "YES"/"NO"

    # 3) upsert sb9_results (one-to-one on property_id)
    ins = pg_insert(
        SB9Result.__table__
    ).values(
        property_id=property_id,
        predicted_label=label,  # SB9Result.predicted_label is an Enum or Text; ensure types match
    )
    stmt = ins.on_conflict_do_update(
        index_elements=[
            "property_id"
        ],  # or constraint="uq_sb9_results_property_id" if you named it
        set_={
            "predicted_label": ins.excluded.predicted_label,
            "updated_at": text("now()"),
        },
    )
    db.execute(stmt)
    db.commit()

    # 4) return prep-image payload + label
    return AnalyzeResponse(**mask.model_dump(), predicted_label=label)
