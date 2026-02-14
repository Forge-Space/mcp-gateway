#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
normalize_gateway_url || true
COMPOSE=$(compose_cmd)
export COMPOSE
JWT=$(get_jwt) || { log_err "Failed to generate JWT. Is the gateway running? Try: docker compose ps gateway"; exit 1; }

log_section "Virtual MCP servers"
log_step "Fetching from $GATEWAY_URL..."

resp=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 15 \
  -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers?limit=0&include_pagination=false" 2>&1) || true
code=$(parse_http_code "$resp")
body=$(parse_http_body "$resp")

if [[ "$code" == "500" ]] || [[ "$code" == "502" ]] || [[ "$code" == "503" ]]; then
  resp_alt=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 15 \
    -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers" 2>&1) || true
  code_alt=$(parse_http_code "$resp_alt")
  if [[ "$code_alt" == "200" ]]; then
    code="200"
    body=$(parse_http_body "$resp_alt")
  fi
fi

if [[ "$code" != "200" ]]; then
  if [[ -z "$code" || "$code" == "000" ]]; then
    log_err "Gateway not reachable at $GATEWAY_URL. Start it with: make start"
    log_info "Then create virtual servers with: make register"
  else
    log_err "GET /servers returned HTTP $code"
    if [[ "$code" =~ ^5 ]]; then
      log_info "Check gateway logs: docker compose logs gateway"
    fi
  fi
  if [[ -n "$body" ]]; then
    if [[ "$code" =~ ^5 ]]; then
      echo "$body"
    else
      echo "$body" | head -20
    fi
  fi
  exit 1
fi

if ! command -v jq &>/dev/null; then
  log_ok "Servers loaded (install jq for table format)."
  echo "$body"
  exit 0
fi

servers_json=$(echo "$body" | jq -c 'if type == "array" then . else .servers? // [] end' 2>/dev/null)
count=$(echo "$servers_json" | jq 'length' 2>/dev/null)
log_ok "Found $count virtual server(s)."
log_line

if [[ "$count" -eq 0 ]]; then
  log_info "Create one with: make register (or POST /servers via API)."
  exit 0
fi

printf "%-38s %-24s %s\n" "ID" "NAME" "TOOLS"
printf "%-38s %-24s %s\n" "--------------------------------------" "------------------------" "-----"
while IFS= read -r line; do
  id=$(echo "$line" | jq -r '.id // empty')
  name=$(echo "$line" | jq -r '.name // "(unnamed)"')
  tools_attr=$(echo "$line" | jq -r '[.associated_tools[]? // .associatedTools[]? // empty] | length' 2>/dev/null)
  if [[ -z "$tools_attr" || "$tools_attr" == "null" ]]; then
    tool_count=$(curl -s --connect-timeout 2 --max-time 5 -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers/${id}" 2>/dev/null | jq -r '[.associated_tools[]? // .associatedTools[]? // empty] | length' 2>/dev/null || echo "?")
  else
    tool_count="$tools_attr"
  fi
  printf "%-38s %-24s %s\n" "$id" "$name" "$tool_count"
done < <(echo "$servers_json" | jq -c '.[]')

url_file="$REPO_ROOT/data/.cursor-mcp-url"
if [[ -f "$url_file" && -s "$url_file" ]]; then
  cursor_url=$(head -n1 "$url_file" | tr -d '\r\n')
  if [[ "$cursor_url" =~ /servers/([a-f0-9-]+)/mcp ]]; then
    log_line
    log_info "Cursor URL points to: .../servers/${BASH_REMATCH[1]}/mcp"
  fi
fi
