from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.db import get_async_session
from app.models import Property
from app.schemas.tasks import PropertyGeoms
from uuid import UUID
from shapely import wkb as shapely_wkb
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
import requests
import json

try:
    # optional: if you pass a GeoAlchemy2 WKBElement
    from geoalchemy2.elements import WKBElement
except Exception:  # pragma: no cover

    class WKBElement:  # type: ignore
        pass


OC_BUILDINGS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Building_Footprints/FeatureServer/0/query"
OC_PARCELS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0/query"
OC_LOCATIONS_LAYER = "https://www.ocgis.com/arcpub/rest/services/Geocode/OC_Locator/GeocodeServer/findAddressCandidates"


def geojson_polygon_to_esri(geom_geojson: dict) -> dict:
    """
    Convert GeoJSON Polygon/MultiPolygon to Esri JSON polygon (rings).
    Assumes GeoJSON coords are [x, y] in the given SR (wkid, default 4326).
    """
    t = geom_geojson.get("type")
    coords = geom_geojson.get("coordinates")
    if not coords or t not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Expected GeoJSON Polygon or MultiPolygon")

    def close_ring(r):
        return r if r and r[0] == r[-1] else (r + [r[0]] if r else r)

    rings = []
    if t == "Polygon":
        for ring in coords:
            pts = [[float(x), float(y)] for x, y in ring]
            rings.append(close_ring(pts))
    else:  # MultiPolygon
        for poly in coords:
            for ring in poly:
                pts = [[float(x), float(y)] for x, y in ring]
                rings.append(close_ring(pts))

    return {"rings": rings, "spatialReference": {"wkid": 2230}}


def ewkb_to_esri_polygon(ewkb):
    # Normalize to bytes
    if isinstance(ewkb, WKBElement):
        wkb_bytes = bytes(ewkb.data)
    elif isinstance(ewkb, str):  # hex
        wkb_bytes = bytes.fromhex(ewkb)
    elif isinstance(ewkb, (bytes, bytearray)):
        wkb_bytes = bytes(ewkb)
    else:
        raise TypeError("ewkb must be hex str, bytes, or WKBElement")

    # Shapely geometry
    g = shapely_wkb.loads(wkb_bytes)
    if g.is_empty:
        return {"rings": [], "spatialReference": {"wkid": 2230}}

    def close_ring(seq):
        pts = [[float(x), float(y)] for x, y in seq]
        if pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        return pts

    def poly_to_rings(p):
        # Esri convention: outer CW, holes CCW
        p = orient(p, sign=-1.0)
        rings = [close_ring(p.exterior.coords)]
        for r in p.interiors:
            rings.append(close_ring(r.coords))
        return rings

    if isinstance(g, Polygon):
        rings = poly_to_rings(g)
    elif isinstance(g, MultiPolygon):
        rings = []
        for p in g.geoms:
            rings.extend(poly_to_rings(p))
    else:
        raise ValueError("Expected Polygon or MultiPolygon geometry")

    return {"rings": rings, "spatialReference": {"wkid": 2230}}


def call_ocgis(url: str, **kwargs) -> requests.Response:
    return requests.get(url, **kwargs)


def _get_location_from_ocgis(
    address_line1: str, address_line2: str | None, city: str, state: str, zip: str
) -> tuple[float, float, str] | None:
    params = {
        "Address": address_line1,
        "Address2": address_line2,
        "City": city,
        "Region": state,
        "Postal": zip,
        "outSR": 2230,
        "f": "pjson",
    }

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


def _get_parcel_geom_from_ocgis(lat: float, lon: float) -> dict | None:
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

        return features[0].get("geometry")

    except requests.RequestException as e:
        print(f"Error fetching parcel geom from OC GIS: {e}")
        return None


def _get_building_geom_from_ocgis(
    parcel: list[list[float]],
) -> dict | None:
    esri_geom = geojson_polygon_to_esri(parcel)
    params = {
        "f": "geojson",
        "geometry": json.dumps(esri_geom),
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

        return features[0].get("geometry")

    except requests.RequestException as e:
        print(f"Error fetching building geom from OC GIS: {e}")
        return None


async def get_property_geoms(
    property_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> PropertyGeoms:
    prop: Property | None = await session.get(Property, property_id)
    if prop is None or prop.address_line1 is None:
        raise ValueError("Property not found or has no address")

    if prop.house_geometry and prop.lot_geometry:
        return PropertyGeoms(
            property_id=property_id, house=prop.house_geometry, parcel=prop.lot_geometry
        )

    lat, lon, address = _get_location_from_ocgis(
        prop.address_line1,
        prop.address_line2,
        prop.city,
        prop.state,
        prop.zip,
    )

    if lat is None or lon is None:
        raise RuntimeError("Cannot find lat & lon for this property from OC GIS")

    parcel = _get_parcel_geom_from_ocgis(lat, lon)
    building = _get_building_geom_from_ocgis(parcel)

    if not parcel or not building:
        raise RuntimeError("Cannot find parcel or building geometry from OC GIS")

    prop.house_geometry = func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(json.dumps(building)), 2230
    )
    prop.lot_geometry = func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(json.dumps(parcel)), 2230
    )
    await session.commit()
    return PropertyGeoms(property_id=property_id, house=building, parcel=parcel)
