from typing import Dict, Any, Optional, List
import requests
import json


OC_BUILDINGS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Building_Footprints/FeatureServer/0/query"
OC_PARCELS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0/query"
OC_LOCATIONS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Geocode/OC_Locator/GeocodeServer/findAddressCandidates"


def call_ocgis(url: str, **kwargs) -> requests.Response:
    return requests.get(url, **kwargs)


def _get_location_from_ocgis(address_in: str) -> Optional[Dict[str, Any]]:
    params = {"SingleLine": address_in, "outSR": 2230, "f": "pjson"}

    try:
        response = call_ocgis(OC_LOCATIONS_LAYER, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("candidates"):
            return None

        location = data["candidates"][0]

        lat = float(location["location"]["y"])
        lon = float(location["location"]["x"])
        address = location.get("address")

        return lat, lon, address

    except requests.RequestException as e:
        print(
            f"Cannot find lat/lon for this address. Make sure this is in Orange County: {e}"
        )
        return None


def _get_parcel_geom_from_ocgis(lat: float, lon: float) -> Optional[List[List[float]]]:
    params = {
        "f": "json",
        "geometry": json.dumps(
            {
                "x": lon,
                "y": lat,
                "spatialReference": {"wkid": 2230},
            }
        ),
        "geometryType": "esriGeometryPoint",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": 1.0,
        "units": "esriSRUnit_Foot",
        "returnGeometry": "true",
        "outSR": 2230,
        "outFields": "*",
    }

    try:
        response = call_ocgis(OC_PARCELS_LAYER, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        features = data.get("features") or []

        if not features:
            return None

        return features[0].get("geometry").get("rings")[0]

    except requests.RequestException as e:
        print(f"Error fetching parcel geom from OC GIS: {e}")
        return None


def _get_building_geom_from_ocgis(
    parcel: List[List[float]],
) -> Optional[List[List[float]]]:
    params = {
        "f": "json",
        "geometry": json.dumps(
            {
                "rings": [parcel],
                "spatialReference": {"wkid": 2230},
            }
        ),
        "geometryType": "esriGeometryPolygon",
        "spatialRel": "esriSpatialRelContains",
        "returnGeometry": "true",
        "outFields": "*",
    }

    try:
        response = call_ocgis(OC_BUILDINGS_LAYER, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        features = data.get("features") or []

        if not features:
            return None

        return features[0].get("geometry").get("rings")[0]

    except requests.RequestException as e:
        print(f"Error fetching building geom from OC GIS: {e}")
        return None


def collect_polygon_points(address_in: str) -> dict:
    # 1) Geocode address to lat/lon
    lat, lon, address = _get_location_from_ocgis(address_in)
    parcel = _get_parcel_geom_from_ocgis(lat, lon)
    building = _get_building_geom_from_ocgis(parcel)

    if not parcel and not building:
        return {
            "address": address_in,
            "error": "Address not found or no data available",
        }

    return {
        "address": address,
        "lat": lat,
        "lon": lon,
        "building": building,
        "parcel": parcel,
    }
