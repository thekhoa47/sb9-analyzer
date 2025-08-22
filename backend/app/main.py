# backend/app/main.py

from fastapi import FastAPI, Query, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uuid import UUID
from typing import Optional
from io import BytesIO
import os

from dotenv import load_dotenv
from shapely.geometry import shape
from shapely.ops import transform as shp_transform
from pyproj import Transformer
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text, select
from geoalchemy2.shape import to_shape, from_shape

from app.utils.geocode import geocode_address
from app.utils.naip import find_naip_assets_for_bbox
from app.utils.mask import mask_naip_with_parcel_mosaic  # will return PIL Image with return_image=True
from app.utils.parcel import get_parcel_geojson_with_props
from app.storage.r2 import upload_bytes_and_get_url
from app.services.prepare_property import prepare_property
from app.schemas import MaskResult, ParcelStats, PrepImageRequest
from app.models import Property, SB9Result
from app.db import get_engine  # your engine factory
from app.ml.sb9_model import SB9Runner


# ---------- App & Config ----------

load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")
SB9_MODEL_PATH = os.getenv("SB9_MODEL_PATH", "app/models/sb9_v1.pt")
MODEL_RUNNER: SB9Runner | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL_RUNNER
    # load once
    MODEL_RUNNER = SB9Runner(SB9_MODEL_PATH)
    print(f"SB9 model loaded from {SB9_MODEL_PATH}")
    try:
        yield
    finally:
        MODEL_RUNNER = None
        print("SB9 model unloaded")

app = FastAPI(title="sb9-analyzer backend", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "https://sb9-analyzer.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DB session helper ----------

_engine = get_engine()
SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Health ----------

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Main endpoint ----------

@app.post("/prep-image", response_model=MaskResult)
def prep_image(
    req: PrepImageRequest,
    db: Session = Depends(get_db),
):
    *_, mask = prepare_property(db, req.address)
    return mask

# ---------- New one-shot analyze endpoint ----------
class AnalyzeResponse(MaskResult):
    predicted_label: str  # "ELIGIBLE" / "INELIGIBLE"

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    address: str,
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    zip: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    # 1) prep (short-circuits if property exists; returns deterministic image_url)
    property_id, mask = prepare_property(db, address, city, state, zip)

    # 2) infer (model loaded once via lifespan)
    if MODEL_RUNNER is None:
        raise HTTPException(
            status_code = 503,
            detail=f"No geocoding results for '{req.address}'. Please check spelling."
        )
    label, _conf, _probs = MODEL_RUNNER.predict_from_url(mask.image_url)
    # label should be one of your training classes, e.g., "ELIGIBLE"/"INELIGIBLE"

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

# ---------- Debug routes ----------

@app.get("/debug/geocode")
def debug_geocode(
    address: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip: Optional[str] = None,
):
    lat, lon, meta = geocode_address(address, MAPBOX_TOKEN, city=city, state=state, zip_code=zip)
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
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip: Optional[str] = None,
):
    lat, lon, _ = geocode_address(address, MAPBOX_TOKEN, city=city, state=state, zip_code=zip)
    geom, props, official_addr, extras, source = get_parcel_geojson_with_props(lat, lon)
    # Show a small, readable subset
    props_preview = props
    return {
        "source": source,
        "official_address": official_addr,
        "extras": extras,
        "geometry_type": geom.get("type"),
        "geometry": geom,  # keep full GeoJSON for debugging
        "props_preview": props_preview,
    }


@app.get("/debug/parcel-stats")
def debug_parcel_stats(address: str):
    lat, lon, _ = geocode_address(address, MAPBOX_TOKEN)
    geom, props, official_addr, extras, source = get_parcel_geojson_with_props(lat, lon)

    g = shape(geom)  # WGS84
    # Project to meters (Web Mercator) for quick area/perimeter
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    gm = shp_transform(lambda x, y: to_m.transform(x, y), g)

    area_m2 = round(gm.area, 2)
    perim_m = round(gm.length, 2)
    minx, miny, maxx, maxy = g.bounds

    return {
        "source": source,
        "official_address": official_addr,
        "extras": extras,
        "geom_type": g.geom_type,
        "bbox_wgs84": [minx, miny, maxx, maxy],
        "area_m2": area_m2,
        "perimeter_m": perim_m,
    }


@app.get("/debug/naip")
def debug_naip(address: str):
    lat, lon, _ = geocode_address(address, MAPBOX_TOKEN)
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
