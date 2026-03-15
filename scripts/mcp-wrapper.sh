#!/usr/bin/env bash
# mcp-wrapper.sh — stdio bridge between IDE and Forge Space MCP Gateway
#
# Reads MCP_CLIENT_SERVER_URL from the environment (written by setup-forge-space-mcp.sh
# or configurable in the IDE mcpServers entry) and forwards stdio MCP protocol to the
# remote gateway via the @forgespace/mcp-gateway-client npx package.
#
# Environment variables:
#   MCP_CLIENT_SERVER_URL  (required) Full gateway server URL, e.g.
#                          http://localhost:4444/servers/<UUID>/mcp
#   MCP_GATEWAY_TOKEN      (optional) JWT bearer token for authenticated gateways
#   MCP_GATEWAY_TIMEOUT    (optional) Request timeout in ms (default: 120000)
#   MCP_WRAPPER_NPX        (optional) Override the npx binary path

set -euo pipefail

NPX="${MCP_WRAPPER_NPX:-npx}"
PACKAGE="@forgespace/mcp-gateway-client"

# Validate required env
if [[ -z "${MCP_CLIENT_SERVER_URL:-}" ]]; then
	echo '{"jsonrpc":"2.0","error":{"code":-32603,"message":"MCP_CLIENT_SERVER_URL is not set. Run make register or pass --mcp-url to setup-forge-space-mcp.sh"},"id":null}' >&2
	exit 1
fi

# Build argument list
ARGS=("--yes" "${PACKAGE}" "--url=${MCP_CLIENT_SERVER_URL}")

if [[ -n "${MCP_GATEWAY_TOKEN:-}" ]]; then
	ARGS+=("--token=${MCP_GATEWAY_TOKEN}")
fi

if [[ -n "${MCP_GATEWAY_TIMEOUT:-}" ]]; then
	ARGS+=("--timeout=${MCP_GATEWAY_TIMEOUT}")
fi

exec "${NPX}" "${ARGS[@]}"
