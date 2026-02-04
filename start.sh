#!/usr/bin/env bash
set -e
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "MCP Gateway – checking environment..."
if ! command -v docker &>/dev/null; then
  echo "Docker is required. Install Docker and run ./start.sh again."
  exit 1
fi

if docker compose version &>/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose"
else
  echo "Docker Compose is required (docker compose or docker-compose)."
  exit 1
fi
echo "Using: $COMPOSE"

if [[ ! -f .env ]]; then
  echo "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD, JWT_SECRET_KEY"
  exit 1
fi
set -a
source .env 2>/dev/null || true
set +a

mkdir -p data

case "${1:-}" in
  stop)
    echo "Stopping gateway and translate services..."
    $COMPOSE down --remove-orphans
    echo "Gateway stopped."
    ;;
  gateway-only)
    echo "Starting gateway only (no translate services)..."
    $COMPOSE up -d gateway --remove-orphans
    echo ""
    echo "Gateway running. Admin UI: http://localhost:${PORT:-4444}/admin"
    echo "To stop: ./start.sh stop"
    ;;
  *)
    echo "Building and starting gateway + translate services (first run may take 1–2 min)..."
    $COMPOSE up -d --build --remove-orphans
    echo ""
    echo "Gateway and translate services running."
    echo "Admin UI: http://localhost:${PORT:-4444}/admin"
    echo "Register gateways: ./scripts/register-gateways.sh"
    echo "Stop: ./start.sh stop"
    ;;
esac
