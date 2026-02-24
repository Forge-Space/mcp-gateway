# Virtual Server System

## Purpose
Guides editing of virtual server configuration and registration logic.

## Key Files
- `config/virtual-servers.txt` — 79 virtual server configurations
- Registration via `make register`
- Admin UI at `http://localhost:4444/admin`

## Architecture
Virtual servers organize tools into collections for IDE connections. Each server has a UUID for IDE MCP config.

Key servers:
| Server | Purpose | Tools |
|--------|---------|-------|
| `cursor-router` | Tool-router only (1-2 tools) | Dynamic routing |
| `cursor-default` | All core tools (~45 tools) | 9 gateways |
| `nodejs-typescript` | Node.js stack | 8 gateways |
| `react-nextjs` | React + testing | 9 gateways |
| `database-dev` | DB tools | 7 gateways |

Management commands:
- `make register` — register/re-register all servers
- `make list-servers` — list active servers with UUIDs
- `make cleanup-duplicates` — remove duplicate registrations
- `REGISTER_WAIT_SECONDS=30 make register` — wait for services

Phase 1 (enable/disable) not yet implemented — currently comment out in config.

## Critical Constraints
- Max **60 tools** per virtual server / IDE connection (BR-001)
- Validate tool count during server creation
- UUID-based IDE connections
