#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

log_section "Register gateways"
log_step "Checking environment..."

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
max_wait="${REGISTER_GATEWAY_MAX_WAIT:-90}"
interval=3
if [[ "$GATEWAY_URL" =~ 127\.0\.0\.1 ]]; then
  first_url="${GATEWAY_URL//127.0.0.1/localhost}"
  second_url="$GATEWAY_URL"
elif [[ "$GATEWAY_URL" =~ localhost ]]; then
  first_url="$GATEWAY_URL"
  second_url="${GATEWAY_URL//localhost/127.0.0.1}"
else
  first_url="$GATEWAY_URL"
  second_url=""
fi

log_info "Waiting for gateway at $first_url (up to ${max_wait}s)..."
code=$(wait_for_health "$first_url" "$max_wait" "$interval") || true
if [[ "$code" != "200" ]] && [[ -n "$second_url" ]]; then
  log_info "Trying alternate URL: $second_url"
  code=$(wait_for_health "$second_url" "$max_wait" "$interval") || true
  [[ "$code" == "200" ]] && GATEWAY_URL="$second_url"
elif [[ "$code" == "200" ]] && [[ "$first_url" != "$GATEWAY_URL" ]]; then
  GATEWAY_URL="$first_url"
fi
if [[ "$code" != "200" ]]; then
  log_err "Gateway not reachable at $GATEWAY_URL (health got ${code} after ${max_wait}s)."
  log_err "Start with ./start.sh. If already started: docker compose ps gateway && docker compose logs gateway"
  exit 1
fi
log_ok "Gateway ready at $GATEWAY_URL"

write_cursor_mcp_url() {
  local id="$1" name="$2"
  local want="${REGISTER_CURSOR_MCP_SERVER_NAME:-cursor-router}"
  if [[ "$name" != "$want" ]]; then
    return
  fi
  mkdir -p "$REPO_ROOT/data"
  printf '%s' "http://host.docker.internal:${PORT:-4444}/servers/$id/mcp" > "$REPO_ROOT/data/.cursor-mcp-url"
  CURSOR_MCP_URL_WRITTEN="$name|$id"
}

if [[ -n "${REGISTER_WAIT_SECONDS:-}" ]] && [[ "${REGISTER_WAIT_SECONDS}" -gt 0 ]] 2>/dev/null; then
  log_info "Waiting ${REGISTER_WAIT_SECONDS}s for translate containers to be ready..."
  left="${REGISTER_WAIT_SECONDS}"
  while [[ "$left" -gt 0 ]]; do
    printf "\r  %ds remaining...   " "$left"
    if [[ "$left" -ge 5 ]]; then step=5; else step=$left; fi
    sleep "$step"
    left=$((left - step))
  done
  echo ""
fi

log_step "Generating JWT for admin API..."
COMPOSE=$(compose_cmd)
export COMPOSE
JWT=$(get_jwt) || { log_err "Failed to generate JWT."; exit 1; }
log_ok "JWT generated."

infer_transport() {
  local url="$1"
  if [[ "$url" == *"/sse"* ]]; then
    echo "SSE"
  elif [[ "$url" == *"/mcp"* ]]; then
    echo "STREAMABLEHTTP"
  else
    echo ""
  fi
}

