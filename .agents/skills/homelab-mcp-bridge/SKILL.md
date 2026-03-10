---
name: homelab-mcp-bridge
description: Fixes and validates Homelab MCP IDE setup when npm client bridges are unavailable. Use when users mention setup-forge-space-mcp, @forge-mcp-gateway/client resolution failures, Cursor/Windsurf MCP config issues, or wrapper bridge migration.
---

# Homelab MCP Bridge

## Goal

Standardize MCP IDE setup on the local wrapper bridge (`scripts/mcp-wrapper.sh`) without relying on
`@forge-mcp-gateway/client` npm resolution.

## Workflow

1. Confirm bridge availability:
   - `test -x scripts/mcp-wrapper.sh`
   - `test -s data/.mcp-client-url`
2. Run setup:
   - `./scripts/setup-forge-space-mcp.sh`
3. Validate setup:
   - `python3 scripts/ide-setup.py setup cursor --action verify`
4. If validation fails, emit deterministic fixes:
   - Gateway health failure: `make start`
   - Missing URL file: `make register`
   - Missing wrapper: `chmod +x scripts/mcp-wrapper.sh`
   - Timeout: `CURSOR_MCP_TIMEOUT_MS=180000 ./scripts/setup-forge-space-mcp.sh`
   - If register reports `GET /servers returned 404`: gateway is in minimal mode; switch to a
     deployment profile that exposes `/servers` or set `MCP_CLIENT_SERVER_URL` explicitly in IDE
     config until full mode is available.

## Output Contract

Always report:
- Whether wrapper bridge is configured in IDE config
- Whether `data/.mcp-client-url` exists and matches `/servers/<uuid>/mcp`
- The exact remediation command if any check fails

## Guardrails

- Do not suggest `npx -y @forge-mcp-gateway/client` as an active setup path.
- Keep secrets out of committed files; rely on `.env` and runtime environment variables.
- Preserve existing unrelated `mcpServers` entries while updating bridge config.
