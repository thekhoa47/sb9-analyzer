from __future__ import annotations
from .geometry_ops import search_bands
from typing import NamedTuple
from shapely.geometry import LineString, Polygon

import matplotlib

matplotlib.use("Agg")

try:
    from geoalchemy2.elements import WKBElement
except Exception:  # pragma: no cover

    class WKBElement:  # type: ignore
        pass


class Eligibility(NamedTuple):
    label: str | None  # "SB9" or "ADU"
    band_low: float | None
    band_high: float | None
    angle_deg: float | None
    line: LineString | None
    image_url: str | None


def define_eligibility(
    parcel: Polygon,
    house: Polygon,
) -> Eligibility:
    sb9_bands = [(lo / 100.0, 1.0 - lo / 100.0) for lo in range(50, 39, -1)]
    adu_bands = [(lo / 100.0, 1.0 - lo / 100.0) for lo in range(39, 29, -1)]

    for label, bands in (("SB9", sb9_bands), ("ADU", adu_bands)):
        hit = search_bands(bands, parcel, house)
        if hit:
            band_low, band_high, ang, line, url = hit
            return Eligibility(
                label=label,
                band_low=band_low,
                band_high=band_high,
                angle_deg=ang,
                line=line,
                image_url=url,
            )
    return Eligibility(None, None, None, None, None, None)
