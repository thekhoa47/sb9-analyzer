from typing import Dict, Tuple, Optional
from app.utils.parcel_fallback_oc import get_oc_parcel_by_point_full

def _pick(props: Dict[str, any], *candidates: str, default=None):
    """Case-insensitive getter that tries several field names."""
    if not props:
        return default
    lower_map = {k.lower(): v for k, v in props.items()}
    for key in candidates:
        v = lower_map.get(key.lower())
        if v not in (None, ""):
            return v
    return default

def get_parcel_geojson_with_props(lat: float, lon: float):
    geom, props = get_oc_parcel_by_point_full(lat, lon)

    # Extras (best-effort; keep None if not present)
    extras = {
        "beds":        props.get("NBR_BEDROOMS"),
        "baths":       _pick(props, "BATHS", "Bathrooms", "NUM_BATHS", "BATHROOMS"),
        "year_built":  props.get("YEAR_BUILT"),
        "living_area": _pick(props, "BLDG_SQFT", "LIVING_SQFT", "SQFT", "SQFT_LIVING"),
        "lot_area":    _pick(props, "LOT_SQFT", "LOT_SIZE", "PARCEL_SQFT", "Acres"),
    }
    return geom, props, extras

def derive_official_address_parts(props: Dict) -> Dict[str, Optional[str]]:
    # Common county field fallbacks (tweak per county):
    # Examples: "SITE_ADDRESS", "SITUSADDR", or components like "ADDR_NUM", "STNAME", "STSUF"
    line = (
        props.get("SITE_ADDRESS")
        or props.get("SITUSADDR")
        or props.get("SitusAddress")
        or props.get("ADDR_FULL")
        or " ".join(
            filter(
                None,
                [
                    props.get("ADDR_NUM"),
                    props.get("STPRE"),
                    props.get("STNAME"),
                    props.get("STSUF"),
                    props.get("STPOST"),
                ],
            )
        )
        or None
    )
    city = props.get("CITY") or props.get("MUNI") or props.get("Town") or None
    state = props.get("STATE") or "CA"  # sensible default; replace if your data has it
    zipc = props.get("ZIP") or props.get("ZIPCODE") or None
    return {"address": line, "city": city, "state": state, "zip": zipc}

def extract_property_extras(props: Dict) -> Dict[str, Optional[int]]:
    # Normalize optional numeric fields when present
    def parse_int(x):
        try:
            return int(x) if x is not None and str(x).strip() != "" else None
        except Exception:
            return None

    return {
        "beds": parse_int(props.get("BEDS") or props.get("Bedrooms")),
        "baths": parse_int(props.get("BATHS") or props.get("Bathrooms")),
        "year_built": parse_int(props.get("YEAR_BUILT") or props.get("YearBuilt")),
        "living_area": parse_int(props.get("LIVING_AREA") or props.get("SqFt")),
        "lot_area": parse_int(props.get("LOT_AREA") or props.get("LotSize")),
    }