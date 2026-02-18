#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err ".env not found in $REPO_ROOT"; exit 1; }

if ! command -v jq &>/dev/null; then
  log_err "jq is required. Install with: brew install jq or apt-get install jq"
  exit 1
fi

MCP_JSON="${MCP_CLIENT_CONFIG:-$HOME/.cursor/mcp.json}"
if [[ ! -f "$MCP_JSON" ]]; then
  log_err "$MCP_JSON not found. Set MCP_CLIENT_CONFIG to your IDE's mcp.json path."
  exit 1
fi

WRAPPER_PATH="$REPO_ROOT/scripts/mcp-client/mcp-wrapper.sh"
if [[ ! -x "$WRAPPER_PATH" ]]; then
  log_err "$WRAPPER_PATH not found or not executable"
  exit 1
fi

source "$SCRIPT_DIR/lib/gateway.sh"
KEY=$(get_mcp_client_key "$MCP_JSON") || true
[[ -z "$KEY" ]] && KEY="forge-mcp-gateway"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

MCP_TIMEOUT_MS="${MCP_CLIENT_TIMEOUT_MS:-120000}"
jq --arg key "$KEY" --arg path "$WRAPPER_PATH" --argjson timeout "$MCP_TIMEOUT_MS" '
  def entry: {"command": $path, "timeout": $timeout};
  if .mcpServers[$key] != null then
    .mcpServers[$key] = entry
  elif .[$key] != null then
    .[$key] = entry
  else
    .mcpServers = ((.mcpServers // {}) | .[$key] = entry)
  end
' "$MCP_JSON" > "$tmp"

cp "$MCP_JSON" "${MCP_JSON}.bak"
mv "$tmp" "$MCP_JSON"
log_section "MCP Client Wrapper"
log_ok "Set \"$KEY\" to use the wrapper in $MCP_JSON."
log_info "Fully quit your IDE and reopen to use automatic JWT."
