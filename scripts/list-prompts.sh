#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=scripts/lib/log.sh
source "$SCRIPT_DIR/lib/log.sh" 2>/dev/null || true

if [[ ! -f .env ]]; then
  log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."
  exit 1
fi

set -a
source .env
set +a

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"

log_section "Prompts"
log_step "Fetching from $GATEWAY_URL..."

if docker compose version &>/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose"
else
  COMPOSE=""
fi

jwt_failed() {
  log_err "Failed to generate JWT. Is the gateway running? Try: docker compose ps gateway"
  log_info "Re-running token command to show error:" >&2
  if [[ -n "$COMPOSE" ]] && $COMPOSE ps gateway -q 2>/dev/null | grep -q .; then
    $COMPOSE exec -T gateway python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" >&2
  else
    docker exec "${MCPGATEWAY_CONTAINER:-mcpgateway}" python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" >&2
  fi
  exit 1
}

if [[ -n "$COMPOSE" ]] && $COMPOSE ps gateway -q 2>/dev/null | grep -q .; then
  JWT=$($COMPOSE exec -T gateway python3 -m mcpgateway.utils.create_jwt_token \
    --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null) || true
else
  CONTAINER="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    log_err "Gateway is not running. Start with ./start.sh (from repo root)."
    exit 1
  fi
  JWT=$(docker exec "$CONTAINER" python3 -m mcpgateway.utils.create_jwt_token \
    --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null) || true
fi

if [[ -z "$JWT" ]]; then
  jwt_failed
fi

resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 -H "Authorization: Bearer $JWT" \
  "${GATEWAY_URL}/prompts?include_pagination=false" 2>&1) || true
code=$(echo "$resp" | tail -n1)
body=$(echo "$resp" | sed '$d')

if [[ "$code" != "200" ]]; then
  if [[ -z "$code" ]]; then
    log_err "GET /prompts failed (no response). Check gateway is up: $GATEWAY_URL/health"
  else
    log_err "GET /prompts returned HTTP $code"
  fi
  if [[ -n "$body" ]]; then
    echo "$body" | head -50
  else
    log_info "(empty response body)" >&2
  fi
  exit 1
fi

log_ok "Prompts loaded."
log_line
if command -v jq &>/dev/null; then
  echo "$body" | jq '.'
else
  echo "$body"
fi
