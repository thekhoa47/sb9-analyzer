# backend/app/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.client import Config
from pathlib import Path
import os
import requests


from dotenv import load_dotenv
from shapely.geometry import shape
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text

from app.utils.geocode import geocode_address
from app.utils.naip import find_naip_assets_for_bbox
from app.utils.parcel import get_parcel_geojson_with_props
from app.services.prepare_property import prepare_property
from app.schemas import MaskResult, PrepImageRequest, AnalyzeResponse
from app.models import SB9Result
from app.db import get_engine  # your engine factory
from app.ml.sb9_model import SB9Runner


# ---------- App & Config ----------

load_dotenv()
# --- R2 config ---
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL") or (
    f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else None
)
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")
SB9_MODEL_PATH = os.getenv("SB9_MODEL_PATH", "app/models/sb9_v1.pt")
R2_MODEL_BUCKET = os.getenv("R2_MODEL_BUCKET", "sb9-models")
R2_MODEL_KEY    = os.getenv("R2_MODEL_KEY",    "sb9_v1.pt")
MODEL_CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", "app/.cache/models"))

MODEL_RUNNER: SB9Runner | None = None


def _r2_client():
    if not (R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_ENDPOINT_URL):
        raise RuntimeError("R2 credentials/endpoint not configured for model download")
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

def _ensure_local_model() -> Path:
    """
    Ensure the model file exists under MODEL_CACHE_DIR/R2_MODEL_KEY.
    If missing, download once from R2. Returns local path.
    """
    local_path = MODEL_CACHE_DIR / R2_MODEL_KEY
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if not local_path.exists() or local_path.stat().st_size == 0:
        s3 = _r2_client()
        # stream to temp then rename (atomic-ish)
        tmp_path = local_path.with_suffix(local_path.suffix + ".part")
        with s3.get_object(Bucket=R2_MODEL_BUCKET, Key=R2_MODEL_KEY)["Body"] as body, open(tmp_path, "wb") as f:
            for chunk in iter(lambda: body.read(1024 * 1024), b""):
                f.write(chunk)
        tmp_path.replace(local_path)
        print(f"[SB9] Downloaded model from r2://{R2_MODEL_BUCKET}/{R2_MODEL_KEY} -> {local_path}")
    else:
        print(f"[SB9] Using cached model at {local_path}")
    return local_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL_RUNNER
    try:
        model_path = _ensure_local_model()
        MODEL_RUNNER = SB9Runner(str(model_path))
        print("[SB9] Model loaded ✅")
        yield
    except Exception as e:
        MODEL_RUNNER = None
        print(f"[SB9] Model load failed: {type(e).__name__}: {e}")
        yield
    finally:
        MODEL_RUNNER = None
        print("[SB9] Model unloaded")

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

# ---------- Debug routes ----------

@app.get("/debug/geocode")
def debug_geocode(
    address: str,
):
    lat, lon, meta = geocode_address(address, MAPBOX_TOKEN)
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
    lat, lon, _ = geocode_address(address, MAPBOX_TOKEN)
    geom, props, extras = get_parcel_geojson_with_props(lat, lon)
    return {
        "extras": extras,
        "geometry_type": geom.get("type"),
        "geometry": geom,
        "props_preview": props if props else None,
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
