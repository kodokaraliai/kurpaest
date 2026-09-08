"""Alias expansion and diacritic folding — no FastAPI."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from kurpaest.aliases import ALIASES, expand_term, fold_diacritics
from kurpaest.catalog import ITEMS, PLACES
from kurpaest.domain import ItemCategory, MenuItem, Place, PlaceSource
from kurpaest.items import cheapest_items

ROOT = Path(__file__).resolve().parents[1]
ALIASES_SOURCE = ROOT / "src" / "kurpaest" / "aliases.py"

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


def _place(**overrides: object) -> Place:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Valgykla",
        "slug": "valgykla",
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
        "search_tokens": (),
    }
    values.update(overrides)
    return MenuItem(**values)  # type: ignore[arg-type]


def test_fold_diacritics_strips_lithuanian_marks_keeps_display_separate() -> None:
    assert fold_diacritics("Šaurma") == "saurma"
    assert fold_diacritics("didžkukuliai") == "didzkukuliai"
    assert fold_diacritics("döner") == "doner"
    assert fold_diacritics("Cepelinai su mėsa") == "cepelinai su mesa"
    original = "Šaurma"
    assert original == "Šaurma"


def test_expand_kebab_group() -> None:
    tokens = set(expand_term("kebab"))
    assert {"kebab", "kebabas", "doner", "shawarma", "saurma", "giros"} <= tokens
    assert set(expand_term("kebabas")) == tokens
    assert set(expand_term("döner")) == tokens
    assert set(expand_term("šaurma")) == tokens
    assert set(expand_term("giros")) == tokens


def test_expand_cepelinai_group() -> None:
    tokens = set(expand_term("cepelinai"))
    assert {"cepelinai", "didzkukuliai"} <= tokens
    assert set(expand_term("didžkukuliai")) == tokens


def test_alias_table_is_expandable_records() -> None:
    terms = {record.term for record in ALIASES}
    assert "kebab" in terms
    assert "cepelinai" in terms


def test_kebab_query_hits_saurma_and_doner_without_shared_tokens() -> None:
    place = _place()
    saurma = _item(
        place_id=place.id,
        name="Šaurma",
        price_cents=620,
        category=ItemCategory.KEBAB,
        search_tokens=(),
    )
    doner = _item(
        place_id=place.id,
        name="Döner",
        price_cents=650,
        category=ItemCategory.KEBAB,
        search_tokens=(),
    )
    pizza = _item(
        place_id=place.id,
        name="Pica",
        price_cents=100,
        category=ItemCategory.PIZZA,
        search_tokens=("pizza",),
    )
    found = cheapest_items((saurma, doner, pizza), (place,), "kebab")
    assert [row.item.name for row in found] == ["Šaurma", "Döner"]
    assert found[0].item.name == "Šaurma"


def test_cepelinai_query_hits_didzkukuliai_name() -> None:
    place = _place()
    dumplings = _item(
        place_id=place.id,
        name="Didžkukuliai",
        price_cents=720,
        search_tokens=(),
    )
    found = cheapest_items((dumplings,), (place,), "cepelinai")
    assert [row.item.name for row in found] == ["Didžkukuliai"]
    reverse = cheapest_items((dumplings,), (place,), "didžkukuliai")
    assert [row.item.name for row in reverse] == ["Didžkukuliai"]


def test_seed_giros_query_returns_kebab_rows_cheapest_first() -> None:
    found = cheapest_items(ITEMS, PLACES, "giros")
    assert found
    assert found[0].item.name == "Kebabas"
    assert found[0].item.price_cents == 499
    names = {row.item.name for row in found}
    assert "Šaurma" in names or "Döner" in names or "Kebabas pita" in names


def test_aliases_module_does_not_import_http_libraries() -> None:
    imported = _imports_of(ALIASES_SOURCE)
    assert imported.isdisjoint(HTTP_LIBRARIES)
