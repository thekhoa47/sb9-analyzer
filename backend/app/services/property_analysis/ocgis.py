from __future__ import annotations

import requests
import json

from shapely.geometry import shape, Polygon
from .geometry_ops import ewkb_or_shapely_to_esri

import matplotlib

matplotlib.use("Agg")


try:
    from geoalchemy2.elements import WKBElement
except Exception:  # pragma: no cover

    class WKBElement:  # type: ignore
        pass


OC_BUILDINGS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Building_Footprints/FeatureServer/0/query"
OC_PARCELS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0/query"
OC_LOCATIONS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Geocode/OC_Locator/GeocodeServer/findAddressCandidates"


def call_ocgis(url: str, **kwargs) -> requests.Response:
    return requests.get(url, **kwargs)


def get_location_from_ocgis(address_in: str) -> dict | None:
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


def get_parcel_polygon_from_ocgis(lat: float, lon: float) -> Polygon | None:
    params = {
        "f": "geojson",
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

        return shape(features[0].get("geometry"))

    except requests.RequestException as e:
        print(f"Error fetching parcel geom from OC GIS: {e}")
        return None


def get_building_polygon_from_ocgis(
    parcel: Polygon,
) -> Polygon | None:
    esri_geom = ewkb_or_shapely_to_esri(parcel)
    params = {
        "f": "geojson",
        "geometry": json.dumps(esri_geom),
        "geometryType": "esriGeometryPolygon",
        "spatialRel": "esriSpatialRelContains",
        "units": "esriSRUnit_Foot",
        "returnGeometry": "true",
        "outSR": 2230,
        "outFields": "*",
    }

    try:
        response = call_ocgis(OC_BUILDINGS_LAYER, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        features = data.get("features") or []

        if not features:
            return None

        return shape(features[0].get("geometry"))

    except requests.RequestException as e:
        print(f"Error fetching building geom from OC GIS: {e}")
        return None
