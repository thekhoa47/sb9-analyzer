# app/ml/sb9_rules.py
"""
SB9 geometric rules (no ML): split parcel polygons and check feasibility.

Core ideas:
1) Try candidate split lines (parallel/perpendicular to street, or cardinal),
   targeting area ratios like 50/50 or 60/40.
2) Require the main house footprint to lie entirely within ONE side.
3) Require a drivable corridor from the street frontage to the rear lot,
   at least `min_drive_width` wide, optionally respecting a house setback.

All geometry is assumed to be in a projected CRS where "feet" or "meters"
make sense. If you provide lat/lon, reproject first.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Union, Dict, Any

import math
from shapely.geometry import Polygon, LineString, MultiPolygon, mapping
from shapely.ops import split, unary_union
from shapely.affinity import translate


Geom = Union[Polygon, MultiPolygon]
Lineish = Union[LineString]

SMALL = 1e-6  # geometric robustness buffer


# ----------------------------- Utilities -------------------------------------


def _bearing_degrees(line: LineString) -> float:
    """
    Approximate bearing of a line (degrees). Returns angle in [0, 180).
    We only care about orientation, not direction.
    """
    x0, y0, x1, y1 = *line.coords[0], *line.coords[-1]
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    ang = (ang + 360.0) % 180.0  # fold to [0,180)
    return ang


def _candidate_angles(street: Optional[LineString]) -> List[float]:
    """
    Generate candidate split orientations (degrees).
    If street provided, use its bearing and bearing+90; otherwise use 0, 90.
    """
    if street is not None and not street.is_empty and len(street.coords) >= 2:
        b = _bearing_degrees(street)
        return [b, (b + 90.0) % 180.0]
    return [0.0, 90.0]


def _long_line_through(
    center_x: float, center_y: float, angle_deg: float, half_extent: float = 1e4
) -> LineString:
    """
    Create a long line passing through (cx,cy) with given angle (degrees).
    """
    theta = math.radians(angle_deg)
    dx, dy = math.cos(theta), math.sin(theta)
    p0 = (center_x - half_extent * dx, center_y - half_extent * dy)
    p1 = (center_x + half_extent * dx, center_y + half_extent * dy)
    return LineString([p0, p1])


def _translate(line: LineString, xoff: float, yoff: float) -> LineString:
    return translate(line, xoff=xoff, yoff=yoff)


def _slide_line(line: LineString, angle_deg: float, step: float) -> LineString:
    """
    Slide 'line' along its normal by 'step' units.
    Positive steps are arbitrary; we scan both directions in caller.
    """
    normal_angle = math.radians(angle_deg + 90.0)
    return translate(
        line, xoff=step * math.cos(normal_angle), yoff=step * math.sin(normal_angle)
    )


def _sorted_by_area(parts: Sequence[Polygon]) -> Tuple[Polygon, Polygon]:
    a, b = parts
    return (a, b) if a.area >= b.area else (b, a)


def _connected(a: Geom, b: Geom) -> bool:
    """
    Heuristic connectivity check using a tiny dilation to close slivers.
    """
    return not a.buffer(SMALL).intersection(b.buffer(SMALL)).is_empty


# -------------------------- Split search --------------------------------------


def _split_for_ratio(
    parcel: Polygon,
    angle_deg: float,
    ratio: float,
    tol: float = 0.03,
    span: float = 200.0,
    steps: int = 401,
) -> Optional[Tuple[Polygon, Polygon, LineString]]:
    """
    Slide a line at angle_deg across the parcel to find a ~ratio area split.
    - ratio is the target fraction for one piece (e.g., 0.5 or 0.6)
    - tol is relative error tolerance (e.g., 0.03 = ±3%)

    Returns (larger_piece, smaller_piece, split_line) or None if not found.
    """
    cx, cy = parcel.centroid.x, parcel.centroid.y
    base = _long_line_through(cx, cy, angle_deg)
    target_area = ratio * parcel.area

    # Search symmetric around the center
    best = None
    for i in range(steps):
        # steps in [-span, +span]
        t = (i / (steps - 1)) * 2.0 * span - span
        L = _slide_line(base, angle_deg, t)
        try:
            parts = split(parcel, L.buffer(SMALL))
        except Exception:
            continue
        if len(parts) != 2:
            continue
        p1, p2 = parts[0], parts[1]
        # select the piece whose area is closer to the target
        err = min(abs(p1.area - target_area), abs(p2.area - target_area)) / parcel.area
        if err <= tol:
            big, small = _sorted_by_area((p1, p2))
            best = (big, small, L)
            break
    return best


def _house_on_one_side(
    big: Polygon, small: Polygon, house: Polygon
) -> Optional[Tuple[Polygon, Polygon]]:
    """
    Ensure the house footprint lies entirely within exactly one part.
    Returns (front, rear) assuming 'front' is where the house is, else None.
    """
    if house.within(big) and not house.intersects(small):
        return big, small
    if house.within(small) and not house.intersects(big):
        return small, big
    return None


# ----------------------- Driveway corridor rule -------------------------------


def _driveway_open_space(
    whole: Geom,
    house: Polygon,
    min_drive_width: float,
    setback: float,
) -> Geom:
    """
    Remove an expanded house buffer from the whole parcel to leave potential
    driveable open space.
    """
    block = house.buffer((min_drive_width / 2.0) + setback)
    open_space = whole.difference(block)
    return open_space


def _has_corridor_between(open_space: Geom, a: Geom, b: Geom, width: float) -> bool:
    """
    Determine if a corridor of at least 'width' connects regions touching 'a'
    and regions touching 'b'. Uses buffered intersections and connectivity
    heuristic.
    """
    touch_a = open_space.intersection(a.buffer(width / 2.0))
    if touch_a.is_empty:
        return False
    touch_b = open_space.intersection(b.buffer(width / 2.0))
    if touch_b.is_empty:
        return False
    return _connected(touch_a, touch_b)


# ----------------------------- Public API -------------------------------------


@dataclass
class SB9SplitResult:
    status: str  # "YES" | "NO" | "UNCERTAIN"
    front: Optional[Polygon] = None
    rear: Optional[Polygon] = None
    split_line: Optional[LineString] = None
    meta: Optional[Dict[str, Any]] = None  # e.g., {'ratio': 0.5, 'angle': 90.0}


def evaluate_sb9_feasibility(
    parcel: Polygon,
    house: Polygon,
    street: Optional[LineString] = None,
    ratios: Sequence[float] = (0.5, 0.6),
    angle_overrides: Optional[Sequence[float]] = None,
    ratio_tol: float = 0.03,  # ±3% area tolerance
    search_span: float = 200.0,  # how far to slide search line (units of CRS)
    search_steps: int = 401,  # resolution of sliding search
    min_drive_width: float = 12.0,  # feet (or CRS units)
    house_setback: float = 0.0,  # additional "no-drive" clearance around house
) -> SB9SplitResult:
    """
    Try to split `parcel` according to SB9-inspired constraints:
      - house must be entirely on one side of the split,
      - rear lot must have a drivable corridor to the street frontage.

    Returns SB9SplitResult with status "YES", "NO", or "UNCERTAIN".
    """
    # Choose candidate orientations
    angle_list = list(angle_overrides) if angle_overrides else _candidate_angles(street)

    # Street-facing line for driveway checks:
    street_for_touch = street if street is not None else parcel.boundary  # fallback

    best_meta = None

    for angle in angle_list:
        for r in ratios:
            res = _split_for_ratio(
                parcel, angle, r, tol=ratio_tol, span=search_span, steps=search_steps
            )
            if not res:
                continue
            part1, part2, L = res

            # Ensure the house sits entirely in one piece
            side = _house_on_one_side(part1, part2, house)
            if not side:
                # This split slices through the house or straddles it
                continue
            front, rear = side  # front := the side containing house

            # Heuristic: ensure 'front' actually fronts the street; if not, swap
            if street is not None:
                if (
                    front.intersection(street.buffer(SMALL)).is_empty
                    and not rear.intersection(street.buffer(SMALL)).is_empty
                ):
                    front, rear = rear, front

            # Driveway corridor rule
            whole = unary_union([front, rear])
            open_space = _driveway_open_space(
                whole, house, min_drive_width=min_drive_width, setback=house_setback
            )

            has_corridor = _has_corridor_between(
                open_space, street_for_touch, rear, width=min_drive_width
            )

            best_meta = {"ratio": r, "angle": float(angle)}

            if has_corridor:
                return SB9SplitResult(
                    status="YES",
                    front=front,
                    rear=rear,
                    split_line=L,
                    meta=best_meta,
                )
            else:
                # Keep as a candidate; if nothing passes, we may return UNCERTAIN with this
                uncertain = SB9SplitResult(
                    status="UNCERTAIN",
                    front=front,
                    rear=rear,
                    split_line=L,
                    meta=best_meta,
                )
                # Don't return immediately; a different angle/ratio might succeed
                maybe_uncertain = uncertain

    # If we reached here, no candidate passed the corridor rule.
    # If we found at least one house-valid split, return UNCERTAIN; else NO.
    if "maybe_uncertain" in locals():
        return maybe_uncertain  # type: ignore[name-defined]
    return SB9SplitResult(status="NO")


# ----------------------------- GeoJSON helpers --------------------------------


def to_geojson_features(result: SB9SplitResult) -> Dict[str, Any]:
    """
    Convert an SB9SplitResult into a simple FeatureCollection for frontend display.
    """
    feats: List[Dict[str, Any]] = []

    if result.front is not None:
        feats.append(
            {
                "type": "Feature",
                "geometry": mapping(result.front),
                "properties": {
                    "layer": "front_lot",
                    "status": result.status,
                    **(result.meta or {}),
                },
            }
        )
    if result.rear is not None:
        feats.append(
            {
                "type": "Feature",
                "geometry": mapping(result.rear),
                "properties": {
                    "layer": "rear_lot",
                    "status": result.status,
                    **(result.meta or {}),
                },
            }
        )
    if result.split_line is not None:
        feats.append(
            {
                "type": "Feature",
                "geometry": mapping(result.split_line),
                "properties": {
                    "layer": "split_line",
                    "status": result.status,
                    **(result.meta or {}),
                },
            }
        )

    return {"type": "FeatureCollection", "features": feats}
