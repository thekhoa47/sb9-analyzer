from fastapi import FastAPI, HTTPException
from typing import Tuple
from io import BytesIO
import os

from dotenv import load_dotenv
from shapely.geometry import shape
from shapely.ops import transform as shp_transform
from pyproj import Transformer

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text, select
from geoalchemy2.shape import to_shape, from_shape

from app.utils.geocode import geocode_address
from app.utils.naip import find_naip_assets_for_bbox
from app.utils.mask import (
    mask_naip_with_parcel_mosaic,
)  # will return PIL Image with return_image=True
from app.utils.parcel import get_parcel_geojson_with_props
from app.storage.r2 import upload_bytes_and_get_url
from app.schemas import MaskResult, ParcelStats
from app.models import Property

load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

app = FastAPI(title="sb9-analyzer backend", version="0.3.1")

# ---------- Small adapter: mask -> PNG bytes (no /tmp write) ----------


def mask_to_png_bytes(
    naip_hrefs, parcel_geojson, superres_factor: float = 4.0
) -> bytes:
    """
    Assumes mask_naip_with_parcel_mosaic can return a PIL.Image when return_image=True.
    """
    img = mask_naip_with_parcel_mosaic(
        naip_hrefs=naip_hrefs,
        parcel_geojson=parcel_geojson,
        superres_factor=superres_factor,
        return_image=True,  # implement in your util
    )
    bio = BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


# ---------- Main Function ----------


def prepare_property(
    db: Session,
    address: str,
) -> Tuple[str, MaskResult]:
    """
    Runs the same logic as /prep-image but returns (property_id, MaskResult)
    so other endpoints can reuse it without HTTP round-trips.
    """
    # 1) Geocode (seed for parcel lookup)
    lat_seed, lon_seed, meta = geocode_address(address, MAPBOX_TOKEN)

    # Pull official postal parts (what we use for identity + display)
    parts = meta.get("official_parts", {}) or {}
    addr = parts.get("address")
    city_off = parts.get("city")
    state_off = parts.get("state")
    zip_off = parts.get("zip")

    # --- FAST PATH: if property already exists, return it and skip NAIP + upload ---
    def _eq_or_null(col, val):
        return (col == val) if val is not None else col.is_(None)

    existing = db.execute(
        select(Property).where(
            _eq_or_null(Property.address, addr),
            _eq_or_null(Property.city, city_off),
            _eq_or_null(Property.state, state_off),
            _eq_or_null(Property.zip, zip_off),
        )
    ).scalar_one_or_none()

    if existing:
        # Optional: compute parcel stats for UI from stored geometry
        parcel_stats = None
        if existing.parcel_geom is not None:
            g_existing = to_shape(existing.parcel_geom)
            to_m = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
            gm = shp_transform(lambda x, y: to_m.transform(x, y), g_existing)
            parcel_stats = ParcelStats(
                area_m2=round(gm.area, 2), perimeter_m=round(gm.length, 2)
            )

        return existing.id, MaskResult(
            id=existing.id,
            address=existing.address,
            city=existing.city,
            state=existing.state,
            zip=existing.zip,
            beds=existing.beds,
            baths=existing.baths,
            year_built=existing.year_built,
            living_area=existing.living_area,
            lot_area=existing.lot_area,
            image_url=existing.image_url,
            parcel_stats=parcel_stats,
        )

    # --- SLOW PATH: not found → do parcel lookup, render, upload once ---

    # 2) Parcel → extras (beds/baths/year_built/areas)
    parcel_geom, props, extras = get_parcel_geojson_with_props(lat_seed, lon_seed)

    # 3) NAIP → masked PNG bytes (no local file)
    g = shape(parcel_geom)  # WGS84 GeoJSON
    minx, miny, maxx, maxy = g.bounds
    pad_deg = 0.0008
    assets = find_naip_assets_for_bbox(
        minx - pad_deg, miny - pad_deg, maxx + pad_deg, maxy + pad_deg, limit=12
    )
    hrefs = [a.href for a in assets]
    if not hrefs:
        raise HTTPException(
            status_code=422, detail="No NAIP assets cover the parcel extent."
        )

    png_bytes = mask_to_png_bytes(hrefs, parcel_geom, superres_factor=4.0)

    # 5) Compute centroid / stats
    centroid = g.centroid
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    gm = shp_transform(lambda x, y: to_m.transform(x, y), g)
    area_m2 = round(gm.area, 2)
    perim_m = round(gm.length, 2)

    geom_wkb = from_shape(g, srid=4326)
    centroid_wkb = from_shape(centroid, srid=4326)

    # 6a) INSERT first (without image_url) to get a stable property_id
    row = {
        "address": addr,
        "city": city_off,
        "state": state_off,
        "zip": zip_off,
        "parcel_geom": geom_wkb,
        "parcel_centroid": centroid_wkb,
        "beds": extras.get("beds"),
        "baths": extras.get("baths"),
        "year_built": extras.get("year_built"),
        "living_area": extras.get("living_area"),
        "lot_area": extras.get("lot_area"),
        # image_url set after upload
    }
    # Use ON CONFLICT to handle a rare race (someone inserted after our fast lookup)
    ins = (
        pg_insert(Property.__table__)
        .values(**row)
        .on_conflict_do_update(
            constraint="ux_properties_addr",
            set_={
                "parcel_geom": pg_insert(Property.__table__).excluded.parcel_geom,
                "parcel_centroid": pg_insert(
                    Property.__table__
                ).excluded.parcel_centroid,
                "beds": pg_insert(Property.__table__).excluded.beds,
                "baths": pg_insert(Property.__table__).excluded.baths,
                "year_built": pg_insert(Property.__table__).excluded.year_built,
                "living_area": pg_insert(Property.__table__).excluded.living_area,
                "lot_area": pg_insert(Property.__table__).excluded.lot_area,
                "updated_at": text("now()"),
            },
        )
        .returning(Property.id)
    )
    property_id = db.execute(ins).scalar_one()
    db.commit()

    # 6b) Deterministic R2 key → avoids duplicate objects forever
    key = f"results/{property_id}.png"
    image_url = upload_bytes_and_get_url(key, png_bytes, "image/png")

    # 6c) Update image_url (and updated_at)
    db.execute(
        Property.__table__.update()
        .where(Property.id == property_id)
        .values(image_url=image_url, updated_at=text("now()"))
    )
    db.commit()

    # 7) Response mirrors table (no createdAt/updatedAt)
    return property_id, MaskResult(
        id=property_id,
        address=addr,
        city=city_off,
        state=state_off,
        zip=zip_off,
        beds=extras.get("beds"),
        baths=extras.get("baths"),
        year_built=extras.get("year_built"),
        living_area=extras.get("living_area"),
        lot_area=extras.get("lot_area"),
        image_url=image_url,
        parcel_stats=ParcelStats(area_m2=area_m2, perimeter_m=perim_m),
    )
