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
JWT=$(get_jwt) || { log_err "Failed to generate JWT. Is the gateway running? Try: docker compose ps gateway"; exit 1; }

log_section "Disable Service"
log_step "Disabling service '$SERVICE_NAME'..."

resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 15 \
  -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  "${GATEWAY_URL}/services/${SERVICE_NAME}/disable" 2>&1) || true

code=$(parse_http_code "$resp")
body=$(parse_http_body "$resp")

if [[ "$code" == "200" ]]; then
    log_ok "Service '$SERVICE_NAME' disabled successfully"
    if command -v jq &>/dev/null; then
        echo "$body" | jq -r '.status // "Disabled"' 2>/dev/null || echo "Disabled"
    else
        echo "Disabled"
    fi
else
    log_err "Failed to disable service '$SERVICE_NAME' (HTTP $code)"
    if [[ -n "$body" ]]; then
        echo "$body" | head -10
    fi
    exit 1
fi
