# Adding a place and menu

kodokaraliai members add kitchens by editing `seed/vilnius.json` and opening a
pull request. Prefer fewer **verified** menus over guessed ones. There is no
admin UI; do not scrape live menus.

Validate a draft with:

```bash
uv run python -m kurpaest.seed
uv run pytest
```

The first command loads the JSON through the same constructors the API uses.

## Format

One JSON object, a `places` array. Each place owns one menu snapshot:

```json
{
  "places": [
    {
      "name": "Senamiesčio kebabinė",
      "slug": "senamiescio-kebabine",
      "lat": 54.6818,
      "lng": 25.2874,
      "address": "Pilies g. 8, Vilnius",
      "city": "Vilnius",
      "hours": [
        {"weekday": 0, "open_minute": 600, "close_minute": 1380}
      ],
      "menu": {
        "currency": "EUR",
        "language": "lt",
        "last_verified_at": "2026-09-08T12:00:00+00:00",
        "items": [
          {
            "name": "Kebabas pita",
            "name_en": "Kebab in pita",
            "price_cents": 550,
            "category": "kebab",
            "dietary_tags": [],
            "search_tokens": ["kebab", "kebabas"]
          }
        ]
      }
    }
  ]
}
```

`slug` must be unique per `city`. `weekday` is 0 = Monday … 6 = Sunday. Minutes
are from midnight (`600` is 10:00). `phone` and `website` are optional.

### Required

| Field | Rule |
| --- | --- |
| `lat`, `lng` | WGS84. A place without coordinates is rejected. |
| `price_cents` | Integer euro cents on **every** item. No floats. No “price on request”. |
| `last_verified_at` | ISO-8601 with a timezone on the menu. |
| `currency` | `EUR` for v1. |
| `category` | `kebab` / `pizza` / `soup` / `main` / `dessert` / `drink` / `other` |
| `dietary_tags` | Closed set, or `[]`. |

Dietary tags (only these strings): `vegetarian`, `vegan`, `gluten_free`,
`lactose_free`, `nut_free`, `halal`, `pescatarian`.

### Dietary tags are asserted, never inferred

Empty `dietary_tags` means **unknown**, not “contains everything”. Do not guess
`vegan` from a dish name. A false positive on diet or allergens is worse than a
missing tag. Unknown items drop out of a dietary filter.

### Search tokens

Optional aliases for cheapest-item search (`kebabas`, `didžkukuliai`, …). Display
names keep Lithuanian spelling; matching folds diacritics.

## PR checklist

When the PR adds or edits a place + items:

- [ ] Coordinates are the real kitchen, not a city centroid.
- [ ] Every item has integer `price_cents` (EUR).
- [ ] Dietary tags are only those a person verified; names were not used to infer tags.
- [ ] `last_verified_at` is when those prices/tags were checked, with a timezone.
- [ ] `uv run python -m kurpaest.seed` prints `ok: …`
- [ ] `uv run pytest` passes.

After merge, optional local PostGIS import: `uv run python -m kurpaest.persistence.load_seed`.
