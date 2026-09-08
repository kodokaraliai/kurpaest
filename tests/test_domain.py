"""Drive the shipped domain constructors — no test-local copies of validation."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from kurpaest.domain import (
    AliasRecord,
    Currency,
    DietaryTag,
    ItemCategory,
    Menu,
    MenuItem,
    MenuLanguage,
    Place,
    PlaceSource,
)

DOMAIN_SOURCE = Path(__file__).resolve().parents[1] / "src" / "kurpaest" / "domain.py"
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

VILNIUS_LAT = 54.6872
VILNIUS_LNG = 25.2798
KEBAB_PRICE_CENTS = 450


def _place(**overrides: object) -> Place:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Kebabinė",
        "slug": "kebabine",
        "lat": VILNIUS_LAT,
        "lng": VILNIUS_LNG,
        "address": "Gedimino pr. 1",
        "city": "Vilnius",
        "hours": (),
        "source": PlaceSource.SEED,
        "updated_at": datetime(2026, 9, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return Place(**values)  # type: ignore[arg-type]


def _menu(**overrides: object) -> Menu:
    values: dict[str, object] = {
        "id": uuid4(),
        "place_id": uuid4(),
        "currency": Currency.EUR,
        "last_verified_at": datetime(2026, 9, 8, tzinfo=UTC),
        "language": MenuLanguage.LT,
    }
    values.update(overrides)
    return Menu(**values)  # type: ignore[arg-type]


def _item(**overrides: object) -> MenuItem:
    values: dict[str, object] = {
        "id": uuid4(),
        "place_id": uuid4(),
        "menu_id": uuid4(),
        "name": "Kebabas",
        "price_cents": KEBAB_PRICE_CENTS,
        "category": ItemCategory.KEBAB,
    }
    values.update(overrides)
    return MenuItem(**values)  # type: ignore[arg-type]


def test_place_construction_keeps_wgs84_coordinates() -> None:
    place = _place()
    assert place.lat == VILNIUS_LAT
    assert place.lng == VILNIUS_LNG
    assert place.source is PlaceSource.SEED


def test_place_without_coordinates_is_rejected() -> None:
    with pytest.raises(ValueError):
        _place(lat=None, lng=None)
    with pytest.raises(ValueError):
        _place(lat=None, lng=VILNIUS_LNG)
    with pytest.raises(ValueError):
        _place(lat=VILNIUS_LAT, lng=None)


def test_menu_construction() -> None:
    place_id = uuid4()
    menu = _menu(place_id=place_id, currency="EUR", language="lt")
    assert menu.place_id == place_id
    assert menu.currency is Currency.EUR
    assert menu.language is MenuLanguage.LT


def test_menu_item_construction_keeps_integer_price() -> None:
    item = _item()
    assert item.price_cents == KEBAB_PRICE_CENTS
    assert item.price_cents == 450
    assert isinstance(item.price_cents, int)
    assert not isinstance(item.price_cents, bool)


def test_menu_item_rejects_non_integer_price_cents() -> None:
    with pytest.raises(TypeError):
        _item(price_cents=4.50)
    with pytest.raises(TypeError):
        _item(price_cents="450")
    with pytest.raises(TypeError):
        _item(price_cents=True)


def test_dietary_tag_closed_vocabulary() -> None:
    assert DietaryTag("vegan") is DietaryTag.VEGAN
    assert DietaryTag("gluten_free") is DietaryTag.GLUTEN_FREE
    with pytest.raises(ValueError):
        DietaryTag("keto")


def test_menu_item_rejects_tag_outside_closed_vocabulary() -> None:
    with pytest.raises(ValueError):
        _item(dietary_tags=frozenset({"keto"}))


def test_empty_dietary_tags_are_accepted_as_unknown() -> None:
    item = _item(dietary_tags=frozenset())
    assert item.dietary_tags == frozenset()
    tagged = _item(dietary_tags=frozenset({DietaryTag.VEGAN, "gluten_free"}))
    assert tagged.dietary_tags == frozenset({DietaryTag.VEGAN, DietaryTag.GLUTEN_FREE})


def test_alias_record_construction() -> None:
    alias = AliasRecord(
        term="kebab",
        expansions=("kebab", "kebabas", "doner", "döner"),
    )
    assert alias.term == "kebab"
    assert "kebabas" in alias.expansions


def test_domain_module_does_not_import_http_libraries() -> None:
    tree = ast.parse(DOMAIN_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(HTTP_LIBRARIES)
    assert imported <= {
        "__future__",
        "math",
        "dataclasses",
        "datetime",
        "enum",
        "uuid",
    }
