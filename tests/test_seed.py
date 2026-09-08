"""Vilnius seed is reviewed domain records, loadable through Store."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

from kurpaest.domain import Currency, DietaryTag, ItemCategory
from kurpaest.seed import SEED_PATH, load_seed

ROOT = Path(__file__).resolve().parents[1]
SEED_SOURCE = ROOT / "src" / "kurpaest" / "seed.py"

HTTP_OR_DB = frozenset(
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

KEBAB_TOKENS = frozenset({"kebab", "kebabas", "doner", "döner", "shawarma", "šaurma"})


def _kebab_items(items):
    found = []
    for item in items:
        tokens = {token.lower() for token in item.search_tokens}
        if tokens & {token.lower() for token in KEBAB_TOKENS}:
            found.append(item)
    return found


def test_seed_file_is_in_the_repo() -> None:
    assert SEED_PATH.is_file()
    assert SEED_PATH.name == "vilnius.json"


def test_seed_loads_vilnius_places_with_itemized_menus() -> None:
    seed = load_seed()
    slugs = {place.slug for place in seed.places}
    assert slugs == {
        "senamiescio-kebabine",
        "saknys",
        "naujamiescio-picerija",
        "fabijoniskiu-valgykla",
    }
    assert all(place.city == "Vilnius" for place in seed.places)
    assert all(place.lat is not None and place.lng is not None for place in seed.places)
    assert len(seed.menus) == len(seed.places)
    assert seed.items
    assert {item.place_id for item in seed.items} == {place.id for place in seed.places}


def test_every_item_has_integer_price_cents_and_eur_menus() -> None:
    seed = load_seed()
    assert all(menu.currency is Currency.EUR for menu in seed.menus)
    assert all(menu.last_verified_at.tzinfo is not None for menu in seed.menus)
    for item in seed.items:
        assert isinstance(item.price_cents, int)
        assert not isinstance(item.price_cents, bool)
        assert item.price_cents >= 0


def test_seed_has_kebab_place_and_cheapest_kebab_is_priced() -> None:
    seed = load_seed()
    kebabs = _kebab_items(seed.items)
    assert kebabs
    kebab_place = next(
        place for place in seed.places if place.slug == "senamiescio-kebabine"
    )
    assert any(item.place_id == kebab_place.id for item in kebabs)
    cheapest = min(kebabs, key=lambda item: item.price_cents)
    assert cheapest.price_cents == 499
    assert cheapest.name == "Kebabas"
    canteen = next(
        place for place in seed.places if place.slug == "fabijoniskiu-valgykla"
    )
    assert cheapest.place_id == canteen.id


def test_seed_has_explicit_vegan_menu_and_unknown_does_not_match() -> None:
    seed = load_seed()
    vegan = [item for item in seed.items if DietaryTag.VEGAN in item.dietary_tags]
    vegetarian_only = [
        item
        for item in seed.items
        if DietaryTag.VEGETARIAN in item.dietary_tags
        and DietaryTag.VEGAN not in item.dietary_tags
    ]
    unknown = [item for item in seed.items if not item.dietary_tags]
    saknys = next(place for place in seed.places if place.slug == "saknys")
    pizza = next(
        place for place in seed.places if place.slug == "naujamiescio-picerija"
    )
    assert vegan
    assert all(DietaryTag.VEGETARIAN in item.dietary_tags for item in vegan)
    assert any(item.place_id == saknys.id for item in vegan)
    assert vegetarian_only
    assert unknown
    assert any(
        item.place_id == pizza.id and not item.dietary_tags for item in seed.items
    )
    assert all(DietaryTag.VEGAN not in item.dietary_tags for item in unknown)
    # A vegan chip is conjunctive: unknown items drop out.
    vegan_ids = {item.id for item in vegan}
    assert {item.id for item in unknown}.isdisjoint(vegan_ids)


def test_seed_mixed_menu_has_partial_tags() -> None:
    seed = load_seed()
    pizza_id = next(
        place.id for place in seed.places if place.slug == "naujamiescio-picerija"
    )
    pizza_items = [item for item in seed.items if item.place_id == pizza_id]
    tagged = [item for item in pizza_items if item.dietary_tags]
    untagged = [item for item in pizza_items if not item.dietary_tags]
    assert tagged
    assert untagged
    assert any(item.category is ItemCategory.PIZZA for item in pizza_items)


def test_seed_module_does_not_import_http_or_database() -> None:
    tree = ast.parse(SEED_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(HTTP_OR_DB)


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_seed_loads_through_wp2_store() -> None:
    from kurpaest.persistence.load_seed import import_seed
    from kurpaest.persistence.store import Store, apply_migrations, connect

    seed = load_seed()
    cheapest = min(_kebab_items(seed.items), key=lambda item: item.price_cents)
    vegan = next(item for item in seed.items if DietaryTag.VEGAN in item.dietary_tags)
    with connect() as conn:
        apply_migrations(conn)
        store = Store(conn)
        import_seed(store, seed)
        store.commit()
        loaded_place = store.load_place(cheapest.place_id)
        loaded_kebab = store.load_menu_item(cheapest.id)
        loaded_vegan = store.load_menu_item(vegan.id)
    assert loaded_place is not None
    assert loaded_place.city == "Vilnius"
    assert loaded_kebab is not None
    assert loaded_kebab.price_cents == 499
    assert isinstance(loaded_kebab.price_cents, int)
    assert loaded_vegan is not None
    assert DietaryTag.VEGAN in loaded_vegan.dietary_tags
