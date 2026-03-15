---
name: virtual-server-mgmt
description: Guide for managing virtual servers in the MCP Gateway. Use when enabling/disabling servers, listing server status, or understanding the virtual server config format. Covers CLI (make targets), REST API endpoints, and the Admin UI toggle.
---

# Virtual Server Management

## Quick Reference

```bash
# List all servers with ✅/❌ status
make list-servers

# Enable a disabled server
make enable-server SERVER=cursor-search

# Disable an enabled server
make disable-server SERVER=database-dev

# Apply changes to the running gateway
make register
```

## REST API (v1.12.0+)

All endpoints require **admin role** (`Authorization: Bearer <jwt>`).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/servers` | List all virtual servers |
| `GET` | `/servers/{name}` | Get a single server |
| `PATCH` | `/servers/{name}/enabled` | Toggle enabled flag |
| `GET` | `/ide/detect` | Detect installed IDEs |

```bash
# Example: disable cursor-browser via API
curl -X PATCH http://localhost:4444/servers/cursor-browser/enabled \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

After toggling via API, run `make register` to apply changes to the gateway routing layer.

The Admin UI at `http://localhost:3000/server-management` provides a one-click toggle backed by this API.

## Config Format

`config/virtual-servers.txt`:
```
# Format: Name|enabled|gateways|description
cursor-default|true|sequential-thinking,filesystem,tavily|Virtual server: cursor-default
cursor-search|false|tavily|Virtual server: cursor-search (disabled)
```

Fields:
- `name` — unique identifier, used in IDE config URLs
- `enabled` — `true`/`false` (also: `1`/`0`, `yes`/`no`)
- `gateways` — comma-separated list of MCP server names
- `description` — human-readable label

Legacy 2-field format (`name|gateways`) is also supported — always treated as enabled.

## Implementation Details

The `enabled` flag is parsed in `scripts/gateway/register.sh`:
```bash
if [[ "$enabled_flag" != "true" && "$enabled_flag" != "1" && "$enabled_flag" != "yes" ]]; then
    log_info "Skipping disabled server: $server_name"
    continue
fi
```

The Makefile targets delegate to `scripts/utils/manage-servers.py` (regex-based in-place editing).

The REST API is implemented in `tool_router/api/server_mgmt.py` and registered in `tool_router/http_server.py`.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/utils/manage-servers.py` | list/enable/disable/status CLI |
| `scripts/gateway/register.sh` | creates virtual servers (skips disabled) |
| `scripts/ide-setup.py list-servers` | list servers for IDE config |

## Workflow: Disable a Resource-Heavy Server

```bash
# 1. See what's enabled
make list-servers

# 2. Disable an unused server
make disable-server SERVER=java-spring

# 3. Apply — gateway re-creates only enabled servers
make register

# 4. Re-enable when needed
make enable-server SERVER=java-spring && make register
```

## Tests

```bash
# CLI utility tests
pytest tests/test_manage_servers.py -v --no-cov

# API endpoint tests
pytest tool_router/tests/unit/test_server_mgmt_api.py -v --no-cov
```
