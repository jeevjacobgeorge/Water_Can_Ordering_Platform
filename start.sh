#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed or is not in PATH." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not running or is not accessible." >&2
  exit 1
fi

"$SCRIPT_DIR/stop.sh"

if [[ ! -f .env ]]; then
  echo "Creating local .env from .env.example..."
  cp .env.example .env
  echo "Add Razorpay test keys to .env when payment testing is needed."
fi

echo "Building and starting PostgreSQL, backend, and frontend..."
docker compose up --build -d

echo "Applying database migrations..."
docker compose exec -T backend alembic upgrade head

echo "Seeding development data if the database is empty..."
docker compose exec -T backend python -m app.db.seed

echo
echo "========================================"
echo "  Application is running"
echo "========================================"
echo "  Customer app: http://localhost:3000"
echo "  LAN app:      http://192.168.1.23:3000"
echo "  API:          http://localhost:8000"
echo "  LAN API:      http://192.168.1.23:8000"
echo "  API docs:     http://localhost:8000/docs"
echo "========================================"
echo

docker compose ps

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:3000 >/dev/null 2>&1 &
fi
