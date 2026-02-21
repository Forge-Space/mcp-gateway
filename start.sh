#!/usr/bin/env bash
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
# shellcheck source=scripts/lib/log.sh
source "$ROOT/scripts/lib/log.sh" 2>/dev/null || true

log_section "MCP Gateway"
log_step "Checking environment..."
if ! command -v docker &>/dev/null; then
  log_err "Docker is required. Install Docker and run ./start.sh again."
  exit 1
fi

if docker compose version &>/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose"
else
  log_err "Docker Compose is required (docker compose or docker-compose)."
  exit 1
fi
log_info "Using: $COMPOSE"

if [[ ! -f .env ]]; then
  log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD, JWT_SECRET_KEY, AUTH_ENCRYPTION_SECRET (run: make generate-secrets)"
  exit 1
fi
set -a
source .env 2>/dev/null || true
set +a

mkdir -p data

case "${1:-}" in
  stop)
    log_step "Stopping gateway and translate services..."
    $COMPOSE down --remove-orphans
    log_ok "Gateway stopped."
    ;;
  gateway-only)
    log_step "Starting gateway only (no translate services)..."
    $COMPOSE up -d gateway --remove-orphans
    echo ""
    log_line
    log_ok "Gateway running."
    log_info "Admin UI: http://localhost:${PORT:-4444}/admin"
    log_info "To stop: ./start.sh stop"
    ;;
  *)
    log_step "Building and starting gateway + translate services (first run may take 1–2 min)..."
    $COMPOSE up -d --build --remove-orphans
    echo ""
    log_line
    log_ok "Gateway and translate services running."
    log_info "Admin UI: http://localhost:${PORT:-4444}/admin"
    log_info "Register gateways: ./scripts/gateway/register.sh"
    log_info "Stop: ./start.sh stop"
    ;;
esac
