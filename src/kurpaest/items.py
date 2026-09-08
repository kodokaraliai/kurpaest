"""Cheapest-item query over menu rows. No HTTP imports."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from kurpaest.aliases import expand_term, fold_diacritics
from kurpaest.dietary import dietary_tags, item_matches_dietary
from kurpaest.domain import MenuItem, Place, _require_finite_float, _require_wgs84

_EARTH_RADIUS_M = 6_371_000.0
_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


@dataclass(frozen=True)
class MenuItemWithPlace:
    """A matching menu row plus the kitchen that sells it."""

    item: MenuItem
    place: Place
    distance_m: float | None = None


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    chord = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(chord)))


def _matches_term(item: MenuItem, term: str) -> bool:
    needles = expand_term(term)
    if not needles:
        return True
    haystacks = [fold_diacritics(item.name)]
    if item.name_en:
        haystacks.append(fold_diacritics(item.name_en))
    haystacks.extend(fold_diacritics(token) for token in item.search_tokens)
    return any(needle in hay for needle in needles for hay in haystacks)


def parse_near(raw: str) -> tuple[float, float]:
    """Parse `lat,lng` into a validated WGS84 point."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("near must be lat,lng")
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2:
        raise ValueError("near must be lat,lng")
    try:
        lat = _require_finite_float(float(parts[0]), "lat")
        lng = _require_finite_float(float(parts[1]), "lng")
    except (TypeError, ValueError) as exc:
        raise ValueError("near must be lat,lng") from exc
    return _require_wgs84(lat, lng)


def cheapest_items(
    items: Iterable[MenuItem],
    places: Iterable[Place],
    term: str,
    *,
    city: str | None = None,
    near: tuple[float, float] | None = None,
    radius_m: float | None = None,
    dietary: Sequence[object] = (),
    limit: int = _DEFAULT_LIMIT,
) -> list[MenuItemWithPlace]:
    """Matching items cheapest-first, each with its place.

    Geo, when both `near` and `radius_m` are set, keeps rows inside the circle
    and uses distance as the tie-break after `price_cents`.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if limit > _MAX_LIMIT:
        raise ValueError(f"limit must be <= {_MAX_LIMIT}")
    if (near is None) != (radius_m is None):
        raise ValueError("near and radius_m must be provided together")
    if radius_m is not None:
        radius = _require_finite_float(radius_m, "radius_m")
        if radius < 0:
            raise ValueError("radius_m must be >= 0")
    else:
        radius = None

    tags = dietary_tags(dietary)
    city_filter = city.strip() if isinstance(city, str) and city.strip() else None
    by_id = {place.id: place for place in places}

    found: list[MenuItemWithPlace] = []
    for item in items:
        if not _matches_term(item, term):
            continue
        if not item_matches_dietary(item, tags):
            continue
        place = by_id.get(item.place_id)
        if place is None:
            continue
        if city_filter is not None and place.city != city_filter:
            continue
        distance: float | None = None
        if near is not None and radius is not None:
            distance = _haversine_m(near[0], near[1], place.lat, place.lng)
            if distance > radius:
                continue
        found.append(MenuItemWithPlace(item=item, place=place, distance_m=distance))

    found.sort(
        key=lambda row: (
            row.item.price_cents,
            row.distance_m if row.distance_m is not None else 0.0,
        )
    )
    return found[:limit]
