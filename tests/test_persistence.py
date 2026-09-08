"""Drive shipped persistence mapping (and Store when PostGIS is available)."""

from __future__ import annotations

import ast
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

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
from kurpaest.persistence import (
    Store,
    apply_migrations,
    connect,
    menu_from_row,
    menu_item_from_row,
    menu_item_to_row,
    menu_to_row,
    place_from_row,
    place_to_row,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "migrations" / "001_init.sql").read_text(encoding="utf-8")
COMPOSE = (ROOT / "compose.yaml").read_text(encoding="utf-8")
DOMAIN_SOURCE = ROOT / "src" / "kurpaest" / "domain.py"

VILNIUS_LAT = 54.6872
VILNIUS_LNG = 25.2798
KEBAB_PRICE_CENTS = 450

ORM_OR_HTTP = frozenset(
    {
        "fastapi",
        "starlette",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "asyncpg",
        "geoalchemy2",
    }
)


def _place() -> Place:
    return Place(
        id=uuid4(),
        name="Kebabinė",
        slug="kebabine",
        lat=VILNIUS_LAT,
        lng=VILNIUS_LNG,
        address="Gedimino pr. 1",
        city="Vilnius",
        hours=(OpenInterval(weekday=0, open_minute=10 * 60, close_minute=22 * 60),),
        source=PlaceSource.SEED,
        updated_at=datetime(2026, 9, 8, tzinfo=UTC),
        phone="+37060000000",
    )


def _menu(place_id) -> Menu:
    return Menu(
        id=uuid4(),
        place_id=place_id,
        currency=Currency.EUR,
        last_verified_at=datetime(2026, 9, 8, tzinfo=UTC),
        language=MenuLanguage.LT,
    )


def _item(place_id, menu_id) -> MenuItem:
    return MenuItem(
        id=uuid4(),
        place_id=place_id,
        menu_id=menu_id,
        name="Kebabas",
        price_cents=KEBAB_PRICE_CENTS,
        category=ItemCategory.KEBAB,
        dietary_tags=frozenset({DietaryTag.HALAL}),
    )


def test_schema_uses_postgis_geography_and_gist() -> None:
    assert "geography(Point, 4326)" in SCHEMA
    assert "USING gist" in SCHEMA
    assert "CREATE EXTENSION IF NOT EXISTS postgis" in SCHEMA


def test_compose_runs_postgis_postgres() -> None:
    assert "postgis/postgis" in COMPOSE
    assert "POSTGRES_DB: kurpaest" in COMPOSE


def test_domain_module_stays_free_of_orm_and_http() -> None:
    tree = ast.parse(DOMAIN_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(ORM_OR_HTTP)


def test_place_row_round_trips_wgs84_coordinates() -> None:
    place = _place()
    loaded = place_from_row(place_to_row(place))
    assert loaded.lat == VILNIUS_LAT
    assert loaded.lng == VILNIUS_LNG
    assert loaded.id == place.id
    assert loaded.hours == place.hours
    assert loaded.source is PlaceSource.SEED


def test_menu_item_row_round_trips_integer_price_cents() -> None:
    item = _item(uuid4(), uuid4())
    loaded = menu_item_from_row(menu_item_to_row(item))
    assert loaded.price_cents == KEBAB_PRICE_CENTS
    assert loaded.price_cents == 450
    assert isinstance(loaded.price_cents, int)
    assert not isinstance(loaded.price_cents, bool)
    assert loaded.dietary_tags == frozenset({DietaryTag.HALAL})


def test_menu_row_round_trip() -> None:
    menu = _menu(uuid4())
    loaded = menu_from_row(menu_to_row(menu))
    assert loaded.currency is Currency.EUR
    assert loaded.place_id == menu.place_id


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_store_save_load_round_trip() -> None:
    place = _place()
    menu = _menu(place.id)
    item = _item(place.id, menu.id)
    with connect() as conn:
        apply_migrations(conn)
        store = Store(conn)
        store.save_place(place)
        store.save_menu(menu)
        store.save_menu_item(item)
        store.commit()
        loaded_place = store.load_place(place.id)
        loaded_item = store.load_menu_item(item.id)
    assert loaded_place is not None
    assert loaded_item is not None
    assert loaded_place.lat == VILNIUS_LAT
    assert loaded_place.lng == VILNIUS_LNG
    assert loaded_item.price_cents == KEBAB_PRICE_CENTS
