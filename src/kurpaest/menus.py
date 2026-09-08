"""Itemized menu queries. No HTTP imports."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from kurpaest.domain import Menu, MenuItem, Place


def place_by_id(places: Iterable[Place], place_id: UUID) -> Place | None:
    """The place with this id, or None."""
    for place in places:
        if place.id == place_id:
            return place
    return None


def menu_record_for_place(menus: Iterable[Menu], place_id: UUID) -> Menu | None:
    """The menu snapshot for this place, or None."""
    for menu in menus:
        if menu.place_id == place_id:
            return menu
    return None


def menu_for_place(items: Iterable[MenuItem], place_id: UUID) -> list[MenuItem]:
    """Items sold at this place, in catalog order."""
    return [item for item in items if item.place_id == place_id]
