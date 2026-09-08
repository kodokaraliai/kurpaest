"""Conjunctive dietary filters over domain records — no FastAPI."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from kurpaest.catalog import ITEMS, PLACES
from kurpaest.dietary import (
    dietary_tags,
    item_matches_dietary,
    items_matching_dietary,
    places_with_dietary,
)
from kurpaest.domain import DietaryTag, ItemCategory, MenuItem, Place, PlaceSource
from kurpaest.items import cheapest_items
from kurpaest.places import places_in_bounds

ROOT = Path(__file__).resolve().parents[1]
DIETARY_SOURCE = ROOT / "src" / "kurpaest" / "dietary.py"

HTTP_LIBRARIES = frozenset(
    {
        "fastapi",
        "starlette",
        "flask",
        "django",
        "httpx",
        "aiohttp",
        "uvicorn",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "asyncpg",
        "geoalchemy2",
    }
)

VILNIUS_BOX = (54.66, 25.22, 54.71, 25.34)


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def _place(**overrides: object) -> Place:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Virtuvė",
        "slug": "virtuve",
        "lat": 54.6872,
        "lng": 25.2798,
        "address": "Gedimino pr. 1",
        "city": "Vilnius",
        "hours": (),
        "source": PlaceSource.SEED,
        "updated_at": datetime(2026, 9, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return Place(**values)  # type: ignore[arg-type]


def _item(**overrides: object) -> MenuItem:
    values: dict[str, object] = {
        "id": uuid4(),
        "place_id": uuid4(),
        "menu_id": uuid4(),
        "name": "Patiekalas",
        "price_cents": 500,
        "category": ItemCategory.MAIN,
    }
    values.update(overrides)
    return MenuItem(**values)  # type: ignore[arg-type]


def test_unknown_item_tags_do_not_match_a_filter() -> None:
    unknown = _item(dietary_tags=frozenset())
    vegan = _item(dietary_tags=frozenset({DietaryTag.VEGAN}))
    required = dietary_tags((DietaryTag.VEGAN,))
    assert not item_matches_dietary(unknown, required)
    assert item_matches_dietary(vegan, required)
    assert item_matches_dietary(unknown, frozenset())


def test_name_does_not_infer_tags() -> None:
    named = _item(name="Veganiška sriuba", dietary_tags=frozenset())
    required = dietary_tags(("vegan",))
    assert not item_matches_dietary(named, required)
    assert items_matching_dietary((named,), ("vegan",)) == []


def test_conjunctive_filter_requires_every_tag() -> None:
    both = _item(
        dietary_tags=frozenset({DietaryTag.VEGAN, DietaryTag.GLUTEN_FREE}),
    )
    vegan_only = _item(dietary_tags=frozenset({DietaryTag.VEGAN}))
    required = dietary_tags(("vegan", "gluten_free"))
    found = items_matching_dietary((both, vegan_only), required)
    assert found == [both]


def test_mixed_menu_drops_untagged_from_vegan_query() -> None:
    pizza = next(place for place in PLACES if place.slug == "naujamiescio-picerija")
    pizza_items = [item for item in ITEMS if item.place_id == pizza.id]
    vegan = items_matching_dietary(pizza_items, ("vegan",))
    names = {item.name for item in vegan}
    assert "Veganiška margarita" in names
    assert "Diavola" not in names
    assert "Dienos sriuba" not in names
    assert all(DietaryTag.VEGAN in item.dietary_tags for item in vegan)

    found = cheapest_items(ITEMS, PLACES, "pizza", dietary=("vegan",))
    assert found
    assert all(DietaryTag.VEGAN in row.item.dietary_tags for row in found)
    assert all(row.item.name != "Diavola" for row in found)


def test_places_with_dietary_need_at_least_one_matching_item() -> None:
    vegan_place = _place(name="Vegan", slug="vegan")
    mixed = _place(name="Mixed", slug="mixed")
    meat = _place(name="Meat", slug="meat")
    items = (
        _item(
            place_id=vegan_place.id,
            dietary_tags=frozenset({DietaryTag.VEGAN}),
        ),
        _item(place_id=mixed.id, dietary_tags=frozenset()),
        _item(
            place_id=mixed.id,
            dietary_tags=frozenset({DietaryTag.VEGAN}),
            name="Tagged",
        ),
        _item(place_id=meat.id, dietary_tags=frozenset()),
    )
    found = places_with_dietary(
        (vegan_place, mixed, meat),
        items,
        ("vegan",),
    )
    assert [place.slug for place in found] == ["vegan", "mixed"]


def test_seed_map_dietary_keeps_places_with_verified_vegan_items() -> None:
    south, west, north, east = VILNIUS_BOX
    in_view = places_in_bounds(PLACES, south, west, north, east)
    vegan_places = places_with_dietary(in_view, ITEMS, ("vegan",))
    slugs = {place.slug for place in vegan_places}
    assert "saknys" in slugs
    assert "naujamiescio-picerija" in slugs
    assert "senamiescio-kebabine" not in slugs


def test_unknown_tag_name_is_rejected() -> None:
    with pytest.raises(ValueError):
        dietary_tags(("keto",))


def test_dietary_module_does_not_import_http_libraries() -> None:
    imported = _imports_of(DIETARY_SOURCE)
    assert imported.isdisjoint(HTTP_LIBRARIES)
