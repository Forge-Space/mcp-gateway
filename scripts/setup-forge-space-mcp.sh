#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WRAPPER_PATH="${REPO_ROOT}/scripts/mcp-wrapper.sh"
URL_FILE="${REPO_ROOT}/data/.mcp-client-url"
CONFIG_PATH="${MCP_CONFIG_PATH:-${HOME}/.cursor/mcp.json}"
SERVER_KEY="${MCP_SERVER_KEY:-context-forge}"
SERVER_KEY_EXPLICIT=0
TIMEOUT_MS="${CURSOR_MCP_TIMEOUT_MS:-120000}"
GATEWAY_BASE="${GATEWAY_URL:-http://localhost:${PORT:-4444}}"
GATEWAY_BASE="${GATEWAY_BASE%/}"
MCP_URL_OVERRIDE="${MCP_CLIENT_SERVER_URL:-}"

usage() {
  cat <<'EOF'
Usage: setup-forge-space-mcp.sh [--config <path>] [--key <name>] [--timeout <ms>] [--gateway <url>] [--mcp-url <url>]

Configures IDE MCP entry to use scripts/mcp-wrapper.sh and backs up existing config.
EOF
}

while [[ $# -gt 0 ]]; do
  case "${1}" in
    --config)
      CONFIG_PATH="${2}"
      shift 2
      ;;
    --key)
      SERVER_KEY="${2}"
      SERVER_KEY_EXPLICIT=1
      shift 2
      ;;
    --timeout)
      TIMEOUT_MS="${2}"
      shift 2
      ;;
    --gateway)
      GATEWAY_BASE="${2%/}"
      shift 2
      ;;
    --mcp-url)
      MCP_URL_OVERRIDE="${2}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: ${1}" >&2
      usage
      exit 1
      ;;
  esac
done

if ! [[ "${TIMEOUT_MS}" =~ ^[0-9]+$ ]] || (( TIMEOUT_MS < 1000 || TIMEOUT_MS > 600000 )); then
  echo "Invalid timeout: ${TIMEOUT_MS} (must be 1000-600000 ms)" >&2
  exit 1
fi

for cmd in curl python3; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Missing required command: ${cmd}" >&2
    exit 1
  fi
done

if [[ ! -x "${WRAPPER_PATH}" ]]; then
  echo "Wrapper script not executable: ${WRAPPER_PATH}" >&2
  echo "Run: chmod +x \"${WRAPPER_PATH}\"" >&2
  exit 1
fi

if [[ -n "${MCP_URL_OVERRIDE}" ]]; then
  MCP_URL="${MCP_URL_OVERRIDE}"
  MCP_URL_SOURCE="explicit override"
else
  if [[ ! -s "${URL_FILE}" ]]; then
    echo "Missing or empty ${URL_FILE}" >&2
    echo "Run: make start && make register, or pass --mcp-url/ MCP_CLIENT_SERVER_URL" >&2
    exit 1
  fi

  MCP_URL="$(head -n1 "${URL_FILE}" | tr -d '\r\n')"
  if [[ -z "${MCP_URL}" ]]; then
    echo "${URL_FILE} is empty" >&2
    exit 1
  fi
  MCP_URL_SOURCE="${URL_FILE}"
fi

if ! [[ "${MCP_URL}" =~ /servers/[a-f0-9-]+/mcp$ ]]; then
  echo "Invalid MCP URL: ${MCP_URL}" >&2
  echo "Expected: .../servers/<uuid>/mcp" >&2
  exit 1
fi

HEALTH_URL="${GATEWAY_BASE}/health"
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 "${HEALTH_URL}" || true)"
if [[ "${HTTP_CODE}" != "200" ]]; then
  echo "Gateway health check failed at ${HEALTH_URL} (HTTP ${HTTP_CODE})" >&2
  echo "Run: make start" >&2
  exit 1
fi

CONFIG_DIR="$(dirname "${CONFIG_PATH}")"
mkdir -p "${CONFIG_DIR}"

if [[ -f "${CONFIG_PATH}" ]]; then
  BACKUP_PATH="${CONFIG_PATH}.bak.$(date +%Y%m%d%H%M%S)"
  cp "${CONFIG_PATH}" "${BACKUP_PATH}"
  echo "Backup created: ${BACKUP_PATH}"
fi

CONFIG_PATH="${CONFIG_PATH}" \
MCP_URL="${MCP_URL}" \
WRAPPER_PATH="${WRAPPER_PATH}" \
SERVER_KEY="${SERVER_KEY}" \
SERVER_KEY_EXPLICIT="${SERVER_KEY_EXPLICIT}" \
TIMEOUT_MS="${TIMEOUT_MS}" \
python3 <<'PY'
import json
import os
import sys
from pathlib import Path

config_path = Path(os.environ["CONFIG_PATH"]).expanduser()
mcp_url = os.environ["MCP_URL"]
wrapper_path = os.environ["WRAPPER_PATH"]
server_key = os.environ["SERVER_KEY"]
timeout_ms = int(os.environ["TIMEOUT_MS"])
key_explicit = os.environ["SERVER_KEY_EXPLICIT"] == "1"

config: dict = {}
if config_path.exists() and config_path.stat().st_size > 0:
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {config_path}: {exc}", file=sys.stderr)
        sys.exit(1)

if not isinstance(config, dict):
    print(f"Invalid top-level JSON type in {config_path}", file=sys.stderr)
    sys.exit(1)

servers = config.get("mcpServers")
if servers is None:
    servers = {}
    config["mcpServers"] = servers
elif not isinstance(servers, dict):
    print("Expected mcpServers to be an object", file=sys.stderr)
    sys.exit(1)

target_key = server_key
if not key_explicit:
    for key in servers:
        if "context-forge" in key.lower():
            target_key = key
            break

servers[target_key] = {
    "command": wrapper_path,
    "env": {"MCP_CLIENT_SERVER_URL": mcp_url},
    "timeout": timeout_ms,
}

config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print(target_key)
PY

echo "Configured MCP bridge in ${CONFIG_PATH}"
echo "Command: ${WRAPPER_PATH}"
echo "Server URL: ${MCP_URL}"
echo "URL source: ${MCP_URL_SOURCE}"
echo "Restart your IDE to apply changes."
