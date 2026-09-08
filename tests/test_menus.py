"""Itemized menu queries over domain records — no FastAPI."""

from __future__ import annotations

import ast
from pathlib import Path
from uuid import uuid4

import pytest

from kurpaest.catalog import ITEMS, MENUS, PLACES
from kurpaest.domain import ItemCategory, MenuItem
from kurpaest.menus import menu_for_place, menu_record_for_place, place_by_id

ROOT = Path(__file__).resolve().parents[1]
MENUS_SOURCE = ROOT / "src" / "kurpaest" / "menus.py"
CATALOG_SOURCE = ROOT / "src" / "kurpaest" / "catalog.py"

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


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def _item(**overrides: object) -> MenuItem:
    values: dict[str, object] = {
        "id": uuid4(),
        "place_id": uuid4(),
        "menu_id": uuid4(),
        "name": "Kebabas",
        "price_cents": 450,
        "category": ItemCategory.KEBAB,
    }
    values.update(overrides)
    return MenuItem(**values)  # type: ignore[arg-type]


def test_menu_for_place_returns_that_places_items_in_catalog_order() -> None:
    place_a = uuid4()
    place_b = uuid4()
    first = _item(place_id=place_a, name="Pita")
    other = _item(place_id=place_b, name="Pizza")
    second = _item(place_id=place_a, name="Gira", category=ItemCategory.DRINK)
    found = menu_for_place((first, other, second), place_a)
    assert found == [first, second]


def test_menu_for_place_unknown_id_is_empty() -> None:
    item = _item()
    assert menu_for_place((item,), uuid4()) == []


def test_place_by_id_finds_seed_place() -> None:
    kebab = next(place for place in PLACES if place.slug == "senamiescio-kebabine")
    assert place_by_id(PLACES, kebab.id) is kebab
    assert place_by_id(PLACES, uuid4()) is None


def test_seed_menu_for_place_has_priced_items_and_verification() -> None:
    kebab = next(place for place in PLACES if place.slug == "senamiescio-kebabine")
    menu = menu_record_for_place(MENUS, kebab.id)
    items = menu_for_place(ITEMS, kebab.id)
    assert menu is not None
    assert menu.place_id == kebab.id
    assert str(menu.currency) == "EUR"
    assert menu.last_verified_at.tzinfo is not None
    assert items
    assert all(item.place_id == kebab.id for item in items)
    assert all(isinstance(item.price_cents, int) for item in items)
    assert {item.category for item in items} >= {ItemCategory.KEBAB, ItemCategory.DRINK}


def test_menu_item_without_price_cents_cannot_be_stored() -> None:
    with pytest.raises(TypeError):
        MenuItem(
            id=uuid4(),
            place_id=uuid4(),
            menu_id=uuid4(),
            name="Kebabas",
            price_cents=None,  # type: ignore[arg-type]
            category=ItemCategory.KEBAB,
        )
    with pytest.raises(TypeError):
        _item(price_cents=4.50)


def test_query_modules_do_not_import_http_libraries() -> None:
    for path in (MENUS_SOURCE, CATALOG_SOURCE):
        imported = _imports_of(path)
        assert imported.isdisjoint(HTTP_LIBRARIES), path