is_local_sse() {
  [[ "$1" =~ ^https?://[^./:]+:(801[3-9]|802[0-9])/sse$ ]]
}

register() {
  local name="$1" url="$2" transport="$3" retried="${4:-0}"
  if [[ "$url" =~ ^https?://([^:/]+):[0-9]+ ]]; then
    local host="${BASH_REMATCH[1]}"
    if [[ -n "$COMPOSE" ]] && ! $COMPOSE ps "$host" -q 2>/dev/null | grep -q .; then
      log_warn "SKIP $name ($host not running; start with ./start.sh)"
      return
    fi
  fi
  if [[ -z "$transport" ]]; then
    transport=$(infer_transport "$url")
  fi
  local json
  if [[ -n "$transport" ]] && [[ "$transport" =~ ^(SSE|STREAMABLEHTTP|STDIO|WEBSOCKET)$ ]]; then
    json=$(printf '{"name":"%s","url":"%s","transport":"%s"}' "$name" "$url" "$transport")
  else
    json=$(printf '{"name":"%s","url":"%s"}' "$name" "$url")
  fi
  local out
  out=$(curl -s -w "\n%{http_code}" --connect-timeout 10 --max-time 45 \
    -X POST -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
    -d "$json" "$GATEWAY_URL/gateways" 2>/dev/null)
  local code
  code=$(parse_http_code "$out")
  if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then
    log_ok "$name"
    return
  fi
  body=$(parse_http_body "$out")
  msg=$(echo "$body" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p')
  detail=$(echo "$body" | sed -n 's/.*"detail":"\([^"]*\)".*/\1/p')
  if [[ "$msg" =~ already\ exists ]] || [[ "$detail" =~ already\ exists ]]; then
    log_ok "$name (already registered)"
    return
  fi
  if [[ $retried -eq 0 ]] && is_local_sse "$url" && \
    { [[ "$msg" =~ [Uu]nable\ to\ connect ]] || [[ "$detail" =~ [Uu]nable\ to\ connect ]] || \
      [[ "$msg" =~ [Uu]nexpected\ error ]] || [[ "$detail" =~ [Uu]nexpected\ error ]]; }; then
    log_info "$name: first attempt failed, retrying in 15s..."
    sleep 15
    register "$name" "$url" "$transport" 1
    return
  fi
  log_fail "$name ($url)"
  if [[ -n "${REGISTER_VERBOSE:-}" ]]; then
    echo "$body"
  else
    [[ -n "$msg" ]] && log_info "$msg"
    [[ -n "$detail" ]] && log_info "detail: $detail"
  fi
  if is_local_sse "$url"; then
    HAS_LOCAL_FAIL=1
    log_info "→ docker compose logs gateway; docker compose logs <service>"
  fi
}

create_or_update_virtual_server() {
  local server_name="$1" desc="$2" tool_ids_json="$3" existing_id="${4:-}"
  if [[ -n "$existing_id" ]]; then
    local put_body put_resp put_code
    put_body=$(jq -n --argjson ids "$tool_ids_json" '{name: $name, description: $desc, associated_tools: $ids}' --arg name "$server_name" --arg desc "$desc")
    put_resp=$(curl -s -w "\n%{http_code}" -X PUT -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
      -d "$put_body" "${GATEWAY_URL}/servers/${existing_id}" 2>/dev/null)
    put_code=$(parse_http_code "$put_resp")
    if [[ "$put_code" =~ ^2[0-9][0-9]$ ]]; then
      log_ok "virtual server updated: $server_name ($existing_id)"
      log_info "Cursor (mcp): $GATEWAY_URL/servers/$existing_id/mcp"
      log_info "Cursor (sse): $GATEWAY_URL/servers/$existing_id/sse"
      write_cursor_mcp_url "$existing_id" "$server_name"
      return 0
    fi
    log_warn "virtual server update failed: $server_name (HTTP $put_code)"
    [[ "${REGISTER_VERBOSE:-0}" -eq 1 ]] && parse_http_body "$put_resp" | head -5
    return 0
  fi

  local post_body post_resp post_code post_body_resp new_id
  post_body=$(jq -n --argjson ids "$tool_ids_json" '{server: {name: $name, description: $desc, associated_tools: $ids}}' --arg name "$server_name" --arg desc "$desc")
  post_resp=$(curl -s -w "\n%{http_code}" -X POST -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
    -d "$post_body" "${GATEWAY_URL}/servers" 2>/dev/null)
  post_code=$(parse_http_code "$post_resp")
  post_body_resp=$(parse_http_body "$post_resp")
  if [[ "$post_code" =~ ^2[0-9][0-9]$ ]]; then
    new_id=$(echo "$post_body_resp" | jq -r '.id // empty' 2>/dev/null)
    if [[ -n "$new_id" ]]; then
      log_ok "virtual server created: $server_name ($new_id)"
      log_info "Cursor (mcp): $GATEWAY_URL/servers/$new_id/mcp"
      log_info "Cursor (sse): $GATEWAY_URL/servers/$new_id/sse"
      write_cursor_mcp_url "$new_id" "$server_name"
    fi
    return 0
  fi

  log_warn "virtual server create failed: $server_name (HTTP $post_code)"
  if [[ "$post_code" == "400" ]]; then
    if echo "$post_body_resp" | grep -q "transaction is inactive"; then
      echo "$post_body_resp" | head -5
      log_info "Workaround: create virtual servers in Admin UI ($GATEWAY_URL) or retry 'make register' after a minute. See docs/ADMIN_UI_MANUAL_REGISTRATION.md"
      return 1
    fi
    echo "$post_body_resp" | head -15
    local post_body_flat post_resp2 post_code2 post_body_resp2
    post_body_flat=$(jq -n --argjson ids "$tool_ids_json" '{name: $name, description: $desc, associatedTools: $ids}' --arg name "$server_name" --arg desc "$desc")
    post_resp2=$(curl -s -w "\n%{http_code}" -X POST -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
      -d "$post_body_flat" "${GATEWAY_URL}/servers" 2>/dev/null)
    post_code2=$(parse_http_code "$post_resp2")
    post_body_resp2=$(parse_http_body "$post_resp2")
    if [[ "$post_code2" =~ ^2[0-9][0-9]$ ]]; then
      new_id=$(echo "$post_body_resp2" | jq -r '.id // empty' 2>/dev/null)
      if [[ -n "$new_id" ]]; then
        log_ok "virtual server created: $server_name ($new_id) [flat body]"
        log_info "Cursor (mcp): $GATEWAY_URL/servers/$new_id/mcp"
        log_info "Cursor (sse): $GATEWAY_URL/servers/$new_id/sse"
        write_cursor_mcp_url "$new_id" "$server_name"
      fi
    fi
  elif [[ "$post_code" =~ ^5 ]] || [[ "${REGISTER_VERBOSE:-0}" -eq 1 ]]; then
    echo "$post_body_resp" | head -10
    [[ "$post_code" =~ ^5 ]] && log_info "Check gateway logs: docker compose logs gateway"
  fi
  return 0
}

HAS_LOCAL_FAIL=0
if [[ -n "$EXTRA_GATEWAYS" ]]; then
  log_step "Registering gateways from EXTRA_GATEWAYS..."
  while IFS= read -r line; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IFS='|' read -r name url transport <<< "$line"
    transport=$(echo "${transport:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    register "$name" "$url" "$transport"
  done <<< "$(echo "$EXTRA_GATEWAYS" | tr ',' '\n')"
fi

gateways_file="${CONFIG_DIR:-$SCRIPT_DIR}/gateways.txt"
if [[ -f "$gateways_file" ]]; then
  log_step "Registering gateways from $gateways_file..."
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IFS='|' read -r name url transport <<< "$line"
    transport=$(echo "${transport:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    register "$name" "$url" "$transport"
  done < "$gateways_file"
fi

if [[ "${REGISTER_VIRTUAL_SERVER:-true}" =~ ^(true|1|yes)$ ]] && command -v jq &>/dev/null; then
  log_step "Syncing tools and updating virtual server(s)..."
  sleep "${REGISTER_VIRTUAL_SERVER_DELAY:-3}"

  # Retry logic to ensure tools are fully synced
  tools_retry_count=0
  tools_retry_max="${REGISTER_TOOLS_SYNC_RETRIES:-3}"
  tools_retry_delay="${REGISTER_TOOLS_SYNC_DELAY:-5}"
  expected_gateways=0

  # Count expected gateways from config
  [[ -n "$EXTRA_GATEWAYS" ]] && expected_gateways=$((expected_gateways + $(echo "$EXTRA_GATEWAYS" | tr ',' '\n' | grep -v '^[[:space:]]*$' | grep -v '^#' | wc -l)))
  [[ -f "$gateways_file" ]] && expected_gateways=$((expected_gateways + $(grep -v '^[[:space:]]*$' "$gateways_file" | grep -v '^#' | wc -l)))

  while [[ $tools_retry_count -lt $tools_retry_max ]]; do
    tools_resp=$(curl -s -w "\n%{http_code}" --connect-timeout 10 --max-time 60 \
      -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/tools?limit=0&include_pagination=false" 2>/dev/null)
    tools_code=$(parse_http_code "$tools_resp")
    tools_body=$(parse_http_body "$tools_resp")

    if [[ "$tools_code" == "200" ]] && [[ -n "$tools_body" ]]; then
      tool_count=$(echo "$tools_body" | jq -r 'if type == "array" then length else (.tools? // [] | length) end' 2>/dev/null || echo "0")
      if [[ "$tool_count" -gt 0 ]] && [[ "$expected_gateways" -gt 0 ]] && [[ "$tool_count" -ge "$expected_gateways" ]]; then
        log_info "Tools synced: $tool_count tools from $expected_gateways gateways"
        break
      elif [[ "$tool_count" -gt 0 ]]; then
        log_info "Tools synced: $tool_count tools available"
        break
      fi
    fi

    tools_retry_count=$((tools_retry_count + 1))
    if [[ $tools_retry_count -lt $tools_retry_max ]]; then
      log_info "Waiting for tools to sync (attempt $((tools_retry_count + 1))/$tools_retry_max)..."
      sleep "$tools_retry_delay"
    fi
  done

  tools_code=$(parse_http_code "$tools_resp")
  tools_body=$(parse_http_body "$tools_resp")
  if [[ "$tools_code" != "200" ]] || [[ -z "$tools_body" ]]; then
    :
  elif [[ -f "${CONFIG_DIR:-$SCRIPT_DIR}/virtual-servers.txt" ]]; then
    tools_arr=$(echo "$tools_body" | jq -c 'if type == "array" then . else .tools? // [] end' 2>/dev/null)
    servers_code=""
    servers_body=""
    fetch_servers_list
    if [[ "$servers_code" != "200" ]]; then
      if [[ "${REGISTER_VIRTUAL_SERVER_CREATE_WHEN_GET_FAILS:-}" =~ ^(true|1|yes)$ ]]; then
        log_warn "GET /servers returned $servers_code; attempting create-only (no update, possible duplicates if run again)."
        servers_body="[]"
      else
        log_warn "GET /servers returned $servers_code; skipping virtual server create/update (gateway cannot list servers)."
        log_info "Create virtual servers in Admin UI ($GATEWAY_URL) or retry 'make register' later. See docs/ADMIN_UI_MANUAL_REGISTRATION.md"
      fi
    fi
    if [[ "$servers_code" == "200" ]] || [[ "${REGISTER_VIRTUAL_SERVER_CREATE_WHEN_GET_FAILS:-}" =~ ^(true|1|yes)$ ]]; then
      used_tool_sets=""
      while IFS= read -r line || [[ -n "$line" ]]; do
      line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      [[ -z "$line" || "$line" =~ ^# ]] && continue
      server_name=$(echo "$line" | cut -d'|' -f1)
      gateways_str=$(echo "$line" | cut -d'|' -f2- | tr -d ' ')
      [[ -z "$server_name" || -z "$gateways_str" ]] && continue
      gates_json=$(echo "$gateways_str" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length > 0))' 2>/dev/null)
      [[ -z "$gates_json" || "$gates_json" == "null" ]] && continue
      tool_ids_json=$(echo "$tools_arr" | jq -c --argjson gates "$gates_json" '
        map(select(
          (.gatewaySlug // .gateway_slug // .gateway.slug // .gateway.name // "") as $g
          | ($g != "" and ($gates | index($g)) != null)
        ))
        | .[0:60]
        | [.[].id]
      ' 2>/dev/null)
      if [[ -z "$tool_ids_json" || "$tool_ids_json" == "[]" ]]; then
        log_warn "No tools for server $server_name (gateways: $gateways_str)"
        continue
      fi
      tool_set_sig=$(echo "$tool_ids_json" | jq -c 'sort' 2>/dev/null)
      if [[ -n "$used_tool_sets" ]] && echo "$used_tool_sets" | grep -qFx "$tool_set_sig"; then
        log_warn "Skipping $server_name (same tool set as an existing server)"
        continue
      fi
      used_tool_sets="${used_tool_sets:+$used_tool_sets$'\n'}$tool_set_sig"
      desc="Tools from: ${gateways_str//,/, }"
      existing_id=$(echo "$servers_body" | jq -r --arg n "$server_name" 'if type == "array" then .[] else .servers[]? // empty end | select(.name == $n) | .id' 2>/dev/null | head -1)
      [[ "$existing_id" == "null" ]] && existing_id=""
      create_or_update_virtual_server "$server_name" "$desc" "$tool_ids_json" "$existing_id" || break
      done < "${CONFIG_DIR:-$SCRIPT_DIR}/virtual-servers.txt"
    fi
  else
    tool_ids=$(echo "$tools_body" | jq -r 'if type == "array" then .[] else .tools[]? // empty end | .id // empty' 2>/dev/null)
    if [[ -n "$tool_ids" ]]; then
      tool_ids_json=$(echo "$tool_ids" | jq -R -s -c 'split("\n") | map(select(length > 0))')
      servers_code=""
      servers_body=""
      fetch_servers_list
      if [[ "$servers_code" != "200" ]]; then
        if [[ "${REGISTER_VIRTUAL_SERVER_CREATE_WHEN_GET_FAILS:-}" =~ ^(true|1|yes)$ ]]; then
          log_warn "GET /servers returned $servers_code; attempting create-only (no update, possible duplicates if run again)."
          servers_body="[]"
        else
          log_warn "GET /servers returned $servers_code; skipping virtual server create/update."
          log_info "Create virtual servers in Admin UI ($GATEWAY_URL) or retry 'make register' later. See docs/ADMIN_UI_MANUAL_REGISTRATION.md"
        fi
      fi
      if [[ "$servers_code" == "200" ]] || [[ "${REGISTER_VIRTUAL_SERVER_CREATE_WHEN_GET_FAILS:-}" =~ ^(true|1|yes)$ ]]; then
        server_name="${REGISTER_VIRTUAL_SERVER_NAME:-default}"
        existing_id=$(echo "$servers_body" | jq -r --arg n "$server_name" 'if type == "array" then .[] else .servers[]? // empty end | select(.name == $n) | .id' 2>/dev/null | head -1)
        [[ "$existing_id" == "null" ]] && existing_id=""
        create_or_update_virtual_server "$server_name" "All registered tools" "$tool_ids_json" "$existing_id" || true
      fi
    fi
  fi
  if [[ -n "${CURSOR_MCP_URL_WRITTEN:-}" ]]; then
    log_info "data/.cursor-mcp-url → ${CURSOR_MCP_URL_WRITTEN%|*} (wrapper uses this server)"
  fi
fi

prompts_file="${CONFIG_DIR:-$SCRIPT_DIR}/prompts.txt"
if [[ "${REGISTER_PROMPTS:-false}" =~ ^(true|1|yes)$ ]] && [[ -f "$prompts_file" ]]; then
  log_step "Registering prompts from $prompts_file..."
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    name=$(echo "$line" | cut -d'|' -f1)
    desc=$(echo "$line" | cut -d'|' -f2)
    template=$(echo "$line" | cut -d'|' -f3- | sed 's/\\n/\n/g')
    if [[ -z "$name" || -z "$template" ]]; then continue; fi
    args_json=$(echo "$template" | grep -oE '\{\{[^}]+\}\}' | sed 's/{{//;s/}}//' | sort -u | while read -r arg; do
      echo "{\"name\":\"$arg\",\"description\":\"$arg\",\"required\":true}"
    done | jq -s . 2>/dev/null)
    [[ -z "$args_json" ]] && args_json="[]"
    payload=$(jq -n --arg n "$name" --arg d "$desc" --arg t "$template" --argjson a "$args_json" '{prompt: {name: $n, description: $d, template: $t, arguments: $a}}')
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" -d "$payload" "$GATEWAY_URL/prompts" 2>/dev/null)
    if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then log_ok "prompt $name"; fi
  done < "$prompts_file"
fi

resources_file="${CONFIG_DIR:-$SCRIPT_DIR}/resources.txt"
if [[ "${REGISTER_RESOURCES:-false}" =~ ^(true|1|yes)$ ]] && [[ -f "$resources_file" ]]; then
  log_step "Registering resources from $resources_file..."
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IFS='|' read -r name uri desc mime <<< "$line"
    desc=$(echo "${desc:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    mime=$(echo "${mime:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    if [[ -z "$name" || -z "$uri" ]]; then continue; fi
    payload=$(jq -n --arg n "$name" --arg u "$uri" --arg d "$desc" --arg m "${mime:-text/plain}" '{resource: {name: $n, uri: $u, description: $desc, mime_type: $m}}')
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" -d "$payload" "$GATEWAY_URL/resources" 2>/dev/null)
    if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then log_ok "resource $name"; fi
  done < "$resources_file"
fi

if [[ -z "$EXTRA_GATEWAYS" && ! -f "$gateways_file" ]]; then
  log_warn "No gateways to register. Set EXTRA_GATEWAYS in .env or add lines to $gateways_file (Name|URL|Transport)."
else
  log_line
  log_ok "Done."
  if [[ "${HAS_LOCAL_FAIL:-0}" -eq 1 ]]; then
    log_info "If local gateways failed: REGISTER_VERBOSE=1 for full API response; REGISTER_WAIT_SECONDS=30 if translate containers were still starting; docker compose ps to confirm all services are up."
  fi
  log_info "Auth: gateways that need API keys or OAuth (Context7, v0, apify-dribbble, etc.) → configure in Admin UI. See docs/ADMIN_UI_MANUAL_REGISTRATION.md"
fi
