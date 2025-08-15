# backend/app/main.py

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional
import os

from dotenv import load_dotenv
from shapely.geometry import shape
from shapely.ops import transform as shp_transform
from pyproj import Transformer

from app.utils.geocode import geocode_address
from app.utils.naip import find_naip_assets_for_bbox
from app.utils.mask import mask_naip_with_parcel_mosaic
from app.utils.parcel import get_parcel_geojson_with_props  # returns (geom, props, source)

# ---------- App & Config ----------

load_dotenv()  # loads backend/.env

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")
REGRID_TOKEN = os.getenv("REGRID_TOKEN", "")

app = FastAPI(title="sb9-analyzer backend", version="0.2.0")

# Allow local Next.js dev by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------

class MaskResult(BaseModel):
    address: str
    image_url: str
    source: str  # parcel source: "regrid" or "oc_gis"
    matched_place_name: Optional[str] = None
    geocode_relevance: Optional[float] = None
    parcel_apn: Optional[str] = None
    parcel_site_address: Optional[str] = None

# ---------- Error handling ----------

@app.exception_handler(RuntimeError)
async def runtime_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

# ---------- Health ----------

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Debug routes ----------

@app.get("/debug/geocode")
def debug_geocode(
    address: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip: Optional[str] = None,
    bbox: Optional[str] = None,      # "minLon,minLat,maxLon,maxLat"
    proximity_lat: Optional[float] = None,
    proximity_lon: Optional[float] = None,
):
    bbox_list = [float(x) for x in bbox.split(",")] if bbox else None
    proximity = (proximity_lat, proximity_lon) if (proximity_lat is not None and proximity_lon is not None) else None

    lat, lon, meta = geocode_address(
        address, MAPBOX_TOKEN,
        city=city, state=state, zip_code=zip,
        bbox=bbox_list, proximity=proximity
    )
    return {
        "lat": lat,
        "lon": lon,
        "matched_place_name": meta.get("matched_place_name"),
        "relevance": meta.get("relevance"),
        "google_maps": f"https://www.google.com/maps?q={lat},{lon}",
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=19/{lat}/{lon}",
    }

# @app.get("/debug/naip")
# def debug_naip(address: str,
#     city: Optional[str] = None,
#     state: Optional[str] = None,
#     zip: Optional[str] = None,):
#     lat, lon, _ = geocode_address(address, MAPBOX_TOKEN, city=city, state=state, zip_code=zip)
#     url, item = find_naip_assets_for_bbox(lat, lon)
#     return {"naip_url": url, "stac_item_id": getattr(item, "id", None)}

@app.get("/debug/parcel")
def debug_parcel(address: str,
                 city: Optional[str] = None,
                 state: Optional[str] = None,
                 zip: Optional[str] = None,
                 ):
    lat, lon, _ = geocode_address(address, MAPBOX_TOKEN, city=city, state=state, zip_code=zip)
    geom, props, source = get_parcel_geojson_with_props(lat, lon)
    return {"source": source, "geometry": geom, "props_sample": dict(list(props.items())[:8])}
    # addresses = get_parcel_geojson_with_props(lat, lon)
    # return addresses

@app.get("/debug/parcel-stats")
def debug_parcel_stats(address: str):
    lat, lon, _ = geocode_address(address, MAPBOX_TOKEN)
    geom, props, source = get_parcel_geojson_with_props(lat, lon, REGRID_TOKEN)

    g = shape(geom)
    # project to meters (Web Mercator is fine for quick stats)
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    gm = shp_transform(lambda x, y: to_m.transform(x, y), g)
    area_m2 = round(gm.area, 2)
    perim_m = round(gm.length, 2)

    return {
        "source": source,
        "geom_type": g.geom_type,
        "area_m2": area_m2,
        "perimeter_m": perim_m,
        "props_sample": dict(list(props.items())[:8]),
    }

# ---------- Main endpoint ----------

@app.post("/prep-image", response_model=MaskResult)
def prep_image(
    address: str,
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    zip: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    proximity_lat: Optional[float] = Query(None),
    proximity_lon: Optional[float] = Query(None),
    dim_neighbors_alpha: int = Query(64, ge=0, le=255),
):
    # Parse optional bbox/proximity
    bbox_list = [float(x) for x in bbox.split(",")] if bbox else None
    proximity = (proximity_lat, proximity_lon) if (proximity_lat is not None and proximity_lon is not None) else None

    # 1) Geocode with tighter constraints
    lat, lon, meta = geocode_address(
        address, MAPBOX_TOKEN,
        city=city, state=state, zip_code=zip,
        bbox=bbox_list, proximity=proximity
    )

    # 2) Parcel (geometry + props + source)
    parcel_geom, parcel_props, source = get_parcel_geojson_with_props(lat, lon)
    assert isinstance(parcel_geom, dict) and "type" in parcel_geom, \
        f"Expected GeoJSON geometry dict, got: {type(parcel_geom)}"
        
    # Compute parcel bbox in WGS84 for the STAC search
    parcel_ll = shape(parcel_geom)  # WGS84 already
    minx, miny, maxx, maxy = parcel_ll.bounds

    # small pad in degrees (~0.0006 ≈ ~65 m); you can tune
    pad_deg = 0.0008
    assets = find_naip_assets_for_bbox(minx - pad_deg, miny - pad_deg, maxx + pad_deg, maxy + pad_deg, limit=12)
    hrefs = [a.href for a in assets]
    
    if not hrefs:
        raise RuntimeError("No NAIP assets cover the parcel extent.")
    
    # 4) Output path (local; swap for S3 upload if desired)
    out_path = f"/tmp/{uuid4().hex}.png"

    # 5) Mask to parcel (with padding), draw parcel outline
    mask_naip_with_parcel_mosaic(
        naip_hrefs=hrefs,
        parcel_geojson=parcel_geom,
        out_png=out_path,
        dim_neighbors_alpha=dim_neighbors_alpha,
        superres_factor=4.0,  # upscale for better quality
    )

    # 6) Useful parcel fields (names vary by county)
    apn = parcel_props.get("ASSESSMENT_NO") or parcel_props.get("APN") or parcel_props.get("APN_NUM")
    site_addr = parcel_props.get("SITE_ADDRESS") or parcel_props.get("SITUSADDR") or parcel_props.get("SitusAddress")

    return MaskResult(
        address=address,
        image_url=out_path,
        source=source,
        matched_place_name=meta.get("matched_place_name"),
        geocode_relevance=meta.get("relevance"),
        parcel_apn=apn,
        parcel_site_address=site_addr,
    )
