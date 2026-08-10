#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f .env ]]; then
  cp -n .env.example .env 2>/dev/null || true
fi

bash __init__/setup-local.sh

echo "[fast-rio] Starting dev infrastructure (db, proxy, adminer)..."
docker compose -f compose.dev.yml up -d db adminer
# Recreate proxy so Traefik re-reads dynamic.dev.yml (Docker Desktop bind mounts skip fsnotify).
docker compose -f compose.dev.yml up -d --force-recreate --no-deps proxy

echo "[fast-rio] Waiting for Postgres..."
until docker compose -f compose.dev.yml exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" >/dev/null 2>&1; do
  sleep 2
done

echo "[fast-rio] Running migrations + seed (local prestart)..."
(
  cd backend
  # shellcheck disable=SC1091
  source ../.venv/bin/activate
  export PYTHONPATH="$PWD"
  python app/backend_pre_start.py
  alembic -c alembic.ini upgrade head
  python app/initial_data.py
)

ROOT="$(pwd)"

echo "[fast-rio] Starting backend (uvicorn --reload) and frontend (rio run)..."
(
  cd backend
  # shellcheck disable=SC1091
  source ../.venv/bin/activate
  export PYTHONPATH="$PWD"
  exec python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 18000
) &
BACKEND_PID=$!

(
  cd "$ROOT/frontend"
  # shellcheck disable=SC1091
  source ../.venv/bin/activate
  export PYTHONPATH="$ROOT/frontend"
  export PUBLIC_API_BASE_URL="${PUBLIC_API_BASE_URL:-http://localhost:18000/api/v1}"
  exec python -m rio run --port 5173 --public
) &
FRONTEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo
echo "Dev stack ready (hot reload on save):"
echo "  Dashboard: http://dashboard.localhost"
echo "  API docs:  http://api.localhost/docs  (Swagger)"
echo "  Scalar:    http://api.localhost/sdoc"
echo "  Adminer:   http://adminer.localhost"
echo "  Traefik:   http://localhost:18090"
echo
echo "Direct: http://localhost:5173  http://localhost:18000/docs"
echo "Press Ctrl+C to stop backend and frontend."

wait
