#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
COMPOSE=$(compose_cmd)
JWT=$(get_jwt) || { log_err "Failed to generate JWT. Is the gateway running? Try: docker compose ps gateway"; exit 1; }

log_section "Prompts"
log_step "Fetching from $GATEWAY_URL..."

resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 -H "Authorization: Bearer $JWT" \
  "${GATEWAY_URL}/prompts?include_pagination=false" 2>&1) || true
code=$(parse_http_code "$resp")
body=$(parse_http_body "$resp")

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
