from __future__ import annotations
from typing import Any
import io
import math
from uuid import uuid4
from datetime import datetime

from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import split as shp_split
from shapely import wkb as shapely_wkb
from app.storage.r2 import upload_bytes_and_get_url

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    # optional: if you pass a GeoAlchemy2 WKBElement
    from geoalchemy2.elements import WKBElement
except Exception:  # pragma: no cover

    class WKBElement:  # type: ignore
        pass


def ewkb_or_shapely_to_esri(geom, wkid: int = 2230):
    """
    Convert EWKB/WKBElement or Shapely Polygon/MultiPolygon to Esri JSON Polygon.
    Works for both PostGIS geometries (WKBElement) and Shapely objects.
    """
    # Normalize to Shapely geometry
    if isinstance(geom, (Polygon, MultiPolygon)):
        g = geom
    elif WKBElement is not None and isinstance(geom, WKBElement):
        g = shapely_wkb.loads(bytes(geom.data))
        wkid = geom.srid or wkid
    elif isinstance(geom, str):
        g = shapely_wkb.loads(bytes.fromhex(geom))
    elif isinstance(geom, (bytes, bytearray)):
        g = shapely_wkb.loads(geom)
    else:
        raise TypeError("Expected Polygon, MultiPolygon, WKBElement, hex str, or bytes")

    if g.is_empty:
        return {"rings": [], "spatialReference": {"wkid": wkid}}

    def close_ring(seq):
        pts = [[float(x), float(y)] for x, y in seq]
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        return pts

    def to_rings(p):
        p = orient(p, sign=-1.0)  # ensure Esri convention: outer CW, holes CCW
        rings = [close_ring(p.exterior.coords)]
        rings += [close_ring(r.coords) for r in p.interiors]
        return rings

    rings = []
    if isinstance(g, Polygon):
        rings = to_rings(g)
    elif isinstance(g, MultiPolygon):
        for p in g.geoms:
            rings.extend(to_rings(p))

    return {"rings": rings, "spatialReference": {"wkid": wkid}}


def projection_interval(poly: Polygon, angle_deg: float) -> tuple[float, float]:
    theta = math.radians(angle_deg)
    ux, uy = math.cos(theta), math.sin(theta)
    xs, ys = poly.exterior.coords.xy
    dots = [x * ux + y * uy for x, y in zip(xs, ys)]
    return min(dots), max(dots)


def make_infinite_cut(bounds, centroid, angle_deg: float, s: float) -> LineString:
    minx, miny, maxx, maxy = bounds
    cx, cy = centroid.x, centroid.y

    theta = math.radians(angle_deg)
    ux, uy = math.cos(theta), math.sin(theta)  # normal
    vx, vy = -uy, ux  # along-line direction

    dot_c = cx * ux + cy * uy
    delta = s - dot_c
    px, py = cx + delta * ux, cy + delta * uy

    diag = math.hypot(maxx - minx, maxy - miny)
    L = 3 * diag if diag > 0 else 100.0
    p1 = (px - L * vx, py - L * vy)
    p2 = (px + L * vx, py + L * vy)
    return LineString([p1, p2])


def search_bands(
    bands,
    parcel: Polygon,
    house: Polygon,
    *,
    angle_step_deg: float = 2.0,
    offset_samples: int = 200,
    strict_contains: bool = True,
    min_clearance_ft: float = 5.0,
    key_prefix: str = "splits",
) -> tuple[float, float, float, LineString, str] | None:
    """Return (band, angle_deg, cut_line, image_url) on success, else None."""
    A_parcel = parcel.area
    parcel = parcel.buffer(0)
    house = house.buffer(0)
    contains_fn = (
        (lambda p: p.contains(house))
        if strict_contains
        else (lambda p: p.covers(house))
    )

    for lo, hi in bands:
        ang = 0.0
        while ang < 180.0:
            lo_p, hi_p = projection_interval(parcel, ang)
            for i in range(offset_samples + 1):
                s = lo_p + (hi_p - lo_p) * (i / offset_samples)
                line = make_infinite_cut(parcel.bounds, parcel.centroid, ang, s)

                # Minimum clearance (house must not touch line)
                if house.exterior.distance(line) < min_clearance_ft:
                    continue

                pieces = shp_split(parcel, line)
                if len(pieces.geoms) < 2:
                    continue

                piece = next((p for p in pieces.geoms if contains_fn(p)), None)
                if piece is None:
                    continue

                frac = piece.area / A_parcel
                if lo <= frac <= hi:
                    # Render & upload
                    meta = {"fraction": float(frac), "angle_deg": round(ang, 3)}
                    svg = render_svg(parcel, house, line, meta)
                    ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
                    key = f"{key_prefix}/{ts}-{uuid4().hex}.svg"
                    url = upload_bytes_and_get_url(
                        key, svg, content_type="image/svg+xml"
                    )
                    return lo, hi, float(ang), line, url
            ang += angle_step_deg
    return None


def render_svg(
    parcel: Polygon, house: Polygon, cut: LineString, meta: dict[str, Any]
) -> bytes:
    fig, ax = plt.subplots(figsize=(6.5, 6.5))

    x, y = parcel.exterior.xy
    ax.fill(x, y, alpha=0.20, label="Parcel")

    hx, hy = house.exterior.xy
    ax.fill(hx, hy, alpha=0.45, label="House")

    cx, cy = cut.xy
    ax.plot(cx, cy, linewidth=2.2, linestyle="--", label="Cut line")

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X (ft, EPSG:2230)")
    ax.set_ylabel("Y (ft, EPSG:2230)")
    ax.set_title(f"Split: {meta.get('fraction'):.3f} (angle {meta.get('angle_deg')}°)")

    ax.legend(loc="best")
    minx, miny, maxx, maxy = parcel.bounds
    pad_x = (maxx - minx) * 0.05
    pad_y = (maxy - miny) * 0.05
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="svg")
    plt.close(fig)
    return buf.getvalue()
