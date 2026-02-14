# Gateway helpers: Docker Compose, JWT, URL normalization, HTTP parse, Cursor MCP key.
# Requires SCRIPT_DIR, REPO_ROOT (from bootstrap) and env loaded (PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY).

compose_cmd() {
  if docker compose version &>/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose &>/dev/null; then
    echo "docker-compose"
  else
    echo ""
  fi
}

get_jwt() {
  local j
  j=$(python3 "$SCRIPT_DIR/create_jwt_token_standalone.py" 2>/dev/null) || true
  j=$(echo "$j" | tr -d '[:space:]')
  if [[ -n "$j" ]] && [[ "$j" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
    echo "$j"
    return 0
  fi
  local compose="${COMPOSE:-$(compose_cmd)}"
  local container="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if [[ -n "$compose" ]] && $compose ps gateway -q 2>/dev/null | grep -q .; then
    j=$($compose exec -T gateway python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null) || true
    j=$(echo "$j" | tr -d '[:space:]')
  elif docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$container"; then
    j=$(docker exec "$container" python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null) || true
    j=$(echo "$j" | tr -d '[:space:]')
  fi
  if [[ -n "$j" ]] && [[ "$j" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
    echo "$j"
    return 0
  fi
  return 1
}

normalize_gateway_url() {
  GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$GATEWAY_URL/health" 2>/dev/null || true)
  if [[ "$code" == "200" ]]; then
    return 0
  fi
  if [[ "$GATEWAY_URL" =~ 127\.0\.0\.1 ]]; then
    local alt="${GATEWAY_URL//127.0.0.1/localhost}"
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$alt/health" 2>/dev/null || true)
    [[ "$code" == "200" ]] && GATEWAY_URL="$alt"
  elif [[ "$GATEWAY_URL" =~ localhost ]]; then
    local alt="${GATEWAY_URL//localhost/127.0.0.1}"
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$alt/health" 2>/dev/null || true)
    [[ "$code" == "200" ]] && GATEWAY_URL="$alt"
  fi
  [[ "$code" == "200" ]]
}

wait_for_health() {
  local base="$1" limit="${2:-90}" interval="${3:-3}"
  local elapsed=0 code=""
  while [[ "$elapsed" -lt "$limit" ]]; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$base/health" 2>/dev/null || true)
    if [[ "$code" == "200" ]]; then
      printf '\r  OK after %ds.    \n' "$elapsed" >&2
      echo "$code"
      return 0
    fi
    printf '\r  %ds elapsed (waiting for 200)...   ' "$elapsed" >&2
    sleep "$interval"
    elapsed=$((elapsed + interval))
  done
  echo >&2
  echo "${code:-000}"
  return 1
}

parse_http_code() {
  echo "$1" | tail -n1
}

parse_http_body() {
  echo "$1" | sed '$d'
}

# Fetches GET /servers with retries: first with ?limit=0&include_pagination=false,
# then plain /servers; if still non-200 and 5xx/408, delayed retries (2 extra attempts).
# Sets servers_code and servers_body in caller scope. Requires JWT and GATEWAY_URL.
# REGISTER_GET_SERVERS_RETRY_DELAY (default 5); set to 0 to disable delayed retries.
fetch_servers_list() {
  local delay="${REGISTER_GET_SERVERS_RETRY_DELAY:-5}"
  servers_resp=$(curl -s -w "\n%{http_code}" --connect-timeout 10 --max-time 30 \
    -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers?limit=0&include_pagination=false" 2>/dev/null)
  servers_code=$(parse_http_code "$servers_resp")
  # shellcheck disable=SC2034
  servers_body=$(parse_http_body "$servers_resp")
  if [[ "$servers_code" != "200" ]]; then
    servers_resp=$(curl -s -w "\n%{http_code}" --connect-timeout 10 --max-time 30 \
      -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers" 2>/dev/null)
    servers_code=$(parse_http_code "$servers_resp")
    # shellcheck disable=SC2034
    servers_body=$(parse_http_body "$servers_resp")
  fi
  if [[ "$servers_code" != "200" ]] && [[ "$delay" -gt 0 ]] && { [[ "$servers_code" =~ ^5 ]] || [[ "$servers_code" == "408" ]]; }; then
    local _
    for _ in 1 2; do
      sleep "$delay"
      servers_resp=$(curl -s -w "\n%{http_code}" --connect-timeout 10 --max-time 30 \
        -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers" 2>/dev/null)
      servers_code=$(parse_http_code "$servers_resp")
      _=$(parse_http_body "$servers_resp")
      [[ "$servers_code" == "200" ]] && return 0
    done
  fi
  return 0
}

get_context_forge_key() {
  local mcp_json="${1:-${CURSOR_MCP_JSON:-$HOME/.cursor/mcp.json}}"
  local k
  for k in ${CONTEXT_FORGE_MCP_KEY:-context-forge user-context-forge}; do
    if jq -e --arg k "$k" '.mcpServers[$k] // .[$k]' "$mcp_json" &>/dev/null; then
      echo "$k"
      return 0
    fi
  done
  return 1
}
