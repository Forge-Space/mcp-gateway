# Scripts

Logging: `lib/log.sh` (TTY-only color). Prefer **make** targets; script paths below are alternatives.

| Command / file                                                     | Purpose                                                             |
| ------------------------------------------------------------------ | ------------------------------------------------------------------- |
| `make generate-secrets`                                            | Print JWT_SECRET_KEY + AUTH_ENCRYPTION_SECRET for .env              |
| `make start` / `./start.sh`                                        | Start gateway + translate services                                  |
| `make stop` / `./start.sh stop`                                    | Stop stack                                                          |
| `make reset-db`                                                    | Stop and remove ./data/mcp.db (then make start, make register)      |
| `make gateway-only` / `./start.sh gateway-only`                    | Gateway only, no translate                                          |
| `make register` / `./scripts/register-gateways.sh`                 | Register from gateways.txt (+ virtual servers, prompts, resources)  |
| `make register-wait`                                               | register with REGISTER_WAIT_SECONDS=30                              |
| `make list-prompts` / `./scripts/list-prompts.sh`                  | GET /prompts (verify or when Admin Prompts page hangs)              |
| `make jwt` / `scripts/create_jwt_token_standalone.py`              | Print JWT (needs PyJWT or running gateway)                          |
| `make refresh-cursor-jwt` / `scripts/refresh-cursor-jwt.sh`        | Update Bearer in ~/.cursor/mcp.json (manual JWT config)             |
| `make use-cursor-wrapper` / `scripts/use-cursor-wrapper.sh`        | Set context-forge in mcp.json to wrapper (needs jq, make register)  |
| `make verify-cursor-setup` / `scripts/verify-cursor-setup.sh`      | Check gateway, .cursor-mcp-url, server UUID                         |
| `make cleanup-duplicates` / `scripts/cleanup-duplicate-servers.sh` | Remove duplicate virtual servers (CLEANUP_DRY_RUN=1 to report only) |
| `scripts/cursor-mcp-wrapper.sh`                                    | Cursor MCP command for context-forge (JWT per connection)           |

**Data / config:** `data/.cursor-mcp-url` (written by `make register`; used by the context-forge wrapper). When `REGISTER_CURSOR_MCP_SERVER_NAME` is unset, the **first** virtual server in `virtual-servers.txt` is written (e.g. cursor-default); set it in `.env` to pin a different server (e.g. cursor-router). If context-forge shows "No server info found", run `make register` to refresh the URL, then fully quit and reopen Cursor.  
**Files:** `gateways.txt` (Name|URL|Transport), `virtual-servers.txt` (ServerName|gateway1,gateway2,...), `prompts.txt` (name|description|template), `resources.txt` (name|uri|description|mime_type). See [README](../README.md) and [.env.example](../.env.example).
