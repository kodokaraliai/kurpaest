# kurpaest frontend

React + Vite UI for [kurpaest.lt](https://kurpaest.lt). Serve it — Vite does not run from `file://`.

From the repo root, `./scripts/run.sh` starts this UI and the Python API together.

```bash
npm install
npm run dev      # http://127.0.0.1:5173/
npm run build
npm run preview  # http://127.0.0.1:4173/
```

The map loads pins from `GET /api/places?bbox=s,w,n,e` (Vite proxies `/api` to the Python API). Pan and zoom refetch the viewport. Click a pin to open the place panel (`GET /api/places/{id}` and `GET /api/places/{id}/menu`): items grouped by category, integer prices, dietary tags, and `last_verified_at`. The search box calls `GET /api/items?q=&sort=price` (cheapest matching items; each row jumps to its pin). Dietary chips are conjunctive and forwarded as `dietary=` on item search and on `GET /api/places?bbox=` (places with at least one verified matching item). Untagged dishes do not match. Lithuanian copy is the default, with an English toggle.

Product and work split: [`../docs/architecture.md`](../docs/architecture.md).
