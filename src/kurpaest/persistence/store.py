"""Postgres + PostGIS adapter. Maps through persistence.mapping; owns SQL."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from kurpaest.domain import Menu, MenuItem, Place
from kurpaest.persistence.mapping import (
    menu_from_row,
    menu_item_from_row,
    menu_item_to_row,
    menu_to_row,
    place_from_row,
    place_to_row,
)

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"

_SAVE_PLACE = """
INSERT INTO places (
    id, name, slug, location, address, city, hours, source, updated_at,
    phone, website
) VALUES (
    %(id)s, %(name)s, %(slug)s,
    ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
    %(address)s, %(city)s, %(hours)s, %(source)s, %(updated_at)s,
    %(phone)s, %(website)s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    slug = EXCLUDED.slug,
    location = EXCLUDED.location,
    address = EXCLUDED.address,
    city = EXCLUDED.city,
    hours = EXCLUDED.hours,
    source = EXCLUDED.source,
    updated_at = EXCLUDED.updated_at,
    phone = EXCLUDED.phone,
    website = EXCLUDED.website
"""

_LOAD_PLACE = """
SELECT
    id, name, slug,
    ST_Y(location::geometry) AS lat,
    ST_X(location::geometry) AS lng,
    address, city, hours, source, updated_at, phone, website
FROM places
WHERE id = %(id)s
"""

_SAVE_MENU = """
INSERT INTO menus (id, place_id, currency, last_verified_at, language)
VALUES (%(id)s, %(place_id)s, %(currency)s, %(last_verified_at)s, %(language)s)
ON CONFLICT (id) DO UPDATE SET
    place_id = EXCLUDED.place_id,
    currency = EXCLUDED.currency,
    last_verified_at = EXCLUDED.last_verified_at,
    language = EXCLUDED.language
"""

_LOAD_MENU = """
SELECT id, place_id, currency, last_verified_at, language
FROM menus
WHERE id = %(id)s
"""

_SAVE_ITEM = """
INSERT INTO menu_items (
    id, place_id, menu_id, name, name_en, description, price_cents, category,
    dietary_tags, search_tokens
) VALUES (
    %(id)s, %(place_id)s, %(menu_id)s, %(name)s, %(name_en)s, %(description)s,
    %(price_cents)s, %(category)s, %(dietary_tags)s, %(search_tokens)s
)
ON CONFLICT (id) DO UPDATE SET
    place_id = EXCLUDED.place_id,
    menu_id = EXCLUDED.menu_id,
    name = EXCLUDED.name,
    name_en = EXCLUDED.name_en,
    description = EXCLUDED.description,
    price_cents = EXCLUDED.price_cents,
    category = EXCLUDED.category,
    dietary_tags = EXCLUDED.dietary_tags,
    search_tokens = EXCLUDED.search_tokens
"""

_LOAD_ITEM = """
SELECT
    id, place_id, menu_id, name, name_en, description, price_cents, category,
    dietary_tags, search_tokens
FROM menu_items
WHERE id = %(id)s
"""


def connect(url: str | None = None) -> psycopg.Connection:
    dsn = url or os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(dsn, row_factory=dict_row)


def apply_migrations(conn: psycopg.Connection, directory: Path | None = None) -> None:
    root = directory or MIGRATIONS_DIR
    for path in sorted(root.glob("*.sql")):
        for command in _sql_commands(path.read_text(encoding="utf-8")):
            conn.execute(command)
    conn.commit()


def _sql_commands(script: str) -> list[str]:
    commands: list[str] = []
    current: list[str] = []
    for line in script.splitlines():
        if line.strip().startswith("--"):
            continue
        current.append(line)
        if line.rstrip().endswith(";"):
            command = "\n".join(current).strip()
            if command:
                commands.append(command)
            current = []
    leftover = "\n".join(current).strip()
    if leftover:
        commands.append(leftover)
    return commands


class Store:
    """Save and load WP-1 domain records through PostGIS."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def save_place(self, place: Place) -> None:
        row = place_to_row(place)
        row["hours"] = Json(row["hours"])
        self._conn.execute(_SAVE_PLACE, row)

    def load_place(self, place_id: UUID) -> Place | None:
        loaded = self._conn.execute(_LOAD_PLACE, {"id": place_id}).fetchone()
        if loaded is None:
            return None
        return place_from_row(loaded)

    def save_menu(self, menu: Menu) -> None:
        self._conn.execute(_SAVE_MENU, menu_to_row(menu))

    def load_menu(self, menu_id: UUID) -> Menu | None:
        loaded = self._conn.execute(_LOAD_MENU, {"id": menu_id}).fetchone()
        if loaded is None:
            return None
        return menu_from_row(loaded)

    def save_menu_item(self, item: MenuItem) -> None:
        self._conn.execute(_SAVE_ITEM, menu_item_to_row(item))

    def load_menu_item(self, item_id: UUID) -> MenuItem | None:
        loaded = self._conn.execute(_LOAD_ITEM, {"id": item_id}).fetchone()
        if loaded is None:
            return None
        return menu_item_from_row(loaded)

    def commit(self) -> None:
        self._conn.commit()
