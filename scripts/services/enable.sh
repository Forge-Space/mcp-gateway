#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

SERVICE_NAME="$1"
if [ -z "$SERVICE_NAME" ]; then
    log_err "Usage: $0 <service-name>"
    exit 1
fi

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
normalize_gateway_url || true
JWT=$(get_jwt) || { log_err "Failed to generate JWT."; exit 1; }

log_section "Enable Service"
log_step "Enabling service '$SERVICE_NAME'..."

resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 15 \
  -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  "${GATEWAY_URL}/services/${SERVICE_NAME}/enable" 2>&1) || true

code=$(parse_http_code "$resp")
body=$(parse_http_body "$resp")

if [[ "$code" == "200" ]]; then
    log_ok "Service '$SERVICE_NAME' enabled successfully"
else
    log_err "Failed to enable service '$SERVICE_NAME' (HTTP $code)"
    [[ -n "$body" ]] && echo "$body" | head -10
    exit 1
fi
