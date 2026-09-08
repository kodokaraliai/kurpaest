# Domain Docs

How agents should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`docs/architecture.md`**: product, domain types, query model, work-package split.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in, if any exist.

If `docs/adr/` is empty, proceed. Do not invent ADRs up front.

## File structure

Single-context repo:

```
docs/architecture.md    product + domain + WP split
docs/agents/            night-shift, tracker, labels
src/kurpaest/domain.py  WP-1 types
src/kurpaest/persistence/  WP-2 PostGIS adapter
src/kurpaest/places.py  WP-3 viewport query (`places_in_bounds`)
src/kurpaest/menus.py   WP-4 `menu_for_place` (no HTTP)
src/kurpaest/items.py   WP-5 `cheapest_items` (no HTTP)
src/kurpaest/aliases.py WP-7 alias table + diacritic folding (no HTTP)
src/kurpaest/dietary.py WP-6 conjunctive tag filter (no HTTP)
src/kurpaest/catalog.py  map pins and menus from the WP-8 seed
src/kurpaest/seed.py    WP-8 JSON → domain types
seed/vilnius.json       reviewed Vilnius places + menus
```
