# Agent notes

- Product and work split: `docs/architecture.md`. GitHub issues 1:1 the **Work packages (WP-n)** section. Do not implement WP-3–WP-6 unless the issue you are on says so.
- Python: `uv` for env and lockfile, `ruff` for format/lint, `uv run pytest` for tests. Package lives in `src/kurpaest/`.
- HTTP is a seam (`src/kurpaest/app.py`). Cheapest-item, dietary, and geo logic must not import FastAPI.
- Frontend: React + Vite in `frontend/`. Must be served (`npm run dev` or `npm run build` + `npm run preview`). `file://` is not a valid run mode.
- Money: integer `price_cents`. Dietary tags are explicit; unknown does not match a filter.
