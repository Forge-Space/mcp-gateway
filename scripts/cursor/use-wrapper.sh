#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
source "$SCRIPT_DIR/lib/bootstrap.sh"
load_env || { log_err ".env not found in $REPO_ROOT"; exit 1; }

if ! command -v jq &>/dev/null; then
  log_err "jq is required. Install with: brew install jq or apt-get install jq"
  exit 1
fi

MCP_JSON="${CURSOR_MCP_JSON:-$HOME/.cursor/mcp.json}"
if [[ ! -f "$MCP_JSON" ]]; then
  log_err "$MCP_JSON not found"
  exit 1
fi

WRAPPER_PATH="$REPO_ROOT/scripts/cursor-mcp-wrapper.sh"
if [[ ! -x "$WRAPPER_PATH" ]]; then
  log_err "$WRAPPER_PATH not found or not executable"
  exit 1
fi

url_file="$REPO_ROOT/data/.cursor-mcp-url"
if [[ -z "${CURSOR_MCP_SERVER_URL:-}" && (! -f "$url_file" || ! -s "$url_file") ]]; then
  log_err "Run 'make register' first so data/.cursor-mcp-url exists, or set CURSOR_MCP_SERVER_URL in .env"
  exit 1
fi

source "$SCRIPT_DIR/lib/gateway.sh"
KEY=$(get_context_forge_key "$MCP_JSON") || true
[[ -z "$KEY" ]] && KEY="context-forge"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

MCP_TIMEOUT_MS="${CURSOR_MCP_TIMEOUT_MS:-120000}"
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
log_section "Cursor MCP wrapper"
log_ok "Set \"$KEY\" to use the wrapper in $MCP_JSON (backup: ${MCP_JSON}.bak)."
log_info "Fully quit Cursor (Cmd+Q / Alt+F4) and reopen to use automatic JWT."
