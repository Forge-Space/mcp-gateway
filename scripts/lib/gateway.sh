# Gateway helpers: Docker Compose, JWT, URL normalization, HTTP parse, Cursor MCP key.
# Requires SCRIPT_DIR, REPO_ROOT (from bootstrap) and env loaded (PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY).

detect_docker_compose_command() {
  if docker compose version &>/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose &>/dev/null; then
    echo "docker-compose"
  else
    echo ""
  fi
}

generate_or_retrieve_jwt_token() {
  local jwt_token
  jwt_token=$(python3 "$SCRIPT_DIR/create_jwt_token_standalone.py" 2>/dev/null) || true
  jwt_token=$(echo "$jwt_token" | tr -d '[:space:]')
  if [[ -n "$jwt_token" ]] && [[ "$jwt_token" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
    echo "$jwt_token"
    return 0
  fi
  local compose_command="${COMPOSE:-$(detect_docker_compose_command)}"
  local container_name="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if [[ -n "$compose_command" ]] && $compose_command ps gateway -q 2>/dev/null | grep -q .; then
    jwt_token=$($compose_command exec -T gateway python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null) || true
    jwt_token=$(echo "$jwt_token" | tr -d '[:space:]')
  elif docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$container_name"; then
    jwt_token=$(docker exec "$container_name" python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null) || true
    jwt_token=$(echo "$jwt_token" | tr -d '[:space:]')
  fi
  if [[ -n "$jwt_token" ]] && [[ "$jwt_token" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
    echo "$jwt_token"
    return 0
  fi
  return 1
}

normalize_gateway_url() {
  GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
  local http_status_code
  http_status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$GATEWAY_URL/health" 2>/dev/null || true)
  if [[ "$http_status_code" == "200" ]]; then
    return 0
  fi
  if [[ "$GATEWAY_URL" =~ 127\.0\.0\.1 ]]; then
    local alternative_url="${GATEWAY_URL//127.0.0.1/localhost}"
    http_status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$alternative_url/health" 2>/dev/null || true)
    [[ "$http_status_code" == "200" ]] && GATEWAY_URL="$alternative_url"
  elif [[ "$GATEWAY_URL" =~ localhost ]]; then
    local alternative_url="${GATEWAY_URL//localhost/127.0.0.1}"
    http_status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$alternative_url/health" 2>/dev/null || true)
    [[ "$http_status_code" == "200" ]] && GATEWAY_URL="$alternative_url"
  fi
  [[ "$http_status_code" == "200" ]]
}

wait_for_healthy_gateway_status() {
  local base_url="$1" max_wait_seconds="${2:-90}" check_interval_seconds="${3:-3}"
  local elapsed_seconds=0 http_status_code=""
  while [[ "$elapsed_seconds" -lt "$max_wait_seconds" ]]; do
    http_status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$base_url/health" 2>/dev/null || true)
    if [[ "$http_status_code" == "200" ]]; then
      printf '\r  OK after %ds.    \n' "$elapsed_seconds" >&2
      echo "$http_status_code"
      return 0
    fi
    printf '\r  %ds elapsed (waiting for 200)...   ' "$elapsed_seconds" >&2
    sleep "$check_interval_seconds"
    elapsed_seconds=$((elapsed_seconds + check_interval_seconds))
  done
  echo >&2
  echo "${http_status_code:-000}"
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
fetch_registered_servers_list() {
  local retry_delay_seconds="${REGISTER_GET_SERVERS_RETRY_DELAY:-5}"
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
  if [[ "$servers_code" != "200" ]] && [[ "$retry_delay_seconds" -gt 0 ]] && { [[ "$servers_code" =~ ^5 ]] || [[ "$servers_code" == "408" ]]; }; then
    local _
    for _ in 1 2; do
      sleep "$retry_delay_seconds"
      servers_resp=$(curl -s -w "\n%{http_code}" --connect-timeout 10 --max-time 30 \
        -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers" 2>/dev/null)
      servers_code=$(parse_http_code "$servers_resp")
      # shellcheck disable=SC2034
      servers_body=$(parse_http_body "$servers_resp")
      [[ "$servers_code" == "200" ]] && return 0
    done
  fi
  return 0
}

get_mcp_client_key() {
  local mcp_config_file="${1:-${MCP_CLIENT_CONFIG:-$HOME/.cursor/mcp.json}}"
  local config_key
  for config_key in ${MCP_CLIENT_KEY:-mcp-gateway context-forge user-context-forge}; do
    if jq -e --arg config_key "$config_key" '.mcpServers[$config_key] // .[$config_key]' "$mcp_config_file" &>/dev/null; then
      echo "$config_key"
      return 0
    fi
  done
  return 1
}

# Backward compatibility alias
get_context_forge_key() {
  get_mcp_client_key "$@"
}
