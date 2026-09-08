"""Place catalog served to the map and place panels. Sourced from the WP-8 seed."""

from __future__ import annotations

from kurpaest.seed import load_seed

_SEED = load_seed()
PLACES = _SEED.places
MENUS = _SEED.menus
ITEMS = _SEED.items
