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
```
