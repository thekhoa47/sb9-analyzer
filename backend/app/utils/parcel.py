from typing import Optional
from app.utils.parcel_fallback_oc import get_oc_parcel_by_point_full

def get_parcel_geojson_with_props(lat: float, lon: float):
    geom, props = get_oc_parcel_by_point_full(lat, lon, 25.0)
    return geom, props, "oc_gis"
    # addresses = get_oc_parcel_by_point_full(lat, lon, 25.0)
    # return addresses
