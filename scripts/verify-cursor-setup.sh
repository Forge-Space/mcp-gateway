#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=scripts/lib/log.sh
source "$SCRIPT_DIR/lib/log.sh" 2>/dev/null || true

ok=0
fail=0

check() {
  if [[ "$1" == "1" ]]; then
    log_ok "$2"
    ok=$((ok + 1))
    return 0
  else
    log_fail "$2"
    fail=$((fail + 1))
    return 1
  fi
}

log_section "Cursor (wrapper) setup"
log_step "Checking environment..."

if [[ ! -f .env ]]; then
  log_err ".env not found. Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."
  exit 1
fi
set -a
source .env
set +a

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$GATEWAY_URL/health" 2>/dev/null || true)
if [[ "$code" != "200" ]] && [[ "$GATEWAY_URL" =~ 127\.0\.0\.1 ]]; then
  alt="${GATEWAY_URL//127.0.0.1/localhost}"
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$alt/health" 2>/dev/null || true)
  [[ "$code" == "200" ]] && GATEWAY_URL="$alt"
elif [[ "$code" != "200" ]] && [[ "$GATEWAY_URL" =~ localhost ]]; then
  alt="${GATEWAY_URL//localhost/127.0.0.1}"
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$alt/health" 2>/dev/null || true)
  [[ "$code" == "200" ]] && GATEWAY_URL="$alt"
fi
if [[ "$code" == "200" ]]; then check 1 "Gateway reachable at $GATEWAY_URL (health=$code)"; else check 0 "Gateway reachable at $GATEWAY_URL (health=$code). Run: make start"; fi

url_file="$REPO_ROOT/data/.cursor-mcp-url"
if [[ ! -f "$url_file" || ! -s "$url_file" ]]; then
  check 0 "data/.cursor-mcp-url missing or empty (run: make register)"
  echo ""
  log_info "Next: make start && make register && restart Cursor"
  exit 1
fi
MCP_URL=$(head -n1 "$url_file" | tr -d '\r\n')
check 1 "data/.cursor-mcp-url exists and has URL"

if [[ ! "$MCP_URL" =~ /servers/([a-f0-9-]+)/mcp ]]; then
  check 0 "URL in .cursor-mcp-url does not look like .../servers/UUID/mcp"
  echo ""
  log_info "Next: make register (to refresh the URL)"
  exit 1
fi
SERVER_ID="${BASH_REMATCH[1]}"

JWT=$(python3 "$SCRIPT_DIR/create_jwt_token_standalone.py" 2>/dev/null) || true
if [[ -z "$JWT" ]]; then
  CONTAINER="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    JWT=$(docker exec "$CONTAINER" python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null)
  fi
fi
if [[ -z "$JWT" ]]; then
  check 0 "Could not generate JWT (need PyJWT or running gateway container)"
else
  check 1 "JWT generated"
fi

if [[ -n "$JWT" ]]; then
  servers_resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 15 \
    -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers?limit=0&include_pagination=false" 2>/dev/null)
  servers_code=$(echo "$servers_resp" | tail -n1)
  servers_body=$(echo "$servers_resp" | sed '$d')
  if [[ "$servers_code" != "200" ]]; then
    check 0 "GET /servers returned $servers_code (expected 200)"
  else
    found=$(echo "$servers_body" | jq -r --arg id "$SERVER_ID" 'if type == "array" then .[] else .servers[]? // empty end | select(.id == $id) | .id' 2>/dev/null | head -1)
    if [[ "$found" == "$SERVER_ID" ]]; then
      check 1 "Server ID $SERVER_ID exists on gateway"
    else
      check 0 "Server ID $SERVER_ID not found on gateway (stale URL? run: make register)"
    fi
  fi
fi

echo ""
if [[ "${fail}" -gt 0 ]]; then
  log_err "Some checks failed."
  log_info "If the gateway is not reachable: make start"
  log_info "Then: make register (and restart Cursor if using the wrapper)."
  exit 1
fi
log_line
log_ok "All checks passed."
log_info "If context-forge still shows Error:"
log_info "  → Fully quit Cursor (Cmd+Q / Alt+F4) and reopen. Reload Window is not enough."
log_info "  → If logs show 'No server info found': run make register (refreshes URL); or set REGISTER_CURSOR_MCP_SERVER_NAME=cursor-default in .env, run make register, then quit and reopen Cursor."
