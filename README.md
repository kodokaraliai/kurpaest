# kurpaest.lt

Queryable map of places to eat in Lithuania, with an itemized menu per place — so you can find the cheapest kebab, or filter by dietary preference, instead of browsing restaurant names.

Group project of [kodokaraliai](https://github.com/kodokaraliai): **[kodokaraliai/kurpaest](https://github.com/kodokaraliai/kurpaest)**. How we intend to build it: [docs/architecture.md](docs/architecture.md). Work packages are GitHub issues: [kodokaraliai/kurpaest/issues](https://github.com/kodokaraliai/kurpaest/issues).

This repository is a **launchable skeleton** plus that architecture. The map, menus, cheapest-item search, and dietary filters are GitHub issues, not this first commit.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22+ and npm
- Docker (for local Postgres + PostGIS)

## Backend

```bash
uv sync --group dev
uv run pytest
uv run ruff check
uv run ruff format --check
uv run kurpaest
```

The API listens on `http://127.0.0.1:8000/`. `GET /` returns JSON:

```json
{"service": "kurpaest", "status": "ok", "site": "kurpaest.lt"}
```

`uv run python -m kurpaest` is the same entry. `--host` and `--port` are optional.

## Database (Postgres + PostGIS)

```bash
docker compose up -d
cp .env.example .env   # DATABASE_URL=postgresql://kurpaest:kurpaest@127.0.0.1:5432/kurpaest
```

`compose.yaml` starts `postgis/postgis`. Schema lives in `migrations/` (`geography(Point, 4326)` plus a gist index on `places.location`). First container boot applies those files via `/docker-entrypoint-initdb.d`. The Python adapter is `kurpaest.persistence.Store` (save/load of WP-1 domain types).

## Frontend

Vite **must be served**. Opening `index.html` as `file://` will not work.

```bash
cd frontend
npm install
npm run dev
```

Dev server: `http://127.0.0.1:5173/`.

Production-like build:

```bash
cd frontend
npm run build
npm run preview
```

## Layout

```
src/kurpaest/     Python package (HTTP entry in app.py, domain in domain.py)
src/kurpaest/persistence/  PostGIS adapter
migrations/       SQL schema (PostGIS geography + gist)
compose.yaml      local Postgres + PostGIS
tests/            pytest — drives the real ASGI app and domain/persistence
frontend/         React + Vite
docs/architecture.md
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Pick up a GitHub issue that maps to a work package in the architecture doc.
