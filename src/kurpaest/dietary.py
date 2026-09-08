"""Conjunctive dietary-tag matching. No HTTP imports.

Tags are asserted on the item. Empty tags mean unknown and do not match a
filter. Do not infer tags from dish names.
"""

from __future__ import annotations

from collections.abc import Iterable

from kurpaest.domain import DietaryTag, MenuItem, Place


def dietary_tags(dietary: Iterable[object]) -> frozenset[DietaryTag]:
    """Closed vocabulary. Unknown tag names raise ValueError."""
    return frozenset(DietaryTag(tag) for tag in dietary)


def item_matches_dietary(item: MenuItem, required: frozenset[DietaryTag]) -> bool:
    """True when the item carries every requested tag. No filter → True."""
    if not required:
        return True
    return required <= item.dietary_tags


def items_matching_dietary(
    items: Iterable[MenuItem],
    dietary: Iterable[object],
) -> list[MenuItem]:
    """Items that satisfy a conjunctive dietary filter, in catalog order."""
    required = dietary_tags(dietary)
    return [item for item in items if item_matches_dietary(item, required)]


def places_with_dietary(
    places: Iterable[Place],
    items: Iterable[MenuItem],
    dietary: Iterable[object],
) -> list[Place]:
    """Places that have at least one item carrying every requested tag."""
    required = dietary_tags(dietary)
    if not required:
        return list(places)
    wanted = {item.place_id for item in items if item_matches_dietary(item, required)}
    return [place for place in places if place.id in wanted]
