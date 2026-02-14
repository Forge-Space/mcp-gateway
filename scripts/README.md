# Scripts

Scripts for managing the MCP gateway stack, organized by functional domain:

- **gateway/**: Gateway registration and management
- **cursor/**: Cursor IDE integration scripts
- **virtual-servers/**: Virtual server management
- **utils/**: Utility scripts (JWT, Docker checks, MCP registry)
- **lib/**: Shared libraries (bootstrap, gateway, logging)

All scripts source `lib/bootstrap.sh` (sets `SCRIPT_DIR`, `REPO_ROOT`, `CONFIG_DIR`, loads `.env`) and `lib/gateway.sh` (JWT generation, API helpers). Use `make` targets when available (see [Makefile](../Makefile)).

**Backward compatibility:** Symlinks exist at the old script locations for compatibility during transition.

**Lib / shared behavior**

- **`lib/log.sh`** – TTY-safe logging (colors only when stdout is a TTY).
- **`lib/bootstrap.sh`** – Sets `SCRIPT_DIR`, `REPO_ROOT`, `cd` to repo root, and sources log.sh. Exposes `load_env` to source `.env` (returns non-zero if `.env` is missing). Scripts source it then call `load_env`; those that require `.env` exit if `load_env` fails.
- **`lib/gateway.sh`** – Gateway helpers (source after bootstrap and `load_env`): `compose_cmd` (docker compose vs docker-compose), `get_jwt` (standalone Python, then compose exec, then docker exec), `normalize_gateway_url` (localhost / 127.0.0.1 health try), `wait_for_health`, `parse_http_code` / `parse_http_body` for curl responses, `get_context_forge_key` for Cursor mcp.json.

| Command / file                                                     | Purpose                                                                           |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| `make generate-secrets`                                            | Print JWT_SECRET_KEY + AUTH_ENCRYPTION_SECRET for .env                            |
| `make start` / `./start.sh`                                        | Start gateway + translate services                                                |
| `make stop` / `./start.sh stop`                                    | Stop stack                                                                        |
| `make reset-db`                                                    | Stop and remove ./data/mcp.db (then make start, make register)                    |
| `make gateway-only` / `./start.sh gateway-only`                    | Gateway only, no translate                                                        |
| `make register` / `./scripts/gateway/register.sh`                  | Register from gateways.txt (+ virtual servers, prompts, resources)                |
| `make register-wait`                                               | register with REGISTER_WAIT_SECONDS=30                                            |
| `make list-prompts` / `./scripts/gateway/list-prompts.sh`          | GET /prompts (verify or when Admin Prompts page hangs)                            |
| `make list-servers` / `./scripts/virtual-servers/list.sh`          | List virtual servers (id, name, tools) via API; use when Admin UI shows 0 servers |
| `make jwt` / `scripts/utils/create-jwt.py`                         | Print JWT (needs PyJWT or running gateway)                                        |
| `make refresh-cursor-jwt` / `scripts/cursor/refresh-jwt.sh`        | Update Bearer in ~/.cursor/mcp.json (manual JWT config)                           |
| `make use-cursor-wrapper` / `scripts/cursor/use-wrapper.sh`        | Set context-forge in mcp.json to wrapper + 2min timeout (needs jq, make register) |
| `make verify-cursor-setup` / `scripts/cursor/verify-setup.sh`      | Check gateway, .cursor-mcp-url, server UUID, Context Forge image, Docker→gateway  |
| `make cursor-pull`                                                  | Pull Context Forge image (avoids first Cursor start timeout)                      |
| `make cleanup-duplicates` / `scripts/virtual-servers/cleanup-duplicates.sh` | Remove duplicate virtual servers (CLEANUP_DRY_RUN=1 to report only)               |
| `scripts/cursor/mcp-wrapper.sh`                                    | Cursor MCP command for context-forge (JWT per connection)                         |

**Data / config:** `data/.cursor-mcp-url` (written by `make register`; used by the context-forge wrapper). When `REGISTER_CURSOR_MCP_SERVER_NAME` is unset, the default is **cursor-router** (tool-router). Set to `cursor-default` (or another name) in `.env` and run `make register` to use the full tool set instead. If context-forge shows "No server info found", run `make register` to refresh the URL, then fully quit and reopen Cursor.
**Config files:** Configuration files have been moved to `/config` at repo root. `config/gateways.txt` (Name|URL|Transport), `config/virtual-servers.txt` (ServerName|gateway1,gateway2,...), `config/prompts.txt` (name|description|template), `config/resources.txt` (name|uri|description|mime_type). See [README](../README.md) and [.env.example](../.env.example).
