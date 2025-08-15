import requests

OC_PARCELS_LAYER = "https://ocgis.com/arcpub/rest/services/Map_Layers/Parcels/MapServer/0/query"

def get_oc_parcel_by_point_full(lat: float, lon: float, distance_m: float = 20.0):
    params = {
        "f": "geojson",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "distance": 5.0,
        "units": "esriSRUnit_Meter",
        "returnGeometry": "true",
        "outFields": "*",
        "outSR": 4326,
        "resultRecordCount": 3,
    }
    r = requests.get(OC_PARCELS_LAYER, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features") or []
    if not feats:
        raise RuntimeError("OC GIS: no parcel near this point.")
    f = feats[0]
    return f["geometry"], f.get("properties", {})
    # addresses = []
    # for f in feats:
    #     props = f.get("properties", {})
    #     site_address = f["geometry"], props.get("SITE_ADDRESS") or props.get("SITUSADDR") or ""
    #     addresses.append(site_address)
    # return addresses
