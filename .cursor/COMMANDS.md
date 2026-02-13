# Cursor Agent Commands (MCP Gateway)

This project is Bash/Docker only (no Node at repo root). Use Make for run, lint, and test.

- **Lint:** `make lint` (shellcheck on scripts + ruff on tool_router). CI runs on push/PR (see [.github/workflows/ci.yml](../.github/workflows/ci.yml)).
- **Test:** `make test` (pytest on tool_router). CI runs tests.

## Verify / run

1. Start gateway (and translate services): `make start`
2. Register gateways: `make register`
3. Optional: list prompts: `make list-prompts`

See [README](../README.md) for full usage. If gateways fail to register, wait for translate containers (e.g. `REGISTER_WAIT_SECONDS=30 make register`) or check `docker compose ps` and logs.

## Connect Cursor

**Recommended:** Use the wrapper so no JWT is stored in mcp.json: after `make register`, run `make use-cursor-wrapper` to set context-forge in `~/.cursor/mcp.json` to the wrapper, then restart Cursor. See [README – Connect Cursor](../README.md#connect-cursor).

**Manual JWT:** `make jwt` then add server URL and `MCP_AUTH=Bearer <token>` to mcp.json (or use streamable HTTP/SSE with Authorization header). To refresh the token in place: `make refresh-cursor-jwt` (run weekly or before Cursor).

## Change gateways or prompts

1. Edit `scripts/gateways.txt` or `scripts/prompts.txt` (and optionally `scripts/resources.txt`).
2. Set `REGISTER_PROMPTS=true` or `REGISTER_RESOURCES=true` in `.env` if using prompts/resources.
3. Run `make register`.

To remove duplicate virtual servers (same tool set): `make cleanup-duplicates` (or `CLEANUP_DRY_RUN=1 make cleanup-duplicates` to report only).

Gateways that need API keys or OAuth (e.g. Context7, v0, apify-dribbble): add in Admin UI and set Passthrough Headers or Authentication. See [docs/ADMIN_UI_MANUAL_REGISTRATION.md](../docs/ADMIN_UI_MANUAL_REGISTRATION.md).
