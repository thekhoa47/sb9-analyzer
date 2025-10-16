from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, select
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from app.core import get_db
from app.models import Property, PropertyAnalysis
from app.schemas.property import PropertyWithAnalysisOut
from app.utils.parse_filters import parse_filters
from app.utils.geo_norm import normalize_state


router = APIRouter(prefix="/analyzed-properties", tags=["analyzed-properties"])


ALLOWED_SORT = {"address_line1", "city", "state", "zip"}


@router.get("", response_model=Page[PropertyWithAnalysisOut])
def list_analyzed_properties(
    request: Request,
    db: Session = Depends(get_db),
    params: Params = Depends(),  # ?page=1&size=50
    sort_by: list[str] | None = Query(
        [], alias="sortBy"
    ),  # multi-sort: sortBy=city:DESC&sortBy=state:ASC
    search: str | None = Query(None),  # free text over address/city/state
):
    # Base selectable (1:1 join + eager load)
    stmt = (
        select(Property)
        .join(Property.analysis)
        .options(selectinload(Property.analysis))
    )

    # Filters
    filters = parse_filters(request.query_params)
    colmap = {
        "city": Property.city,
        "state": Property.state,
        "zip": Property.zip,
        "sb9": PropertyAnalysis.sb9_possible,
        "adu": PropertyAnalysis.adu_possible,
    }
    for field, op, value in filters:
        col = colmap[field]
        if op == "$eq":
            stmt = stmt.where(col == value)
        elif op == "$ne":
            stmt = stmt.where(col != value)
        elif op == "$ilike":
            stmt = stmt.where(col.ilike(f"%{value}%"))
        elif op == "$in":
            vals = [v.strip() for v in value.split(",") if v.strip()]
            if vals:
                stmt = stmt.where(col.in_(vals))
        elif op == "$nin":
            vals = [v.strip() for v in value.split(",") if v.strip()]
            if vals:
                stmt = stmt.where(~col.in_(vals))

    # Search over address/city/state (+ “California” -> CA)
    if search:
        needle = search.strip()
        like = f"%{needle}%"
        maybe_abbr = normalize_state(needle)
        ors = [
            Property.address_line1.ilike(like),
            Property.city.ilike(like),
            Property.state.ilike(like),
        ]
        if maybe_abbr:
            ors.append(Property.state == maybe_abbr)
        stmt = stmt.where(or_(*ors))

    # Multi-sort parsing
    sort_map = {
        "address_line1": Property.address_line1,
        "city": Property.city,
        "state": Property.state,
        "zip": Property.zip,
    }

    order_cols = []
    for item in sort_by:
        field, _, dirpart = item.partition(":")
        field = field.strip().lower()
        if field not in ALLOWED_SORT:
            raise HTTPException(400, detail=f"Unsupported sort field: {field}")
        direction = (dirpart or "ASC").strip().upper()
        col = sort_map[field]
        order_cols.append(col.desc() if direction == "DESC" else col.asc())

    if order_cols:
        stmt = stmt.order_by(*order_cols)
    else:
        stmt = stmt.order_by(Property.address_line1.asc())  # default

    return paginate(db, stmt, params)
