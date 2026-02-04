#!/usr/bin/env bash
# Removes virtual servers that share the same tool set (duplicates).
# Keeps one server per unique tool set; prefers names listed in virtual-servers.txt.
# Usage: CLEANUP_DRY_RUN=1 to report only.
# Optional: CLEANUP_CURL_CONNECT=10, CLEANUP_CURL_MAX_TIME=60 (increase if gateway is slow or times out).
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=scripts/lib/log.sh
source "$SCRIPT_DIR/lib/log.sh" 2>/dev/null || true

if [[ ! -f .env ]]; then
  log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."
  exit 1
fi

set -a
source .env
set +a

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
DRY_RUN="${CLEANUP_DRY_RUN:-0}"

log_section "Cleanup duplicate virtual servers"
log_step "Connecting to gateway..."

if docker compose version &>/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose"
else
  COMPOSE=""
fi

if [[ -n "$COMPOSE" ]] && $COMPOSE ps gateway -q 2>/dev/null | grep -q .; then
  JWT=$($COMPOSE exec -T gateway python3 -m mcpgateway.utils.create_jwt_token \
    --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null)
else
  CONTAINER="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    log_err "Gateway is not running. Start with ./start.sh (from repo root)."
    exit 1
  fi
  JWT=$(docker exec "$CONTAINER" python3 -m mcpgateway.utils.create_jwt_token \
    --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null)
fi
if [[ -z "$JWT" ]]; then
  log_err "Failed to generate JWT."
  exit 1
fi

if ! command -v jq &>/dev/null; then
  log_err "jq is required. Install jq to run this script."
  exit 1
fi

CURL_CONNECT="${CLEANUP_CURL_CONNECT:-10}"
CURL_MAX_TIME="${CLEANUP_CURL_MAX_TIME:-60}"

servers_resp=$(curl -s -w "\n%{http_code}" --connect-timeout "$CURL_CONNECT" --max-time "$CURL_MAX_TIME" \
  -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers?limit=0&include_pagination=false" 2>/dev/null)
curl_rc=$?
if [[ "$curl_rc" -eq 28 ]]; then
  log_err "GET /servers timed out. Increase CLEANUP_CURL_MAX_TIME (current: ${CURL_MAX_TIME}s) or check gateway at $GATEWAY_URL"
  exit 28
fi
if [[ "$curl_rc" -eq 7 ]]; then
  log_err "Could not reach gateway at $GATEWAY_URL. Is it running? (make start)"
  exit 7
fi
servers_code=$(echo "$servers_resp" | tail -n1)
servers_body=$(echo "$servers_resp" | sed '$d')
if [[ "$servers_code" != "200" ]] || [[ -z "$servers_body" ]]; then
  log_err "GET /servers failed (HTTP ${servers_code:-none}). Check gateway and JWT."
  exit 1
fi

server_list=$(echo "$servers_body" | jq -c 'if type == "array" then .[] else .servers[]? // empty end' 2>/dev/null)
if [[ -z "$server_list" ]]; then
  log_ok "No virtual servers found. Nothing to clean."
  exit 0
fi

preferred_names=""
if [[ -f "$SCRIPT_DIR/virtual-servers.txt" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    name=$(echo "$line" | cut -d'|' -f1)
    [[ -n "$name" ]] && preferred_names="${preferred_names:+$preferred_names$'\n'}$name"
  done < "$SCRIPT_DIR/virtual-servers.txt"
fi

declare -A sig_to_ids
declare -A id_to_name
declare -A id_to_sig

while IFS= read -r obj; do
  [[ -z "$obj" ]] && continue
  id=$(echo "$obj" | jq -r '.id // empty')
  name=$(echo "$obj" | jq -r '.name // empty')
  tools=$(echo "$obj" | jq -c '.associated_tools // []' 2>/dev/null)
  if [[ -z "$id" || "$id" == "null" ]]; then
    continue
  fi
  if [[ -z "$tools" || "$tools" == "null" ]]; then
    get_resp=$(curl -s -w "\n%{http_code}" --connect-timeout "$CURL_CONNECT" --max-time "$CURL_MAX_TIME" \
      -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers/${id}" 2>/dev/null) || true
    get_code=$(echo "$get_resp" | tail -n1)
    get_body=$(echo "$get_resp" | sed '$d')
    if [[ "$get_code" == "200" ]]; then
      tools=$(echo "$get_body" | jq -c '(.server // .).associated_tools // []' 2>/dev/null)
    fi
  fi
  sig=$(echo "$tools" | jq -c 'sort' 2>/dev/null)
  [[ -z "$sig" ]] && sig="[]"
  id_to_name["$id"]="$name"
  id_to_sig["$id"]="$sig"
  sig_to_ids["$sig"]="${sig_to_ids[$sig]:+${sig_to_ids[$sig]}$'\n'}$id"
done < <(echo "$server_list")

duplicates_found=0
to_delete=()

for sig in "${!sig_to_ids[@]}"; do
  ids=($(echo "${sig_to_ids[$sig]}" | tr '\n' ' '))
  if [[ ${#ids[@]} -le 1 ]]; then
    continue
  fi
  duplicates_found=1
  keep_id=""
  for id in "${ids[@]}"; do
    name="${id_to_name[$id]:-}"
    if echo "$preferred_names" | grep -qFx "$name"; then
      keep_id="$id"
      break
    fi
  done
  if [[ -z "$keep_id" ]]; then
    keep_id="${ids[0]}"
  fi
  for id in "${ids[@]}"; do
    [[ "$id" == "$keep_id" ]] && continue
    to_delete+=("$id")
  done
done

if [[ $duplicates_found -eq 0 ]]; then
  log_ok "No duplicate tool sets found."
  exit 0
fi

if [[ ${#to_delete[@]} -eq 0 ]]; then
  log_ok "No duplicate servers to remove."
  exit 0
fi

for id in "${to_delete[@]}"; do
  name="${id_to_name[$id]:-}"
  if [[ "$DRY_RUN" =~ ^(1|true|yes)$ ]]; then
    log_info "[dry-run] Would delete server: $name ($id)"
  else
    del_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout "$CURL_CONNECT" --max-time "$CURL_MAX_TIME" -X DELETE \
      -H "Authorization: Bearer $JWT" "${GATEWAY_URL}/servers/${id}" 2>/dev/null) || del_code="000"
    if [[ "$del_code" =~ ^2[0-9][0-9]$ ]] || [[ "$del_code" == "204" ]]; then
      log_ok "Deleted duplicate: $name ($id)"
    else
      log_warn "Could not delete $name ($id): HTTP $del_code (API may not support DELETE)"
    fi
  fi
done

if [[ "$DRY_RUN" =~ ^(1|true|yes)$ ]]; then
  log_line
  log_info "Run without CLEANUP_DRY_RUN=1 to perform deletions."
fi
