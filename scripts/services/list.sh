#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
normalize_gateway_url || true
JWT=$(get_jwt) || { log_err "Failed to generate JWT."; exit 1; }

log_section "Service Status"
log_step "Fetching service status from $GATEWAY_URL..."

resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 15 \
  -H "Authorization: Bearer $JWT" \
  "${GATEWAY_URL}/services" 2>&1) || true

code=$(parse_http_code "$resp")
body=$(parse_http_body "$resp")

if [[ "$code" != "200" ]]; then
    log_err "Failed to fetch services (HTTP $code)"
    [[ -n "$body" ]] && echo "$body" | head -10
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo "$body"
    exit 0
fi

echo "$body" | jq '.'
