# backend/app/utils/geocode.py
import requests
from typing import Optional, Tuple, Dict, Any, List

def _compose_address(address: str, city: Optional[str], state: Optional[str], zip_code: Optional[str]) -> str:
    parts = [address]
    if city: parts.append(city)
    if state: parts.append(state)
    if zip_code: parts.append(zip_code)
    return ", ".join([p for p in parts if p and p.strip()])

def geocode_address(
    address: str,
    mapbox_token: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    country: str = "US",
    bbox: Optional[List[float]] = None,          # [minLon, minLat, maxLon, maxLat] in WGS84
    proximity: Optional[Tuple[float, float]] = None,  # (lat, lon)
    limit: int = 5,
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Returns (lat, lon, meta) for the best address match.
    meta includes 'matched_place_name', 'relevance', 'raw_feature'.
    """
    q = _compose_address(address, city, state, zip_code)
    params = {
        "access_token": mapbox_token,
        "limit": limit,
        "types": "address",
        "country": country,
        "autocomplete": "false",
        "fuzzyMatch": "false",
    }
    if bbox:
        # bbox must be comma-separated string lon1,lat1,lon2,lat2
        params["bbox"] = ",".join(str(x) for x in bbox)
    if proximity:
        plat, plon = proximity
        params["proximity"] = f"{plon},{plat}"  # Mapbox wants lon,lat here

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{q}.json"
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features", [])

    if not feats:
        raise RuntimeError(f"Geocoding returned no results for: {q}")

    # If city/state/zip provided, prefer candidates whose context matches them
    def score_feature(f):
        s = 0.0
        ctx = f.get("context", []) + [ {"id": f.get("id",""), "text": f.get("text","")} ]
        texts = {c.get("id",""): c.get("text","").lower() for c in ctx}

        if city and city.lower() in "".join(texts.values()):
            s += 2.0
        if state and state.lower() in "".join(texts.values()):
            s += 1.5
        if zip_code and zip_code.lower() in "".join(texts.values()):
            s += 1.0
        # native relevance from Mapbox (0..1)
        s += float(f.get("relevance", 0))
        return s

    feats_sorted = sorted(feats, key=score_feature, reverse=True)
    top = feats_sorted[0]
    lon, lat = top["center"]  # Mapbox returns [lon, lat]
    meta = {
        "matched_place_name": top.get("place_name"),
        "relevance": top.get("relevance"),
        "raw_feature": top,
    }
    return lat, lon, meta
