import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from ..config import settings

def build_filter(city: str, beds_min: int, baths_min: int, max_price: int | None, since_iso: str):
    clauses = [
        "StandardStatus eq 'Active'",
        f"City eq '{city}'",
        f"BedsTotal ge {beds_min}",
        f"BathroomsTotalInteger ge {baths_min}",
        f"ModificationTimestamp ge {since_iso}"
    ]
    if max_price:
        clauses.append(f"ListPrice le {max_price}")
    return " and ".join(clauses)

def poll_reso(city: str, beds_min: int, baths_min: int, max_price: int | None, since_iso: str) -> List[Dict]:
    """
    NOTE: Replace fields to match your MLS metadata if they differ.
    Add $select to trim payload if desired.
    """
    if not settings.RESO_BASE_URL or not settings.RESO_BEARER_TOKEN:
        return []
    q = {
        "$filter": build_filter(city, beds_min, baths_min, max_price, since_iso),
        "$orderby": "ModificationTimestamp desc",
        "$top": "50"
    }
    headers = {"Authorization": f"Bearer {settings.RESO_BEARER_TOKEN}"}
    r = requests.get(settings.RESO_BASE_URL, headers=headers, params=q, timeout=25)
    r.raise_for_status()
    data = r.json()
    # Many OData endpoints return {'value': [ ... ]}
    return data.get("value", [])
