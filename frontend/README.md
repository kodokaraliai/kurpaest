# kurpaest frontend

React + Vite UI for [kurpaest.lt](https://kurpaest.lt). Serve it — Vite does not run from `file://`.

```bash
npm install
npm run dev      # http://127.0.0.1:5173/
npm run build
npm run preview  # http://127.0.0.1:4173/
```

The map loads pins from `GET /api/places?bbox=s,w,n,e` (Vite proxies `/api` to the Python API). Pan and zoom refetch the viewport.

Product and work split: [`../docs/architecture.md`](../docs/architecture.md).
