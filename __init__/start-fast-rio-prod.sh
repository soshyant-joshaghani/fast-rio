#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -f .env ]]; then
  cp -n .env.example .env 2>/dev/null || true
fi
source "$(dirname "$0")/lib/ensure-letsencrypt.sh"
docker network inspect traefik-public >/dev/null 2>&1 || docker network create traefik-public
docker compose up -d --build
echo
echo "fast-rio production stack started."
echo "Update DOMAIN in compose.yml, ACME email in compose.traefik.yml, and DNS before going live."
