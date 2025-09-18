# split_finder.py
# Requires: shapely>=2, matplotlib, boto3

from __future__ import annotations
from typing import Iterable, Tuple, Dict, Any
import io
import math
import uuid
import datetime as dt

from shapely.geometry import Polygon, LineString
from shapely.ops import split as shp_split
from app.storage.r2 import upload_bytes_and_get_url

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------- geometry helpers ----------


def _to_polygon_xy(coords_xy: Iterable[Tuple[float, float]]) -> Polygon:
    poly = Polygon(coords_xy)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def _projection_interval(poly: Polygon, angle_deg: float) -> Tuple[float, float]:
    theta = math.radians(angle_deg)
    ux, uy = math.cos(theta), math.sin(theta)
    xs, ys = poly.exterior.coords.xy
    dots = [x * ux + y * uy for x, y in zip(xs, ys)]
    return min(dots), max(dots)


def _make_infinite_cut(bounds, centroid, angle_deg: float, s: float) -> LineString:
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


# ---------- render & upload ----------


def _render_svg(
    parcel: Polygon, house: Polygon, cut: LineString, meta: Dict[str, Any]
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


# ---------- main ----------


def find_house_containment_split_feet(
    parcel_xy: Iterable[Tuple[float, float]],
    house_xy: Iterable[Tuple[float, float]],
    *,
    angle_step_deg: float = 2.0,
    offset_samples: int = 200,
    strict_contains: bool = True,
    min_clearance_ft: float = 5.0,
    key_prefix: str = "splits",
) -> Dict[str, Any]:
    """
    SB9 pass: try 50–50 down to 40–60. If found -> sb9=True, adu=True.
    If SB9 fails: try ADU-only 39–61 down to 30–70. If found -> sb9=False, adu=True.
    Else -> sb9=False, adu=False.
    Exits early at first success and returns an SVG URL.
    """
    # Phase 1 (SB9): 50–50, 49–51, ..., 40–60
    sb9_bands = [(lo / 100.0, 1.0 - lo / 100.0) for lo in range(50, 39, -1)]
    # Phase 2 (ADU-only): 39–61, 38–62, ..., 30–70
    adu_bands = [(lo / 100.0, 1.0 - lo / 100.0) for lo in range(39, 29, -1)]

    parcel = _to_polygon_xy(parcel_xy)
    house = _to_polygon_xy(house_xy)

    A_parcel = parcel.area
    A_house = house.area
    if A_parcel <= 0 or A_house <= 0:
        return {
            "found": False,
            "sb9": False,
            "adu": False,
            "error": "Invalid parcel or house area.",
        }

    contains_fn = (
        (lambda p: p.contains(house))
        if strict_contains
        else (lambda p: p.covers(house))
    )

    def _search_bands(bands, label: str) -> Dict[str, Any] | None:
        """Try bands (ordered); return meta dict if found, else None."""
        for lo, hi in bands:
            ang = 0.0
            while ang < 180.0:
                lo_p, hi_p = _projection_interval(parcel, ang)
                for i in range(offset_samples + 1):
                    s = lo_p + (hi_p - lo_p) * (i / offset_samples)
                    line = _make_infinite_cut(parcel.bounds, parcel.centroid, ang, s)

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
                        # Build meta and upload SVG
                        meta = {
                            "found": True,
                            "band": (lo, hi),
                            "angle_deg": round(ang, 3),
                            "fraction": float(frac),
                            "parcel_sqft": float(A_parcel),
                            "house_sqft": float(A_house),
                            "clearance_ft": float(house.exterior.distance(line)),
                            "phase": label,
                        }
                        svg = _render_svg(parcel, house, line, meta)
                        ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                        key = f"{key_prefix}/{ts}-{uuid.uuid4().hex}.svg"
                        url = upload_bytes_and_get_url(
                            key, svg, content_type="image/svg+xml"
                        )
                        meta["imageURL"] = url
                        return meta
                ang += angle_step_deg
        return None

    # --- Phase 1: SB9 ---
    sb9_meta = _search_bands(sb9_bands, label="SB9")
    if sb9_meta is not None:
        sb9_meta["sb9"] = True
        sb9_meta["adu"] = True
        return sb9_meta  # early exit

    # --- Phase 2: ADU-only ---
    adu_meta = _search_bands(adu_bands, label="ADU")
    if adu_meta is not None:
        adu_meta["sb9"] = False
        adu_meta["adu"] = True
        return adu_meta  # early exit

    # Neither SB9 nor ADU bands worked
    return {
        "found": False,
        "sb9": False,
        "adu": False,
        "note": "No valid split found in SB9 or ADU bands.",
    }
