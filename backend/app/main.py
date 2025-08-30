# backend/app/main.py

from fastapi import FastAPI, Depends, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.client import Config
from pathlib import Path
import os
import requests
from typing import Optional, Literal, List, Mapping, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, select
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
import logging

from shapely.geometry import shape
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text

from .utils.geocode import geocode_address
from .utils.naip import find_naip_assets_for_bbox
from .utils.parcel import get_parcel_geojson_with_props
from .services.prepare_property import prepare_property
from .schemas import MaskResult, PrepImageRequest, AnalyzeResponse, ResultWithProperty
from .models import SB9Result, Property
from .db import get_db  # your engine factory
from .ml.sb9_model import SB9Runner
from .utils.geo_norm import normalize_state
from .utils.parse_filters import parse_filters
from .models import Client, SavedSearch
from .schemas import ClientIn, ClientOut, SavedSearchIn, SavedSearchOut
from .jobs import start_scheduler, shutdown_scheduler, trigger_poll_once
from .config import settings
from app.routers import messenger_webhook, tasks


# --- logging ---
log = logging.getLogger("sb9")
log.setLevel(logging.INFO)


# ---------- App & Config ----------

MODEL_RUNNER: SB9Runner | None = None


def _r2_client():
    if not (settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY and settings.R2_ENDPOINT_URL):
        raise RuntimeError("R2 credentials/endpoint not configured for model download")
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

def _ensure_local_model() -> Path:
    """
    Ensure the model file exists under MODEL_CACHE_DIR/R2_MODEL_KEY.
    If missing, download once from R2. Returns local path.
    """
    local_path = settings.MODEL_CACHE_DIR / settings.R2_MODEL_KEY
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if not local_path.exists() or local_path.stat().st_size == 0:
        s3 = _r2_client()
        # stream to temp then rename (atomic-ish)
        tmp_path = local_path.with_suffix(local_path.suffix + ".part")
        with s3.get_object(Bucket=settings.R2_MODEL_BUCKET, Key=settings.R2_MODEL_KEY)["Body"] as body, open(tmp_path, "wb") as f:
            for chunk in iter(lambda: body.read(1024 * 1024), b""):
                f.write(chunk)
        tmp_path.replace(local_path)
        print(f"[SB9] Downloaded model from r2://{settings.R2_MODEL_BUCKET}/{settings.R2_MODEL_KEY} -> {local_path}")
    else:
        print(f"[SB9] Using cached model at {local_path}")
    return local_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL_RUNNER
    try:
        model_path = _ensure_local_model()
        MODEL_RUNNER = SB9Runner(str(model_path))
        log.info("[SB9] Model loaded ✅")
        if settings.ENABLE_SCHEDULER:
            start_scheduler()
        yield
    except Exception as e:
        MODEL_RUNNER = None
        log.exception("[SB9] Startup error: %s: %s", type(e).__name__, e)
        # Still yield so the app can serve e.g. /health if you want
        yield
    finally:
        # Stop background scheduler first so it doesn't run during teardown
        shutdown_scheduler()
        log.info("[SB9] Scheduler stopped")

        # Unload model
        MODEL_RUNNER = None
        log.info("[SB9] Model unloaded")

app = FastAPI(title="sb9-analyzer backend", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "https://sb9-analyzer.vercel.app",
    ],
    # Allow Vercel preview deployments too:
    allow_origin_regex=r"^https://sb9-analyzer-.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Health ----------

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Routers ----------
app.include_router(messenger_webhook.router)
app.include_router(tasks.router)

# ---------- Main endpoint ----------

@app.post("/prep-image", response_model=MaskResult)
def prep_image(
    req: PrepImageRequest,
    db: Session = Depends(get_db),
):
    *_, mask = prepare_property(db, req.address)
    return mask

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    req: PrepImageRequest,
    db: Session = Depends(get_db),
):
    # 1) prep (short-circuits if property exists; returns deterministic image_url)
    property_id, mask = prepare_property(db, req.address)

    # 2) infer (model loaded once via lifespan)
    if MODEL_RUNNER is None:
        raise HTTPException(
            status_code = 503,
            detail=f"No geocoding results for '{req.address}'. Please check spelling."
        )
    label, _conf, _probs = MODEL_RUNNER.predict_from_url(mask.image_url)
    # label should be one of your training classes, e.g., "YES"/"NO"

    # 3) upsert sb9_results (one-to-one on property_id)
    ins = pg_insert(SB9Result.__table__).values(
        property_id=property_id,
        predicted_label=label,   # SB9Result.predicted_label is an Enum or Text; ensure types match
    )
    stmt = ins.on_conflict_do_update(
        index_elements=["property_id"],   # or constraint="uq_sb9_results_property_id" if you named it
        set_={
            "predicted_label": ins.excluded.predicted_label,
            "updated_at": text("now()"),
        },
    )
    db.execute(stmt)
    db.commit()

    # 4) return prep-image payload + label
    return AnalyzeResponse(**mask.model_dump(), predicted_label=label)

ALLOWED_SORT = {"address", "city", "state", "zip", "label"}

