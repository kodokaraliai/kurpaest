#!/usr/bin/env bash
# Start the kurpaest API and Vite UI together.
#
# Usage (from the repo root, or via this path):
#   ./scripts/run.sh
#
# API:  http://127.0.0.1:8000/
# UI:   http://127.0.0.1:5173/   (proxies /api to the API)
# Ctrl-C stops both. Do not open the UI as file://.

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

API_HOST="${KURPAEST_HOST:-127.0.0.1}"
API_PORT="${KURPAEST_PORT:-8000}"
UI_HOST="127.0.0.1"
UI_PORT="${KURPAEST_UI_PORT:-5173}"

need() {
  command -v "$1" >/dev/null || {
    echo "run: $1 not on PATH" >&2
    exit 1
  }
}

need uv
need node
need npm
need python3

port_open() {
  local host="$1" port="$2"
  python3 -c "
import socket, sys
s = socket.socket()
s.settimeout(0.3)
try:
    s.connect(('$host', int('$port')))
except OSError:
    sys.exit(1)
finally:
    s.close()
"
}

if port_open "$API_HOST" "$API_PORT"; then
  echo "run: $API_HOST:$API_PORT is already in use (API port)" >&2
  exit 1
fi
if port_open "$UI_HOST" "$UI_PORT"; then
  echo "run: $UI_HOST:$UI_PORT is already in use (Vite port)" >&2
  exit 1
fi

api_pid=

cleanup() {
  if [ -n "${api_pid:-}" ] && kill -0 "$api_pid" 2>/dev/null; then
    kill "$api_pid" 2>/dev/null || true
    wait "$api_pid" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "run: installing Python deps"
uv sync --group dev

echo "run: installing frontend deps"
(cd "$ROOT/frontend" && npm install)

echo "run: starting API on http://${API_HOST}:${API_PORT}/"
uv run kurpaest --host "$API_HOST" --port "$API_PORT" &
api_pid=$!

api_ready=0
for _ in $(seq 1 80); do
  if ! kill -0 "$api_pid" 2>/dev/null; then
    echo "run: API exited before it was ready" >&2
    exit 1
  fi
  if python3 -c "
import urllib.request, sys
try:
    with urllib.request.urlopen('http://${API_HOST}:${API_PORT}/', timeout=0.5) as resp:
        sys.exit(0 if resp.status == 200 else 1)
except Exception:
    sys.exit(1)
"; then
    api_ready=1
    break
  fi
  sleep 0.1
done

if [ "$api_ready" -ne 1 ]; then
  echo "run: API did not respond at http://${API_HOST}:${API_PORT}/" >&2
  exit 1
fi

echo "run: API is up"
echo "run: starting Vite on http://${UI_HOST}:${UI_PORT}/"
echo "run: open http://${UI_HOST}:${UI_PORT}/  (not file://)"

cd "$ROOT/frontend"
npm run dev -- --host "$UI_HOST" --port "$UI_PORT"
