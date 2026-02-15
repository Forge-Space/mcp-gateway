#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err ".env not found in $REPO_ROOT"; exit 1; }
source "$SCRIPT_DIR/lib/gateway.sh"

if ! command -v jq &>/dev/null; then
  log_err "jq is required. Install with: brew install jq or apt-get install jq"
  exit 1
fi

MCP_JSON="${MCP_CLIENT_CONFIG:-$HOME/.cursor/mcp.json}"
if [[ ! -f "$MCP_JSON" ]]; then
  log_err "$MCP_JSON not found. Set MCP_CLIENT_CONFIG to your IDE's mcp.json path."
  log_info "Examples: ~/.cursor/mcp.json, ~/.windsurf/mcp.json, ~/.vscode/settings.json"
  exit 1
fi

JWT=$(get_jwt) || { log_err "Failed to generate JWT."; exit 1; }

KEY=$(get_mcp_client_key "$MCP_JSON") || true
if [[ -z "$KEY" ]]; then
  log_err "MCP gateway entry not found in $MCP_JSON (tried: context-forge, user-context-forge, mcp-gateway). Set MCP_CLIENT_KEY if your key differs."
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
log_section "Refresh MCP Client JWT"
log_ok "Updated token for \"$KEY\" in $MCP_JSON (backup: ${MCP_JSON}.bak)."
log_info "Restart your IDE to use the new token."
