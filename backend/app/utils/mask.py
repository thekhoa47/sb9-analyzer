# backend/app/utils/mask.py

import numpy as np
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import transform as shp_transform
from pyproj import Transformer
import rasterio
from rasterio.windows import from_bounds
from rasterio import features
from rasterio.merge import merge as rio_merge
from PIL import Image, ImageDraw
from typing import Optional


def _exterior_only(geom):
    if geom.geom_type == "Polygon":
        return Polygon(geom.exterior)
    if geom.geom_type == "MultiPolygon":
        return MultiPolygon([Polygon(g.exterior) for g in geom.geoms])
    return geom

def mask_naip_with_parcel_mosaic(
    naip_hrefs: list,       # list of signed COG urls
    parcel_geojson: dict,   # GeoJSON (EPSG:4326)
    out_png: str,
    outline_px: int = 1,
    pad_meters: float = 20.0,
    dim_neighbors_alpha: int = 64,
    superres_factor: Optional[float] = None,  # upscale factor for final image (draw outline AFTER upscaling)
):
    """
    Build a small mosaic from multiple NAIP COGs over the parcel bbox (with padding),
    then mask/outline the parcel. No downscaling. If superres_factor > 1,
    the image is upscaled FIRST and the outline is drawn at the new scale.
    """
    if not naip_hrefs:
        raise RuntimeError("No NAIP assets for mosaic.")

    # 1) Open first to get CRS
    with rasterio.open(naip_hrefs[0]) as src0:
        raster_crs = src0.crs

    # 2) Reproject parcel to raster CRS and compute padded bounds
    parcel_ll = shape(parcel_geojson)
    to_img = Transformer.from_crs("EPSG:4326", raster_crs, always_xy=True)
    parcel_img = shp_transform(lambda x, y: to_img.transform(x, y), parcel_ll)
    parcel_img = _exterior_only(parcel_img)

    minx, miny, maxx, maxy = parcel_img.bounds
    pad = float(pad_meters)
    bbox = (minx - pad, miny - pad, maxx + pad, maxy + pad)

    # 3) Read/merge only the bbox from all assets (RGB bands)
    srcs = [rasterio.open(h) for h in naip_hrefs]
    try:
        mosaic, transform = rio_merge(
            srcs,
            bounds=bbox,
            indexes=[1, 2, 3],
            nodata=0,
            precision=7,
        )  # (bands, H, W)
    finally:
        for s in srcs:
            s.close()

    # 4) Rasterize parcel onto mosaic grid
    H, W = mosaic.shape[1], mosaic.shape[2]
    mask_arr = features.rasterize(
        [(mapping(parcel_img), 1)],
        out_shape=(H, W),
        transform=transform,
        fill=0,
        dtype=np.uint8,
    )

    # 5) Compose RGBA with dimmed neighbors (native resolution)
    rgb = np.transpose(mosaic[:3], (1, 2, 0))  # (H,W,3)
    alpha = np.where(mask_arr == 1, 255, dim_neighbors_alpha).astype(np.uint8)
    rgba = np.concatenate([rgb, alpha[..., None]], axis=-1)
    img = Image.fromarray(rgba, mode="RGBA")

    # --- Outline drawing with crisp scaling ---

    # A) compute base pixel ring using inverse transform (at native size)
    inv = ~transform
    base_ring_px = [ ( (inv * (x, y))[0], (inv * (x, y))[1] )
                     for (x, y) in list(parcel_img.exterior.coords) ]

    # B) optional upscale FIRST (so line is rendered at high-res)
    scale = float(superres_factor) if superres_factor and superres_factor > 1 else 1.0
    if scale > 1.0:
        new_w = int(round(img.width  * scale))
        new_h = int(round(img.height * scale))
        img = img.resize((new_w, new_h), resample=Image.LANCZOS)

    # C) draw outline AFTER upscale, scaling coords & width
    draw = ImageDraw.Draw(img)
    if scale > 1.0:
        ring_px = [ (p[0]*scale, p[1]*scale) for p in base_ring_px ]
        line_w  = max(1, int(round(outline_px * scale)))
    else:
        ring_px = base_ring_px
        line_w  = max(1, int(outline_px))

    draw.line(ring_px, width=line_w, fill=(255, 0, 0, 255))

    # 6) Save to PNG
    img.save(out_png)
    return out_png