@app.get("/results", response_model=Page[ResultWithProperty])
def list_results(
    request: Request,
    db: Session = Depends(get_db),
    params: Params = Depends(),                   # ?page=1&size=50
    sort_by: List[str] = Query([], alias="sortBy"), # multi-sort: sortBy=city:DESC&sortBy=state:ASC
    search: Optional[str] = Query(None),           # free text over address/city/state
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
        "city":  Property.city,
        "state": Property.state,
        "zip":   Property.zip,
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
            if vals: stmt = stmt.where(col.in_(vals))
        elif op == "$nin":
            vals = [v.strip() for v in value.split(",") if v.strip()]
            if vals: stmt = stmt.where(~col.in_(vals))

    # Search over address/city/state (+ “California” -> CA)
    if search:
        needle = search.strip()
        like = f"%{needle}%"
        maybe_abbr = normalize_state(needle)
        ors = [Property.address.ilike(like), Property.city.ilike(like), Property.state.ilike(like)]
        if maybe_abbr:
            ors.append(Property.state == maybe_abbr)
        stmt = stmt.where(or_(*ors))

    # Multi-sort parsing
    sort_map = {
        "address": Property.address,
        "city":    Property.city,
        "state":   Property.state,
        "zip":     Property.zip,
        "label":   SB9Result.predicted_label,
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


# --- Clients ---
@app.post("/clients", response_model=ClientOut)
def create_client(payload: ClientIn, db: Session = Depends(get_db)):
    c = Client(**payload.model_dict())
    db.add(c); db.commit(); db.refresh(c)
    return ClientOut(**{**payload.model_dump(), "id": c.id})

@app.get("/clients/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    c = db.get(Client, client_id)
    if not c: raise HTTPException(404)
    return ClientOut(
        id=c.id, name=c.name, email=c.email, phone=c.phone,
        messenger_psid=c.messenger_psid,
        sms_opt_in=c.sms_opt_in, email_opt_in=c.email_opt_in, messenger_opt_in=c.messenger_opt_in
    )

# --- Saved Searches ---
@app.post("/saved-searches", response_model=SavedSearchOut)
def create_saved_search(payload: SavedSearchIn, db: Session = Depends(get_db)):
    s = SavedSearch(**payload.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return SavedSearchOut(**{**payload.model_dump(), "id": s.id, "cursor_iso": s.cursor_iso})

@app.get("/saved-searches/{search_id}", response_model=SavedSearchOut)
def get_saved_search(search_id: int, db: Session = Depends(get_db)):
    s = db.get(SavedSearch, search_id)
    if not s: raise HTTPException(404)
    return SavedSearchOut(
        id=s.id, name=s.name, city=s.city, radius_miles=s.radius_miles,
        beds_min=s.beds_min, baths_min=s.baths_min, max_price=s.max_price,
        client_id=s.client_id, cursor_iso=s.cursor_iso
    )


#-----------------------------------
# ---------- Debug routes ----------
#-----------------------------------


@app.get("/debug/geocode")
def debug_geocode(
    address: str,
):
    lat, lon, meta = geocode_address(address, settings.MAPBOX_TOKEN)
    return {
        "lat": lat,
        "lon": lon,
        **meta,
        "google_maps": f"https://www.google.com/maps?q={lat},{lon}",
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=19/{lat}/{lon}",
    }


@app.get("/debug/parcel")
def debug_parcel(
    address: str,
):
    lat, lon, _ = geocode_address(address, settings.MAPBOX_TOKEN)
    geom, props, extras = get_parcel_geojson_with_props(lat, lon)
    return {
        "extras": extras,
        "geometry_type": geom.get("type"),
        "geometry": geom,
        "props_preview": props if props else None,
    }


@app.get("/debug/naip")
def debug_naip(address: str):
    lat, lon, _ = geocode_address(address, settings.MAPBOX_TOKEN)
    geom, *_ = get_parcel_geojson_with_props(lat, lon)
    g = shape(geom)
    minx, miny, maxx, maxy = g.bounds
    pad = 0.0008
    assets = find_naip_assets_for_bbox(minx - pad, miny - pad, maxx + pad, maxy + pad, limit=12)
    return {
        "count": len(assets),
        "asset_hrefs": [a.href for a in assets],
        "stac_ids": [getattr(a, "id", None) for a in assets],
    }

@app.get("/debug/analyze")
def debug_analyze(address: str, db: Session = Depends(get_db)):
    # 1) Prove the model exists first
    if MODEL_RUNNER is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # 2) Then touch external services
    try:
        property_id, mask = prepare_property(db, address)
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Parcel service timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Parcel service error: {e}")

    # 3) Predict
    label, conf, probs = MODEL_RUNNER.predict_from_url(mask.image_url)
    return {
        "property_id": property_id,
        "image_url": mask.image_url,
        "predicted_label": label,
        "confidence": conf,
    }


@app.get("/debug/model")
def debug_model():
    ok = MODEL_RUNNER is not None
    info = getattr(MODEL_RUNNER, "info", None) if ok else None
    return {"loaded": ok, "info": info}
