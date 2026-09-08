"""Row ↔ domain mapping. No SQL driver, no HTTP — Store uses these dicts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from kurpaest.domain import (
    Currency,
    DietaryTag,
    ItemCategory,
    Menu,
    MenuItem,
    MenuLanguage,
    OpenInterval,
    Place,
    PlaceSource,
)


def place_to_row(place: Place) -> dict[str, Any]:
    return {
        "id": place.id,
        "name": place.name,
        "slug": place.slug,
        "lat": place.lat,
        "lng": place.lng,
        "address": place.address,
        "city": place.city,
        "hours": [
            {
                "weekday": interval.weekday,
                "open_minute": interval.open_minute,
                "close_minute": interval.close_minute,
            }
            for interval in place.hours
        ],
        "source": str(place.source),
        "updated_at": place.updated_at,
        "phone": place.phone,
        "website": place.website,
    }


def place_from_row(row: Mapping[str, Any]) -> Place:
    return Place(
        id=_as_uuid(row["id"]),
        name=str(row["name"]),
        slug=str(row["slug"]),
        lat=float(row["lat"]),
        lng=float(row["lng"]),
        address=str(row["address"]),
        city=str(row["city"]),
        hours=_hours_from_row(row["hours"]),
        source=PlaceSource(row["source"]),
        updated_at=_as_datetime(row["updated_at"]),
        phone=_optional_str(row.get("phone")),
        website=_optional_str(row.get("website")),
    )


def menu_to_row(menu: Menu) -> dict[str, Any]:
    return {
        "id": menu.id,
        "place_id": menu.place_id,
        "currency": str(menu.currency),
        "last_verified_at": menu.last_verified_at,
        "language": str(menu.language),
    }


def menu_from_row(row: Mapping[str, Any]) -> Menu:
    return Menu(
        id=_as_uuid(row["id"]),
        place_id=_as_uuid(row["place_id"]),
        currency=Currency(row["currency"]),
        last_verified_at=_as_datetime(row["last_verified_at"]),
        language=MenuLanguage(row["language"]),
    )


def menu_item_to_row(item: MenuItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "place_id": item.place_id,
        "menu_id": item.menu_id,
        "name": item.name,
        "name_en": item.name_en,
        "description": item.description,
        "price_cents": item.price_cents,
        "category": str(item.category),
        "dietary_tags": sorted(str(tag) for tag in item.dietary_tags),
        "search_tokens": list(item.search_tokens),
    }


def menu_item_from_row(row: Mapping[str, Any]) -> MenuItem:
    tags = row.get("dietary_tags") or ()
    tokens = row.get("search_tokens") or ()
    return MenuItem(
        id=_as_uuid(row["id"]),
        place_id=_as_uuid(row["place_id"]),
        menu_id=_as_uuid(row["menu_id"]),
        name=str(row["name"]),
        name_en=_optional_str(row.get("name_en")),
        description=_optional_str(row.get("description")),
        price_cents=int(row["price_cents"]),
        category=ItemCategory(row["category"]),
        dietary_tags=frozenset(DietaryTag(tag) for tag in tags),
        search_tokens=tuple(str(token) for token in tokens),
    )


def _hours_from_row(value: object) -> tuple[OpenInterval, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise TypeError("hours must be a list of intervals")
    return tuple(
        OpenInterval(
            weekday=int(item["weekday"]),
            open_minute=int(item["open_minute"]),
            close_minute=int(item["close_minute"]),
        )
        for item in value
    )


def _as_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _as_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("expected a datetime")
    return value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None
