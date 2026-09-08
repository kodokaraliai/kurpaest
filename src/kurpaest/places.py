"""Viewport queries over Place records. No HTTP imports."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from kurpaest.domain import MenuItem, Place, _require_finite_float, _require_wgs84


def bounds(
    south: object,
    west: object,
    north: object,
    east: object,
) -> tuple[float, float, float, float]:
    """Validate a WGS84 bounding box. Inclusive edges; no antimeridian wrap."""
    south_lat, west_lng = _require_wgs84(south, west)
    north_lat, east_lng = _require_wgs84(north, east)
    if south_lat > north_lat:
        raise ValueError("south must be <= north")
    if west_lng > east_lng:
        raise ValueError("west must be <= east")
    return south_lat, west_lng, north_lat, east_lng


def places_in_bounds(
    places: Iterable[Place],
    south: object,
    west: object,
    north: object,
    east: object,
    city: str | None = None,
) -> list[Place]:
    """Places whose coordinates fall in the viewport, optionally in one city."""
    south_lat, west_lng, north_lat, east_lng = bounds(south, west, north, east)
    city_filter = city.strip() if isinstance(city, str) and city.strip() else None
    found: list[Place] = []
    for place in places:
        if not (south_lat <= place.lat <= north_lat):
            continue
        if not (west_lng <= place.lng <= east_lng):
            continue
        if city_filter is not None and place.city != city_filter:
            continue
        found.append(place)
    return found


def places_for_items(
    matching_items: Iterable[MenuItem],
    places: Iterable[Place],
) -> list[Place]:
    """Pins for an item query: unique owning places, in catalog order."""
    wanted = {item.place_id for item in matching_items}
    seen: set[UUID] = set()
    found: list[Place] = []
    for place in places:
        if place.id not in wanted or place.id in seen:
            continue
        seen.add(place.id)
        found.append(place)
    return found


def parse_bbox(raw: str) -> tuple[float, float, float, float]:
    """Parse `s,w,n,e` into a validated bounding box."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("bbox is required (s,w,n,e)")
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be four comma-separated numbers (s,w,n,e)")
    try:
        south = _require_finite_float(float(parts[0]), "south")
        west = _require_finite_float(float(parts[1]), "west")
        north = _require_finite_float(float(parts[2]), "north")
        east = _require_finite_float(float(parts[3]), "east")
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox must be four comma-separated numbers (s,w,n,e)") from exc
    return bounds(south, west, north, east)
