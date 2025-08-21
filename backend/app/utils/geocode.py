# app/utils/geocode.py
from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, List
import requests
from fastapi import HTTPException


def _score_feature(f: Dict[str, Any]) -> float:
    """
    Score a feature based on match_code hints.
    Priority: address_number > street > postcode > place > region
    """
    props = f.get("properties", {})
    mc: Dict[str, str] = props.get("match_code") or {}

    score = 0.0

    # Strong matches
    if mc.get("address_number") == "matched":
        score += 3.0
    if mc.get("street") == "matched":
        score += 2.0
    if mc.get("postcode") == "matched":
        score += 1.5
    if mc.get("place") == "matched":
        score += 1.0
    if mc.get("region") == "matched":
        score += 0.5

    # Penalize unmatched or weird confidence
    if mc.get("confidence") == "low":
        score -= 1.0
    elif mc.get("confidence") == "medium":
        score -= 0.5

    return score



def _extract_context_parts(props: Dict[str, Any]) -> Dict[str, Optional[str]]:
    ctx = props.get("context") or {}
    parts: Dict[str, Optional[str]] = {"address": None, "postcode": None, "place": None, "region": None}

    # v6 (object/dict) path
    if isinstance(ctx, dict):
        if isinstance(ctx.get("address"), dict):
            parts["address"] = ctx["address"].get("name") or props.get("name") or props.get("full_address")
        if isinstance(ctx.get("postcode"), dict):
            parts["postcode"] = ctx["postcode"].get("name")
        if isinstance(ctx.get("place"), dict):
            parts["place"] = ctx["place"].get("name")
        if isinstance(ctx.get("region"), dict):
            parts["region"] = (
                ctx["region"].get("region_code")
                or ctx["region"].get("name")  # fallback if region_code missing
            )
            
    # Final fallback for address
    if not parts["address"]:
        parts["address"] = props.get("name") or props.get("full_address")

    return parts



def geocode_address(
    address: str,
    mapbox_token: str,
    country: str = "US",
    limit: int = 5,
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Returns (lat, lon, meta) for the best address match using Mapbox Geocoding API v6.
    Selection:
      1) Highest count from properties.match_code (most components matched)
      2) Tiebreak by Mapbox relevance
    meta includes:
      - matched_place_name (feature.place_name fallback or composed)
      - relevance
      - official_parts: {address, city, state, zip}
      - raw_feature
    """
    q = address.strip()
    base = "https://api.mapbox.com/search/geocode/v6/forward"
    params = {
        "access_token": mapbox_token,
        "types": "address",
        "country": country,
        "autocomplete": "false",
        "limit": str(limit),
        "q": q,
    }
    # Some setups prefer putting q in path; v6 supports ?q= as well.
    r = requests.get(base, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    feats: List[Dict[str, Any]] = data.get("features", []) or []
    if not feats:
        raise HTTPException(status_code=422, detail=f"Geocoding returned no results for: {q}")

    # Sort by match_count (desc), then relevance
    feats_sorted = sorted(feats, key=_score_feature)
    top = feats_sorted[0]

    # Coordinates: Mapbox center is [lon, lat]
    coordinates = top.get("geometry", {}).get("coordinates")
    if not coordinates or len(coordinates) < 2:
        raise HTTPException(status_code=422, detail="Geocoding result missing coordinates.")
    lon, lat = coordinates[0], coordinates[1]

    props = top.get("properties", {}) or {}
    ctx_parts = _extract_context_parts(props)
    # Build official parts in the keys you want for DB
    official_parts = {
        "address": ctx_parts.get("address"),
        "city": ctx_parts.get("place"),
        "state": ctx_parts.get("region"),
        "zip": ctx_parts.get("postcode"),
    }

    # Human-friendly line
    place_name = props.get("full_address") or q

    meta: Dict[str, Any] = {
        "matched_place_name": place_name,
        "official_parts": official_parts,
        "match_code": props.get("match_code"),
    }
    return lat, lon, meta
