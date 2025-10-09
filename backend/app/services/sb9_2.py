from __future__ import annotations
from typing import Dict, Any
import io
import math
from uuid import UUID, uuid4
from datetime import datetime

from geoalchemy2.shape import from_shape
from shapely.geometry import shape, Polygon, LineString
from shapely.ops import split as shp_split
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.r2 import upload_bytes_and_get_url
from app.models import PropertyAnalysis

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------- geometry helpers ----------


def _to_polygon_xy(coords_xy: dict) -> Polygon:
    poly = shape(coords_xy)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def _projection_interval(poly: Polygon, angle_deg: float) -> tuple[float, float]:
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


async def find_house_containment_split_feet(
    session: AsyncSession,
    property_id: UUID,
    parcel_xy: dict,
    house_xy: dict,
    *,
    angle_step_deg: float = 2.0,
    offset_samples: int = 200,
    strict_contains: bool = True,
    min_clearance_ft: float = 5.0,
    key_prefix: str = "splits",
    force_recompute: bool = False,
) -> "PropertyAnalysis":
    # --- short-circuit if we already have an analysis ---
    if not force_recompute:
        existing = await session.scalar(
            select(PropertyAnalysis).where(PropertyAnalysis.property_id == property_id)
        )
        if existing:
            return existing

    sb9_bands = [(lo / 100.0, 1.0 - lo / 100.0) for lo in range(50, 39, -1)]
    adu_bands = [(lo / 100.0, 1.0 - lo / 100.0) for lo in range(39, 29, -1)]

    parcel = _to_polygon_xy(parcel_xy)
    house = _to_polygon_xy(house_xy)

    A_parcel = parcel.area

    contains_fn = (
        (lambda p: p.contains(house))
        if strict_contains
        else (lambda p: p.covers(house))
    )

    def _search_bands(
        bands,
    ) -> tuple[tuple[float, float], float, LineString, str] | None:
        """Return (band, angle_deg, cut_line, image_url) on success, else None."""
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
                        # Render & upload
                        meta = {"fraction": float(frac), "angle_deg": round(ang, 3)}
                        svg = _render_svg(parcel, house, line, meta)
                        ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
                        key = f"{key_prefix}/{ts}-{uuid4().hex}.svg"
                        url = upload_bytes_and_get_url(
                            key, svg, content_type="image/svg+xml"
                        )
                        return (lo, hi), float(ang), line, url
                ang += angle_step_deg
        return None

    # --- Phase 1: SB9 ---
    sb9_hit = _search_bands(sb9_bands)
    if sb9_hit is not None:
        band, ang, line, url = sb9_hit
        return await _persist_property_analysis(
            session=session,
            property_id=property_id,
            sb9=True,
            adu=True,
            band=band,
            angle_deg=ang,
            cut_line=line,
            image_url=url,
        )

    # --- Phase 2: ADU-only ---
    adu_hit = _search_bands(adu_bands)
    if adu_hit is not None:
        band, ang, line, url = adu_hit
        return await _persist_property_analysis(
            session=session,
            property_id=property_id,
            sb9=False,
            adu=True,
            band=band,
            angle_deg=ang,
            cut_line=line,
            image_url=url,
        )

    # --- Neither SB9 nor ADU bands worked ---
    return await _persist_property_analysis(
        session=session,
        property_id=property_id,
        sb9=False,
        adu=False,
        band=None,
        angle_deg=None,
        cut_line=None,
        image_url=None,
    )


# ---------- persistence helper (tiny, isolated) ----------


async def _persist_property_analysis(
    session: AsyncSession,
    property_id: UUID,
    *,
    sb9: bool,
    adu: bool,
    band: tuple[float, float] | None,
    angle_deg: float | None,
    cut_line: LineString | None,
    image_url: str | None,
) -> PropertyAnalysis:
    lo_pct, hi_pct = (
        (int(round(band[0] * 100)), int(round(band[1] * 100))) if band else (None, None)
    )
    line_geom = from_shape(cut_line, srid=2230) if cut_line is not None else None

    existing = await session.scalar(
        select(PropertyAnalysis).where(PropertyAnalysis.property_id == property_id)
    )
    if existing:
        existing.sb9_possible = sb9
        existing.adu_possible = adu
        existing.band_low = lo_pct
        existing.band_high = hi_pct
        existing.split_angle_degree = (
            float(angle_deg) if angle_deg is not None else None
        )
        existing.split_line_geometry = line_geom
        existing.image_url = image_url
        return existing

    row = PropertyAnalysis(
        property_id=property_id,
        sb9_possible=sb9,
        adu_possible=adu,
        band_low=lo_pct,
        band_high=hi_pct,
        split_angle_degree=float(angle_deg) if angle_deg is not None else None,
        split_line_geometry=line_geom,
        image_url=image_url,
    )
    session.add(row)
    return row
