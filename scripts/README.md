# Scripts

Scripts for managing the MCP gateway stack:

- **gateway/**: Gateway registration
- **virtual-servers/**: Virtual server management
- **utils/**: Utility scripts (JWT, Docker checks, MCP registry)
- **lib/**: Shared libraries (bootstrap, gateway, logging)

All shell scripts source `lib/bootstrap.sh` (sets `SCRIPT_DIR`, `REPO_ROOT`, `CONFIG_DIR`, loads `.env`) and `lib/gateway.sh` (JWT generation, API helpers). Use `make` targets when available (see [Makefile](../Makefile)).

**Lib / shared behavior**

- **`lib/log.sh`** – TTY-safe logging (colors only when stdout is a TTY).
- **`lib/bootstrap.sh`** – Sets `SCRIPT_DIR`, `REPO_ROOT`, `cd` to repo root, and sources log.sh. Exposes `load_env` to source `.env`.
- **`lib/gateway.sh`** – Gateway helpers: `compose_cmd`, `get_jwt`, `normalize_gateway_url`, `wait_for_health`, `parse_http_code` / `parse_http_body`, `get_context_forge_key`.

| Script | Purpose |
| --- | --- |
| `gateway/register.sh` | Register gateways from gateways.txt (+ virtual servers, prompts, resources) |
| `virtual-servers/cleanup-duplicates.sh` | Remove duplicate virtual servers (CLEANUP_DRY_RUN=1 to report only) |
| `mcp-wrapper.sh` | MCP command wrapper for IDE integration (JWT per connection) |
| `setup-wizard.py` | Interactive project setup wizard |
| `status.py` | Project status dashboard |
| `ide-setup.py` | IDE integration setup and management |
| `utils/create-jwt.py` | Generate JWT tokens for gateway auth |
| `utils/check-docker-updates.sh` | Check for Docker image updates (CI) |
| `utils/check-mcp-registry.py` | Validate MCP server registry (CI) |

**Config files:** Located in `/config` at repo root — `gateways.txt`, `virtual-servers.txt`, `prompts.txt`, `resources.txt`. See [README](../README.md).
