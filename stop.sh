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

echo "Stopping Water Can Platform services..."
docker compose down
echo "Services stopped. Database data was preserved."
