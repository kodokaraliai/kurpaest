"""Cheapest-item query over domain records — no FastAPI."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from kurpaest.catalog import ITEMS, PLACES
from kurpaest.domain import DietaryTag, ItemCategory, MenuItem, Place, PlaceSource
from kurpaest.items import cheapest_items, parse_near

ROOT = Path(__file__).resolve().parents[1]
ITEMS_SOURCE = ROOT / "src" / "kurpaest" / "items.py"

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


def _item(**overrides: object) -> MenuItem:
    values: dict[str, object] = {
        "id": uuid4(),
        "place_id": uuid4(),
        "menu_id": uuid4(),
        "name": "Kebabas",
        "price_cents": 450,
        "category": ItemCategory.KEBAB,
        "search_tokens": ("kebab", "kebabas"),
    }
    values.update(overrides)
    return MenuItem(**values)  # type: ignore[arg-type]


def test_cheapest_items_sorts_by_price_and_attaches_place() -> None:
    cheap_place = _place(name="Pigiau", slug="pigiau")
    dear_place = _place(name="Brangiau", slug="brangiau", lat=54.69, lng=25.28)
    cheap = _item(place_id=cheap_place.id, name="Kebabas", price_cents=400)
    dear = _item(place_id=dear_place.id, name="Kebabas pita", price_cents=700)
    soup = _item(
        place_id=cheap_place.id,
        name="Sriuba",
        price_cents=100,
        category=ItemCategory.SOUP,
        search_tokens=("sriuba",),
    )
    found = cheapest_items((cheap, dear, soup), (cheap_place, dear_place), "kebab")
    assert [row.item.price_cents for row in found] == [400, 700]
    assert found[0].place is cheap_place
    assert found[1].place is dear_place
    assert found[0].place.lat == cheap_place.lat
    assert found[0].place.lng == cheap_place.lng


def test_cheapest_items_matches_name_or_search_tokens() -> None:
    place = _place()
    by_name = _item(
        place_id=place.id,
        name="Kebabas lėkštėje",
        search_tokens=(),
        price_cents=500,
    )
    by_token = _item(
        place_id=place.id,
        name="Lėkštė",
        search_tokens=("kebab",),
        price_cents=600,
    )
    miss = _item(
        place_id=place.id,
        name="Pica",
        search_tokens=("pizza",),
        price_cents=100,
        category=ItemCategory.PIZZA,
    )
    found = cheapest_items((by_name, by_token, miss), (place,), "kebab")
    assert [row.item.name for row in found] == ["Kebabas lėkštėje", "Lėkštė"]


def test_cheapest_items_city_filter() -> None:
    vilnius = _place(city="Vilnius")
    kaunas = _place(name="Kaunas", slug="kaunas", city="Kaunas", lat=54.90, lng=23.89)
    cheap_kaunas = _item(place_id=kaunas.id, price_cents=300)
    vilnius_item = _item(place_id=vilnius.id, price_cents=400)
    found = cheapest_items(
        (cheap_kaunas, vilnius_item),
        (vilnius, kaunas),
        "kebab",
        city="Vilnius",
    )
    assert [row.place.city for row in found] == ["Vilnius"]


def test_cheapest_items_geo_keeps_circle_and_tie_breaks_by_distance() -> None:
    near_place = _place(name="Near", slug="near", lat=54.6872, lng=25.2798)
    far_place = _place(name="Far", slug="far", lat=54.7335, lng=25.2418)
    same_price_near = _item(place_id=near_place.id, price_cents=500)
    same_price_far = _item(place_id=far_place.id, price_cents=500)
    found = cheapest_items(
        (same_price_far, same_price_near),
        (near_place, far_place),
        "kebab",
        near=(54.6872, 25.2798),
        radius_m=2000,
    )
    assert [row.place.slug for row in found] == ["near"]
    assert found[0].distance_m is not None
    assert found[0].distance_m < 2000

    both = cheapest_items(
        (same_price_far, same_price_near),
        (near_place, far_place),
        "kebab",
        near=(54.6872, 25.2798),
        radius_m=10_000,
    )
    assert [row.place.slug for row in both] == ["near", "far"]
    assert both[0].distance_m is not None
    assert both[1].distance_m is not None
    assert both[0].distance_m < both[1].distance_m


def test_cheapest_items_empty_dietary_unknown_does_not_match() -> None:
    place = _place()
    unknown = _item(place_id=place.id, dietary_tags=frozenset(), price_cents=100)
    vegan = _item(
        place_id=place.id,
        dietary_tags=frozenset({DietaryTag.VEGAN}),
        price_cents=200,
        name="Falafelis",
        search_tokens=("falafel", "kebab"),
    )
    found = cheapest_items(
        (unknown, vegan),
        (place,),
        "kebab",
        dietary=(DietaryTag.VEGAN,),
    )
    assert [row.item.name for row in found] == ["Falafelis"]


def test_cheapest_items_rejects_split_geo() -> None:
    with pytest.raises(ValueError, match="near and radius_m"):
        cheapest_items((), (), "kebab", near=(VILNIUS_LAT, VILNIUS_LNG))
    with pytest.raises(ValueError, match="near and radius_m"):
        cheapest_items((), (), "kebab", radius_m=1000)


def test_parse_near_reads_lat_lng() -> None:
    assert parse_near("54.68,25.27") == pytest.approx((54.68, 25.27))
    with pytest.raises(ValueError):
        parse_near("54.68")
    with pytest.raises(ValueError):
        parse_near("north,east")


def test_seed_kebab_cheapest_is_canteen() -> None:
    found = cheapest_items(ITEMS, PLACES, "kebab")
    assert found
    assert found[0].item.name == "Kebabas"
    assert found[0].item.price_cents == 499
    assert found[0].place.slug == "fabijoniskiu-valgykla"
    prices = [row.item.price_cents for row in found]
    assert prices == sorted(prices)
    assert all(row.place.lat is not None and row.place.lng is not None for row in found)


def test_items_module_does_not_import_http_libraries() -> None:
    imported = _imports_of(ITEMS_SOURCE)
    assert imported.isdisjoint(HTTP_LIBRARIES)
