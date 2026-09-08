"""Domain records for kurpaest.lt.

Construction and write-time invariants only. This module must not import
FastAPI or any other HTTP library; persistence and routes adapt these types.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

_LAT_MIN, _LAT_MAX = -90.0, 90.0
_LNG_MIN, _LNG_MAX = -180.0, 180.0


class DietaryTag(StrEnum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    LACTOSE_FREE = "lactose_free"
    NUT_FREE = "nut_free"
    HALAL = "halal"
    PESCETARIAN = "pescatarian"


class PlaceSource(StrEnum):
    SEED = "seed"
    MANUAL = "manual"
    PARTNER = "partner"


class Currency(StrEnum):
    EUR = "EUR"


class MenuLanguage(StrEnum):
    LT = "lt"
    EN = "en"


class ItemCategory(StrEnum):
    KEBAB = "kebab"
    PIZZA = "pizza"
    SOUP = "soup"
    MAIN = "main"
    DESSERT = "dessert"
    DRINK = "drink"
    OTHER = "other"


def _require_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def _require_finite_float(value: object, name: str) -> float:
    if value is None:
        raise ValueError(f"{name} is required")
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{name} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite WGS84 coordinate")
    return number


def _require_wgs84(lat: object, lng: object) -> tuple[float, float]:
    if lat is None or lng is None:
        raise ValueError("place coordinates (lat, lng) are required")
    latitude = _require_finite_float(lat, "lat")
    longitude = _require_finite_float(lng, "lng")
    if not _LAT_MIN <= latitude <= _LAT_MAX:
        raise ValueError(f"lat must be within [{_LAT_MIN}, {_LAT_MAX}]")
    if not _LNG_MIN <= longitude <= _LNG_MAX:
        raise ValueError(f"lng must be within [{_LNG_MIN}, {_LNG_MAX}]")
    return latitude, longitude


def _require_non_empty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def _require_uuid(value: object, name: str) -> UUID:
    if not isinstance(value, UUID):
        raise TypeError(f"{name} must be a UUID")
    return value


def _require_datetime(value: object, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime")
    return value


@dataclass(frozen=True)
class OpenInterval:
    """One weekly opening interval. weekday 0 = Monday, 6 = Sunday."""

    weekday: int
    open_minute: int
    close_minute: int

    def __post_init__(self) -> None:
        weekday = _require_int(self.weekday, "weekday")
        open_minute = _require_int(self.open_minute, "open_minute")
        close_minute = _require_int(self.close_minute, "close_minute")
        if not 0 <= weekday <= 6:
            raise ValueError("weekday must be in 0..6 (Monday..Sunday)")
        if not 0 <= open_minute <= 24 * 60:
            raise ValueError("open_minute must be in 0..1440")
        if not 0 <= close_minute <= 24 * 60:
            raise ValueError("close_minute must be in 0..1440")
        object.__setattr__(self, "weekday", weekday)
        object.__setattr__(self, "open_minute", open_minute)
        object.__setattr__(self, "close_minute", close_minute)


@dataclass(frozen=True)
class Place:
    id: UUID
    name: str
    slug: str
    lat: float
    lng: float
    address: str
    city: str
    hours: tuple[OpenInterval, ...]
    source: PlaceSource
    updated_at: datetime
    phone: str | None = None
    website: str | None = None

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_non_empty(self.name, "name")
        _require_non_empty(self.slug, "slug")
        _require_non_empty(self.address, "address")
        _require_non_empty(self.city, "city")
        _require_datetime(self.updated_at, "updated_at")
        lat, lng = _require_wgs84(self.lat, self.lng)
        object.__setattr__(self, "lat", lat)
        object.__setattr__(self, "lng", lng)
        if not isinstance(self.hours, tuple) or any(
            not isinstance(interval, OpenInterval) for interval in self.hours
        ):
            raise TypeError("hours must be a tuple of OpenInterval")
        object.__setattr__(self, "source", PlaceSource(self.source))


@dataclass(frozen=True)
class Menu:
    id: UUID
    place_id: UUID
    currency: Currency
    last_verified_at: datetime
    language: MenuLanguage

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.place_id, "place_id")
        _require_datetime(self.last_verified_at, "last_verified_at")
        object.__setattr__(self, "currency", Currency(self.currency))
        object.__setattr__(self, "language", MenuLanguage(self.language))


@dataclass(frozen=True)
class MenuItem:
    id: UUID
    place_id: UUID
    menu_id: UUID
    name: str
    price_cents: int
    category: ItemCategory
    name_en: str | None = None
    description: str | None = None
    dietary_tags: frozenset[DietaryTag] = field(default_factory=frozenset)
    search_tokens: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_uuid(self.id, "id")
        _require_uuid(self.place_id, "place_id")
        _require_uuid(self.menu_id, "menu_id")
        _require_non_empty(self.name, "name")
        price = _require_int(self.price_cents, "price_cents")
        if price < 0:
            raise ValueError("price_cents must be >= 0")
        object.__setattr__(self, "price_cents", price)
        object.__setattr__(self, "category", ItemCategory(self.category))
        tags = frozenset(DietaryTag(tag) for tag in self.dietary_tags)
        object.__setattr__(self, "dietary_tags", tags)
        if not isinstance(self.search_tokens, tuple):
            raise TypeError("search_tokens must be a tuple of strings")


@dataclass(frozen=True)
class AliasRecord:
    """Query term and the item tokens it expands to. Expansion logic is WP-7."""

    term: str
    expansions: tuple[str, ...]

    def __post_init__(self) -> None:
        term = _require_non_empty(self.term, "term")
        object.__setattr__(self, "term", term)
        if not isinstance(self.expansions, tuple) or not self.expansions:
            raise ValueError("expansions must be a non-empty tuple of strings")
        if any(
            not isinstance(token, str) or not token.strip() for token in self.expansions
        ):
            raise ValueError("each alias expansion must be a non-empty string")
