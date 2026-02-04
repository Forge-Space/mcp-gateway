#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=scripts/lib/log.sh
source "$SCRIPT_DIR/lib/log.sh" 2>/dev/null || true

if ! command -v jq &>/dev/null; then
  log_err "jq is required. Install with: brew install jq or apt-get install jq"
  exit 1
fi

MCP_JSON="${CURSOR_MCP_JSON:-$HOME/.cursor/mcp.json}"
if [[ ! -f "$MCP_JSON" ]]; then
  log_err "$MCP_JSON not found"
  exit 1
fi

if [[ ! -f .env ]]; then
  log_err ".env not found in $REPO_ROOT"
  exit 1
fi
set -a
source .env
set +a

JWT=$(python3 "$SCRIPT_DIR/create_jwt_token_standalone.py" 2>/dev/null) || true
if [[ -z "$JWT" ]]; then
  CONTAINER="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    JWT=$(docker exec "$CONTAINER" python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null)
  fi
fi
if [[ -z "$JWT" ]]; then
  log_err "Failed to generate JWT."
  exit 1
fi

KEY=""
for k in ${CONTEXT_FORGE_MCP_KEY:-context-forge user-context-forge}; do
  if jq -e --arg k "$k" '.mcpServers[$k] // .[$k]' "$MCP_JSON" &>/dev/null; then
    KEY="$k"
    break
  fi
done
if [[ -z "$KEY" ]]; then
  log_err "context-forge entry not found in $MCP_JSON (tried: context-forge, user-context-forge). Set CONTEXT_FORGE_MCP_KEY if your key differs."
  exit 1
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

jq --arg jwt "$JWT" --arg key "$KEY" '
  def setToken:
    (if .args then .args |= map(if type == "string" and startswith("MCP_AUTH=") then "MCP_AUTH=Bearer " + $jwt else . end) else . end) |
    (.headers = ((.headers // {}) | .["Authorization"] = "Bearer " + $jwt));

  if .mcpServers[$key] != null then
    .mcpServers[$key] |= setToken
  else
    .[$key] |= setToken
  end
' "$MCP_JSON" > "$tmp"

cp "$MCP_JSON" "${MCP_JSON}.bak"
mv "$tmp" "$MCP_JSON"
log_section "Refresh Cursor JWT"
log_ok "Updated token for \"$KEY\" in $MCP_JSON (backup: ${MCP_JSON}.bak)."
log_info "Restart Cursor to use the new token."
