#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=scripts/lib/log.sh
source "$SCRIPT_DIR/lib/log.sh" 2>/dev/null || true

if [[ ! -f .env ]]; then
  log_err ".env not found in $REPO_ROOT"
  exit 1
fi
set -a
source .env
set +a

if [[ -n "${CURSOR_MCP_SERVER_URL:-}" ]]; then
  MCP_SERVER_URL="$CURSOR_MCP_SERVER_URL"
else
  url_file="$REPO_ROOT/data/.cursor-mcp-url"
  if [[ ! -f "$url_file" ]] || [[ ! -s "$url_file" ]]; then
    log_err "Missing or empty data/.cursor-mcp-url. Run: make start && make register"
    log_err "Then run: make verify-cursor-setup (optional) and restart Cursor fully."
    exit 1
  fi
  MCP_SERVER_URL=$(head -n1 "$url_file" | tr -d '\r\n')
  if [[ -z "$MCP_SERVER_URL" ]]; then
    log_err "data/.cursor-mcp-url is empty. Run: make register"
    exit 1
  fi
  if [[ ! "$MCP_SERVER_URL" =~ /servers/[a-f0-9-]+/mcp ]]; then
    log_err "data/.cursor-mcp-url should be .../servers/UUID/mcp. Run: make register"
    exit 1
  fi
fi

JWT=$(python3 "$SCRIPT_DIR/create_jwt_token_standalone.py" 2>/dev/null) || true
if [[ -z "$JWT" ]]; then
  CONTAINER="${MCPGATEWAY_CONTAINER:-mcpgateway}"
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
    JWT=$(docker exec "$CONTAINER" python3 -m mcpgateway.utils.create_jwt_token \
      --username "${PLATFORM_ADMIN_EMAIL:?}" --exp 10080 --secret "${JWT_SECRET_KEY:?}" 2>/dev/null)
  fi
fi
if [[ -z "$JWT" ]]; then
  log_err "Failed to generate JWT (need PyJWT or running gateway container)."
  exit 1
fi

docker_args=(run --rm -i
  -e "MCP_SERVER_URL=$MCP_SERVER_URL"
  -e "MCP_AUTH=Bearer $JWT"
  -e "MCP_TOOL_CALL_TIMEOUT=120"
)
if [[ "$(uname -s)" == "Linux" ]]; then
  docker_args+=(--add-host=host.docker.internal:host-gateway)
fi
docker_args+=(ghcr.io/ibm/mcp-context-forge:latest python3 -m mcpgateway.wrapper)

exec docker "${docker_args[@]}"
