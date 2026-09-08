## What

<!-- Summary. If this PR adds a kitchen, say which place. -->

## Checklist (place + menu contributions)

Skip this section unless you are adding or editing `seed/vilnius.json`.

- [ ] Coordinates (`lat`, `lng`) are WGS84 for the kitchen
- [ ] Every item has integer `price_cents` (EUR; no “price on request”)
- [ ] Dietary tags are asserted, never inferred from the dish name
- [ ] `last_verified_at` is ISO-8601 with a timezone
- [ ] `uv run python -m kurpaest.seed` succeeds
- [ ] `uv run pytest` passes

See [docs/contributing-menus.md](docs/contributing-menus.md).
