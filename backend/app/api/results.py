from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, select
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from app.core import get_db
from app.models import SB9Result, Property
from app.schemas import ResultWithProperty
from app.utils.parse_filters import parse_filters
from app.utils.geo_norm import normalize_state


router = APIRouter(prefix="/results", tags=["results"])


ALLOWED_SORT = {"address", "city", "state", "zip", "label"}


@router.get("/", response_model=Page[ResultWithProperty])
def list_results(
    request: Request,
    db: Session = Depends(get_db),
    params: Params = Depends(),  # ?page=1&size=50
    sort_by: List[str] = Query(
        [], alias="sortBy"
    ),  # multi-sort: sortBy=city:DESC&sortBy=state:ASC
    search: Optional[str] = Query(None),  # free text over address/city/state
):
    # Base selectable (1:1 join + eager load)
    stmt = (
        select(SB9Result)
        .join(SB9Result.property)
        .options(selectinload(SB9Result.property))
    )

    # Filters
    filters = parse_filters(request.query_params)
    colmap = {
        "city": Property.city,
        "state": Property.state,
        "zip": Property.zip,
        "label": SB9Result.predicted_label,
    }
    for field, op, value in filters:
        col = colmap[field]
        if field == "state":
            value = normalize_state(value) or value  # allow full names
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
            Property.address.ilike(like),
            Property.city.ilike(like),
            Property.state.ilike(like),
        ]
        if maybe_abbr:
            ors.append(Property.state == maybe_abbr)
        stmt = stmt.where(or_(*ors))

    # Multi-sort parsing
    sort_map = {
        "address": Property.address,
        "city": Property.city,
        "state": Property.state,
        "zip": Property.zip,
        "label": SB9Result.predicted_label,
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
        stmt = stmt.order_by(Property.address.asc())  # default

    return paginate(db, stmt, params)
