"""Vilnius seed records. JSON in, domain types out. No HTTP, no database."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from uuid import UUID, uuid5

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

SEED_PATH = Path(__file__).resolve().parents[2] / "seed" / "vilnius.json"
_NAMESPACE = UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class Seed:
    places: tuple[Place, ...]
    menus: tuple[Menu, ...]
    items: tuple[MenuItem, ...]


def _place_id(slug: str) -> UUID:
    return uuid5(_NAMESPACE, f"https://kurpaest.lt/places/{slug}")


def _menu_id(slug: str) -> UUID:
    return uuid5(_NAMESPACE, f"https://kurpaest.lt/menus/{slug}")


def _item_id(slug: str, name: str) -> UUID:
    return uuid5(_NAMESPACE, f"https://kurpaest.lt/items/{slug}/{name}")


def _as_datetime(raw: object) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("last_verified_at is required")
    value = datetime.fromisoformat(raw)
    if value.tzinfo is None:
        raise ValueError("last_verified_at must include a timezone")
    return value


def _hours(raw: object) -> tuple[OpenInterval, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise TypeError("hours must be a list of intervals")
    return tuple(
        OpenInterval(
            weekday=int(item["weekday"]),
            open_minute=int(item["open_minute"]),
            close_minute=int(item["close_minute"]),
        )
        for item in raw
    )


def _tags(raw: object) -> frozenset[DietaryTag]:
    if not raw:
        return frozenset()
    if not isinstance(raw, list):
        raise TypeError("dietary_tags must be a list of strings")
    return frozenset(DietaryTag(tag) for tag in raw)


def _tokens(raw: object) -> tuple[str, ...]:
    if not raw:
        return ()
    if not isinstance(raw, list):
        raise TypeError("search_tokens must be a list of strings")
    return tuple(str(token) for token in raw)


def _optional_str(raw: object) -> str | None:
    if raw is None:
        return None
    text = str(raw)
    return text if text else None


def _require_key(row: dict[str, object], key: str, where: str) -> object:
    if key not in row:
        raise ValueError(f"{where}: {key} is required")
    return row[key]


def seed_from_payload(payload: object) -> Seed:
    """Validate contribution JSON and build domain records.

    Coordinates, integer price_cents, and last_verified_at are required.
    Dietary tags are asserted only; names never imply a tag.
    """
    if not isinstance(payload, dict):
        raise TypeError("seed must be a JSON object")
    places_raw = payload.get("places")
    if not isinstance(places_raw, list) or not places_raw:
        raise ValueError("seed must contain a non-empty places list")

    places: list[Place] = []
    menus: list[Menu] = []
    items: list[MenuItem] = []
    seen_slugs: set[tuple[str, str]] = set()
    for row in places_raw:
        if not isinstance(row, dict):
            raise TypeError("each place must be a JSON object")
        slug = str(_require_key(row, "slug", "place"))
        city = str(_require_key(row, "city", f"place {slug}"))
        if (city, slug) in seen_slugs:
            raise ValueError(f"duplicate slug {slug} in {city}")
        seen_slugs.add((city, slug))
        place_id = _place_id(slug)
        menu_row = _require_key(row, "menu", f"place {slug}")
        if not isinstance(menu_row, dict):
            raise TypeError(f"place {slug}: menu must be a JSON object")
        last_verified = _as_datetime(
            _require_key(menu_row, "last_verified_at", f"place {slug} menu")
        )
        place = Place(
            id=place_id,
            name=str(_require_key(row, "name", f"place {slug}")),
            slug=slug,
            lat=_require_key(row, "lat", f"place {slug}"),
            lng=_require_key(row, "lng", f"place {slug}"),
            address=str(_require_key(row, "address", f"place {slug}")),
            city=city,
            hours=_hours(row.get("hours")),
            source=PlaceSource.SEED,
            updated_at=(
                _as_datetime(row["updated_at"])
                if row.get("updated_at")
                else last_verified
            ),
            phone=_optional_str(row.get("phone")),
            website=_optional_str(row.get("website")),
        )
        menu = Menu(
            id=_menu_id(slug),
            place_id=place_id,
            currency=Currency(_require_key(menu_row, "currency", f"place {slug} menu")),
            last_verified_at=last_verified,
            language=MenuLanguage(
                _require_key(menu_row, "language", f"place {slug} menu")
            ),
        )
        item_rows = menu_row.get("items")
        if not isinstance(item_rows, list) or not item_rows:
            raise ValueError(f"place {slug} must have an itemized menu")
        places.append(place)
        menus.append(menu)
        for item_row in item_rows:
            if not isinstance(item_row, dict):
                raise TypeError(f"place {slug}: each item must be a JSON object")
            name = str(_require_key(item_row, "name", f"place {slug} item"))
            items.append(
                MenuItem(
                    id=_item_id(slug, name),
                    place_id=place_id,
                    menu_id=menu.id,
                    name=name,
                    name_en=_optional_str(item_row.get("name_en")),
                    description=_optional_str(item_row.get("description")),
                    price_cents=_require_key(
                        item_row, "price_cents", f"place {slug} item {name}"
                    ),
                    category=ItemCategory(
                        _require_key(item_row, "category", f"place {slug} item {name}")
                    ),
                    dietary_tags=_tags(item_row.get("dietary_tags")),
                    search_tokens=_tokens(item_row.get("search_tokens")),
                )
            )
    return Seed(places=tuple(places), menus=tuple(menus), items=tuple(items))


@lru_cache(maxsize=1)
def load_seed(path: Path | None = None) -> Seed:
    """Load the reviewed Vilnius seed into WP-1 types."""
    source = path or SEED_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))
    return seed_from_payload(payload)


def main() -> None:
    records = load_seed()
    print(
        f"ok: {len(records.places)} places, "
        f"{len(records.menus)} menus, {len(records.items)} items"
    )


if __name__ == "__main__":
    main()
