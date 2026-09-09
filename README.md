# kurpaest.lt

Queryable map of places to eat in Lithuania, with an itemized menu per place — so you can find the cheapest kebab, or filter by dietary preference, instead of browsing restaurant names.

Group project of [kodokaraliai](https://github.com/kodokaraliai): **[kodokaraliai/kurpaest](https://github.com/kodokaraliai/kurpaest)**. How we intend to build it: [docs/architecture.md](docs/architecture.md). Work packages are GitHub issues: [kodokaraliai/kurpaest/issues](https://github.com/kodokaraliai/kurpaest/issues).

This repository is a **launchable skeleton** plus that architecture. The map, menus, cheapest-item search, and dietary filters are GitHub issues, not this first commit.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22+ and npm
- Docker (for local Postgres + PostGIS)

## Try it

One command installs deps and starts the API plus the Vite UI:

```bash
./scripts/run.sh
```

Open `http://127.0.0.1:5173/`. Ctrl-C stops both. Vite **must be served** — `file://` is not a valid run mode. Postgres is not required for this path; the HTTP handlers load `seed/vilnius.json` in-process.

The API is `http://127.0.0.1:8000/`. The two-process commands below are the same steps, split out.

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

`GET /places?bbox=s,w,n,e` returns map pins in that viewport (`city` is optional). Bbox is required — the handler does not download the whole country. Pins come from the reviewed Vilnius seed (`seed/vilnius.json`).

`GET /places/{id}` is place detail (hours, `last_verified_at`). `GET /places/{id}/menu` is the itemized menu: integer `price_cents`, currency EUR, dietary tags. Clicking a map pin opens that menu in the Vite app.

`GET /items?q=kebab&sort=price` is cheapest-item search (optional `city`, `near=lat,lng`, `radius_m`, `dietary`). Queries expand through a small alias table (`kebab`/`giros`/`šaurma`, `cepelinai`/`didžkukuliai`) and fold Lithuanian diacritics for matching; display keeps the original spelling. The Vite search box lists those rows and jumps each to its pin.

Dietary chips are conjunctive and stateless (`dietary=vegan,gluten_free`). Unknown tags on an item do not match. `GET /places?bbox=&dietary=` keeps pins for places that have at least one verified matching item.

`uv run python -m kurpaest` is the same entry. `--host` and `--port` are optional.

## Database (Postgres + PostGIS)

```bash
docker compose up -d
cp .env.example .env   # DATABASE_URL=postgresql://kurpaest:kurpaest@127.0.0.1:5432/kurpaest
```

`compose.yaml` starts `postgis/postgis`. Schema lives in `migrations/` (`geography(Point, 4326)` plus a gist index on `places.location`). First container boot applies those files via `/docker-entrypoint-initdb.d`. The Python adapter is `kurpaest.persistence.Store` (save/load of WP-1 domain types).

With the container healthy and `.env` present:

```bash
uv run pytest tests/test_persistence.py -q
```

That includes `test_store_save_load_round_trip` against the real database. The rest of the suite: `uv run pytest`.

Vilnius seed (places + itemized menus) lives in `seed/vilnius.json`. How to add a kitchen: [docs/contributing-menus.md](docs/contributing-menus.md) (`uv run python -m kurpaest.seed` validates). Load it through the WP-2 store:

```bash
uv run python -m kurpaest.persistence.load_seed
```

The HTTP map reads the same JSON in-process. Re-running the import upserts by id.

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
seed/             Vilnius places + itemized menus (JSON)
migrations/       SQL schema (PostGIS geography + gist)
compose.yaml      local Postgres + PostGIS
scripts/run.sh    one-shot API + Vite launcher
tests/            pytest — drives the real ASGI app and domain/persistence
frontend/         React + Vite
docs/architecture.md
```

## Agents

`AGENTS.md` is the always-loaded instruction file. Product language is `docs/architecture.md`. Night shift (VPS / unattended drain of `ready-for-agent` issues): `./scripts/night-shift.sh` (prompt: `docs/agents/night-shift.md`).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Pick up a GitHub issue that maps to a work package in the architecture doc. Label an issue `ready-for-agent` only when its brief is complete enough for an unattended run.
