from fastapi import APIRouter, Depends, HTTPException
from app.core import get_db, settings
from app.utils.geocode import geocode_address
from app.utils.naip import find_naip_assets_for_bbox
from app.utils.parcel import get_parcel_geojson_with_props
from app.services.prepare_property import prepare_property
from app.core.model import model_manager
from sqlalchemy.orm import Session
import requests
from shapely.geometry import shape


router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/geocode")
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


@router.get("/parcel")
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


@router.get("/naip")
def debug_naip(address: str):
    lat, lon, _ = geocode_address(address, settings.MAPBOX_TOKEN)
    geom, *_ = get_parcel_geojson_with_props(lat, lon)
    g = shape(geom)
    minx, miny, maxx, maxy = g.bounds
    pad = 0.0008
    assets = find_naip_assets_for_bbox(
        minx - pad, miny - pad, maxx + pad, maxy + pad, limit=12
    )
    return {
        "count": len(assets),
        "asset_hrefs": [a.href for a in assets],
        "stac_ids": [getattr(a, "id", None) for a in assets],
    }


@router.get("/analyze")
def debug_analyze(address: str, db: Session = Depends(get_db)):
    # 1) Prove the model exists first
    if model_manager.model_runner is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # 2) Then touch external services
    try:
        property_id, mask = prepare_property(db, address)
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Parcel service timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Parcel service error: {e}")

    # 3) Predict
    label, conf, probs = model_manager.model_runner.predict_from_url(mask.image_url)
    return {
        "property_id": property_id,
        "image_url": mask.image_url,
        "predicted_label": label,
        "confidence": conf,
    }


@router.get("/model")
def debug_model():
    ok = model_manager.is_loaded
    info = getattr(model_manager.model_runner, "info", None) if ok else None
    return {"loaded": ok, "info": info}
