#!/usr/bin/env bash
# Removes virtual servers that share the same tool set (duplicates).
# Keeps one server per unique tool set; prefers names listed in virtual-servers.txt.
# Usage: CLEANUP_DRY_RUN=1 to report only.
# Optional: CLEANUP_CURL_CONNECT=10, CLEANUP_CURL_MAX_TIME=60 (increase if gateway is slow or times out).
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err "Copy .env.example to .env and set PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY."; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

GATEWAY_URL="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
DRY_RUN="${CLEANUP_DRY_RUN:-0}"
COMPOSE=$(compose_cmd)
export COMPOSE
JWT=$(get_jwt) || { log_err "Failed to generate JWT."; exit 1; }

if ! command -v jq &>/dev/null; then
  log_err "jq is required. Install jq to run this script."
  exit 1
fi

CURL_CONNECT="${CLEANUP_CURL_CONNECT:-10}"
CURL_MAX_TIME="${CLEANUP_CURL_MAX_TIME:-60}"

log_section "Cleanup duplicate virtual servers"
log_step "Connecting to gateway..."

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
servers_code=$(parse_http_code "$servers_resp")
servers_body=$(parse_http_body "$servers_resp")
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
virtual_servers_file="${CONFIG_DIR:-$SCRIPT_DIR}/virtual-servers.txt"
if [[ -f "$virtual_servers_file" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    name=$(echo "$line" | cut -d'|' -f1)
    [[ -n "$name" ]] && preferred_names="${preferred_names:+$preferred_names$'\n'}$name"
  done < "$virtual_servers_file"
fi

declare -A sig_to_ids
declare -A id_to_name

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
    get_code=$(parse_http_code "$get_resp")
    get_body=$(parse_http_body "$get_resp")
    if [[ "$get_code" == "200" ]]; then
      tools=$(echo "$get_body" | jq -c '(.server // .).associated_tools // []' 2>/dev/null)
    fi
  fi
  sig=$(echo "$tools" | jq -c 'sort' 2>/dev/null)
  [[ -z "$sig" ]] && sig="[]"
  id_to_name["$id"]="$name"
  sig_to_ids["$sig"]="${sig_to_ids[$sig]:+${sig_to_ids[$sig]}$'\n'}$id"
done < <(echo "$server_list")

duplicates_found=0
to_delete=()

for sig in "${!sig_to_ids[@]}"; do
  IFS=' ' read -ra ids <<< "$(echo "${sig_to_ids[$sig]}" | tr '\n' ' ')"
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
