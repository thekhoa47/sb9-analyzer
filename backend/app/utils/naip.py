# backend/app/utils/naip.py

from typing import List, Tuple, Optional
from dataclasses import dataclass
from pystac_client import Client
import planetary_computer as pc

NAIP_STAC_ENDPOINT = "https://planetarycomputer.microsoft.com/api/stac/v1"
NAIP_COLLECTION = "naip"

@dataclass
class NaipItem:
    href: str
    item_id: str
    year: Optional[int]

def _item_year(item) -> Optional[int]:
    props = item.properties or {}
    y = props.get("naip:year")
    if y is not None:
        try: return int(y)
        except: pass
    dt = props.get("datetime") or props.get("start_datetime")
    if dt:
        try: return int(str(dt)[:4])
        except: return None
    return None

def _sign_pref_asset(item) -> str:
    # Prefer common keys; fall back to first asset
    for k in ("image", "naip:RGBNIR", "naip", "cog"):
        if k in item.assets:
            return pc.sign(item.assets[k].href)
    # fallback
    for _, asset in item.assets.items():
        return pc.sign(asset.href)
    raise RuntimeError(f"NAIP item {item.id} has no readable asset.")

def find_naip_assets_for_bbox(
    minx: float, miny: float, maxx: float, maxy: float, prefer_years: Optional[List[int]] = None, limit: int = 12
) -> List[NaipItem]:
    """Return signed COG hrefs for all NAIP items intersecting the bbox, newest first."""
    stac = Client.open(NAIP_STAC_ENDPOINT)
    search = stac.search(collections=[NAIP_COLLECTION], bbox=[minx, miny, maxx, maxy], limit=limit)
    items = list(search.get_items())
    if not items:
        return []

    if prefer_years:
        yrs = set(prefer_years)
        pref = [it for it in items if _item_year(it) in yrs]
        items = pref or items

    # newest first
    items.sort(key=lambda it: (_item_year(it) is not None, _item_year(it) or -1), reverse=True)

    out: List[NaipItem] = []
    for it in items:
        try:
            out.append(NaipItem(href=_sign_pref_asset(it), item_id=it.id, year=_item_year(it)))
        except Exception:
            continue
    return out
