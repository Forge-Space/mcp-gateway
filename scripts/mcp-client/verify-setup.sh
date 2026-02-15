#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err ".env not found. Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

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

log_section "MCP Client (wrapper) setup"
log_step "Checking environment..."

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
normalize_gateway_url || true
if [[ "$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$GATEWAY_URL/health" 2>/dev/null || true)" == "200" ]]; then
  check 1 "Gateway reachable at $GATEWAY_URL (health=200)"
else
  check 0 "Gateway reachable at $GATEWAY_URL. Run: make start"
fi

url_file="$REPO_ROOT/data/.mcp-client-url"
if [[ ! -f "$url_file" || ! -s "$url_file" ]]; then
  check 0 "data/.mcp-client-url missing or empty (run: make register)"
  echo ""
  log_info "Next: make start && make register && restart your IDE"
  exit 1
fi
MCP_URL=$(head -n1 "$url_file" | tr -d '\r\n')
check 1 "data/.mcp-client-url exists and has URL"

if [[ ! "$MCP_URL" =~ /servers/([a-f0-9-]+)/mcp ]]; then
  check 0 "URL in .mcp-client-url does not look like .../servers/UUID/mcp"
  echo ""
  log_info "Next: make register (to refresh the URL)"
  exit 1
fi
SERVER_ID="${BASH_REMATCH[1]}"

JWT=$(get_jwt) || true
if [[ -z "$JWT" ]]; then
  check 0 "Could not generate JWT (need PyJWT or running gateway container)"
else
  check 1 "JWT generated"
fi

CONTEXT_FORGE_IMAGE="${CONTEXT_FORGE_IMAGE:-ghcr.io/ibm/mcp-context-forge:1.0.0-BETA-2}"
if docker image inspect "$CONTEXT_FORGE_IMAGE" &>/dev/null; then
  check 1 "Context Forge image present ($CONTEXT_FORGE_IMAGE)"
  GATEWAY_FROM_DOCKER_URL="http://host.docker.internal:${PORT:-4444}"
  add_host_args=()
  [[ "$(uname -s)" == "Linux" ]] && add_host_args=(--add-host=host.docker.internal:host-gateway)
  if docker run --rm "${add_host_args[@]}" "$CONTEXT_FORGE_IMAGE" python3 -c "
import urllib.request, sys
try:
  r = urllib.request.urlopen('$GATEWAY_FROM_DOCKER_URL/health', timeout=8)
  sys.exit(0 if r.getcode() == 200 else 1)
except Exception:
  sys.exit(1)
" 2>/dev/null; then
    check 1 "Gateway reachable from Docker (host.docker.internal:${PORT:-4444})"
  else
    log_warn "Gateway not reachable from Docker (wrapper runs in container). If your IDE shows errors, ensure gateway is running and host.docker.internal works (Linux: Docker 20.10+)."
    ok=$((ok + 1))
  fi
else
  check 0 "Context Forge image missing (first IDE connection may timeout). Run: make mcp-client-pull"
fi

if [[ -n "$JWT" ]]; then
  servers_resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 15 \
    -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers?limit=0&include_pagination=false" 2>/dev/null)
  servers_code=$(parse_http_code "$servers_resp")
  servers_body=$(parse_http_body "$servers_resp")
  if [[ "$servers_code" != "200" ]]; then
    check 0 "GET /servers returned $servers_code (expected 200)"
  else
    found=$(echo "$servers_body" | jq -r --arg id "$SERVER_ID" 'if type == "array" then .[] else .servers[]? // empty end | select(.id == $id) | .id' 2>/dev/null | head -1)
    if [[ "$found" == "$SERVER_ID" ]]; then
      check 1 "Server ID $SERVER_ID exists on gateway"
      server_json=$(curl -s --connect-timeout 5 --max-time 10 -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers/${SERVER_ID}" 2>/dev/null)
      server_name=$(echo "$server_json" | jq -r '.name // empty' 2>/dev/null)
      tool_count=$(echo "$server_json" | jq -r '[.associated_tools[]? // .associatedTools[]? // empty] | length' 2>/dev/null | tr -d '\n\r')
      if [[ -n "$server_name" ]]; then
        if [[ "$tool_count" =~ ^[0-9]+$ ]]; then
          log_info "  → URL points to server \"$server_name\" ($tool_count tools)."
        else
          log_info "  → URL points to server \"$server_name\"."
        fi
        if [[ "$tool_count" =~ ^[0-9]+$ ]] && [[ "$tool_count" -eq 0 ]]; then
          if [[ "$server_name" == "mcp-router" ]]; then
            check 0 "mcp-router has 0 tools; set GATEWAY_JWT in .env (run make jwt, paste token), then make start and make register"
          else
            log_warn "  → Server has no tools. For mcp-router: set GATEWAY_JWT in .env, run make start, then make register."
          fi
        fi
        if [[ "$server_name" == "mcp-default" ]]; then
          log_info "  → To use default mcp-router (tool-router), remove REGISTER_MCP_CLIENT_SERVER_NAME from .env and run make register."
        fi
      fi
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
log_info "  → Fully quit your IDE (Cmd+Q / Alt+F4) and reopen. Reload Window is not enough."
log_info "  → To use default mcp-router: remove REGISTER_MCP_CLIENT_SERVER_NAME from .env, run make register, then quit and reopen your IDE."
log_info "  → If logs show 'No server info found': ensure gateway is reachable from Docker (host.docker.internal:${PORT:-4444}); run make start, make register, then quit and reopen your IDE."
log_info "  → If logs show 'Request timed out' (-32001): run make mcp-client-pull once, add timeout in mcp.json (make use-mcp-client-wrapper sets 120s), then quit and reopen your IDE."
