"""Viewport queries over domain Place records — no FastAPI."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from kurpaest.catalog import MOCK_PLACES
from kurpaest.domain import (
    ItemCategory,
    MenuItem,
    Place,
    PlaceSource,
)
from kurpaest.places import parse_bbox, places_for_items, places_in_bounds

ROOT = Path(__file__).resolve().parents[1]
PLACES_SOURCE = ROOT / "src" / "kurpaest" / "places.py"
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

VILNIUS_LAT = 54.6872
VILNIUS_LNG = 25.2798
# Typical zoom-13 box around the old town; excludes Kaunas.
VILNIUS_BOX = (54.66, 25.22, 54.71, 25.34)


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


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_places_in_bounds_keeps_only_viewport_hits() -> None:
    inside = _place(name="Inside")
    north = _place(name="North", lat=55.5, lng=VILNIUS_LNG)
    east = _place(name="East", lat=VILNIUS_LAT, lng=26.5)
    south, west, north_b, east_b = VILNIUS_BOX
    found = places_in_bounds((inside, north, east), south, west, north_b, east_b)
    assert [place.name for place in found] == ["Inside"]


def test_places_in_bounds_includes_edges() -> None:
    south, west, north, east = VILNIUS_BOX
    on_sw = _place(lat=south, lng=west)
    on_ne = _place(lat=north, lng=east)
    found = places_in_bounds((on_sw, on_ne), south, west, north, east)
    assert found == [on_sw, on_ne]


def test_places_in_bounds_optional_city_filter() -> None:
    vilnius = _place(city="Vilnius")
    kaunas = _place(name="Kaunas", city="Kaunas", lat=54.90, lng=23.89)
    south, west, north, east = 54.0, 23.0, 56.0, 26.0
    both = places_in_bounds((vilnius, kaunas), south, west, north, east)
    only_vilnius = places_in_bounds(
        (vilnius, kaunas), south, west, north, east, city="Vilnius"
    )
    assert {place.city for place in both} == {"Vilnius", "Kaunas"}
    assert [place.city for place in only_vilnius] == ["Vilnius"]


def test_places_in_bounds_rejects_inverted_box() -> None:
    with pytest.raises(ValueError, match="south"):
        places_in_bounds((), 55.0, 25.0, 54.0, 26.0)
    with pytest.raises(ValueError, match="west"):
        places_in_bounds((), 54.0, 26.0, 55.0, 25.0)


def test_place_without_coordinates_cannot_enter_the_map() -> None:
    with pytest.raises(ValueError):
        _place(lat=None, lng=None)


def test_parse_bbox_reads_s_w_n_e() -> None:
    assert parse_bbox("54.66,25.22,54.71,25.34") == VILNIUS_BOX
    assert parse_bbox(" 54.66 , 25.22 , 54.71 , 25.34 ") == VILNIUS_BOX


def test_parse_bbox_rejects_malformed() -> None:
    with pytest.raises(ValueError):
        parse_bbox("")
    with pytest.raises(ValueError):
        parse_bbox("54.66,25.22,54.71")
    with pytest.raises(ValueError):
        parse_bbox("south,west,north,east")
    with pytest.raises(ValueError):
        parse_bbox("54.71,25.22,54.66,25.34")


def test_mock_catalog_vilnius_viewport_excludes_kaunas() -> None:
    south, west, north, east = VILNIUS_BOX
    found = places_in_bounds(MOCK_PLACES, south, west, north, east)
    cities = {place.city for place in found}
    slugs = {place.slug for place in found}
    assert cities == {"Vilnius"}
    assert "kauno-kebabas" not in slugs
    assert "senamiescio-kebabine" in slugs
    assert all(place.lat is not None and place.lng is not None for place in found)


def test_places_for_items_returns_unique_owning_places() -> None:
    first, second, _third, kaunas = MOCK_PLACES
    item_a = MenuItem(
        id=uuid4(),
        place_id=first.id,
        menu_id=uuid4(),
        name="Kebabas",
        price_cents=450,
        category=ItemCategory.KEBAB,
    )
    item_b = MenuItem(
        id=uuid4(),
        place_id=first.id,
        menu_id=uuid4(),
        name="Šaurma",
        price_cents=500,
        category=ItemCategory.KEBAB,
    )
    item_c = MenuItem(
        id=uuid4(),
        place_id=kaunas.id,
        menu_id=uuid4(),
        name="Kebabas",
        price_cents=399,
        category=ItemCategory.KEBAB,
    )
    found = places_for_items((item_a, item_b, item_c), MOCK_PLACES)
    assert [place.slug for place in found] == [first.slug, kaunas.slug]
    assert second not in found


def test_query_modules_do_not_import_http_libraries() -> None:
    for path in (PLACES_SOURCE, CATALOG_SOURCE):
        imported = _imports_of(path)
        assert imported.isdisjoint(HTTP_LIBRARIES), path
