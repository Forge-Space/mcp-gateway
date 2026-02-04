# MCP Gateway (Context Forge)

Self-hosted MCP gateway using [IBM Context Forge](https://github.com/IBM/mcp-context-forge). One connection from Cursor (or other MCP clients) to the gateway; add upstream MCP servers via the Admin UI.

## Prerequisites

- Docker
- Docker Compose V2 (`docker compose`) or V1 (`docker-compose`)

## Quick start

```bash
cp .env.example .env
# Edit .env: set PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD, JWT_SECRET_KEY
./start.sh
```

- **Admin UI:** http://localhost:4444/admin
- **Stop:** `./start.sh stop`

Default `./start.sh` starts the gateway and all local servers (e.g. sequential-thinking). Use `./start.sh gateway-only` for the gateway alone. Data is stored in `./data` (SQLite). Add gateways in Admin UI or run `./scripts/register-gateways.sh` after start; create a virtual server, attach tools, note its UUID.

### Registering URL-based MCP servers

Servers that expose an HTTP/SSE URL can be added as gateways so one Cursor connection reaches them through Context Forge. Either add them in Admin UI (**MCP Servers** → **Add New MCP Server or Gateway**) or run the script once the gateway is up:

```bash
./scripts/register-gateways.sh
```

The script is idempotent: if a gateway name already exists (e.g. after restart with the same DB), it reports "OK name (already registered)" instead of failing. The script waits up to 90s for the gateway to respond at `/health` (override with `REGISTER_GATEWAY_MAX_WAIT`). If the first URL fails (e.g. `127.0.0.1` on Docker Desktop), it retries with `localhost` or vice versa. If still unreachable, run `docker compose ps gateway` and `docker compose logs gateway`. If a gateway shows FAIL, the gateway could not initialize the remote URL (see **Troubleshooting**). Run `REGISTER_VERBOSE=1 ./scripts/register-gateways.sh` to see the API response. If **all** local gateways fail, translate containers may still be starting (first run pulls npm packages). Wait 30–60s and run the script again, or run `REGISTER_WAIT_SECONDS=30 ./scripts/register-gateways.sh`.

The script reads `scripts/gateways.txt` (one line per gateway: `Name|URL`) or the `EXTRA_GATEWAYS` env var (comma-separated). Default `gateways.txt` registers **local** servers (e.g. sequential-thinking); they start with `./start.sh`. Wait a few seconds after start, then run the script. Example remote entries:

| Name                     | URL                                          | Transport       |
| ------------------------ | -------------------------------------------- | --------------- |
| Context7                 | https://mcp.context7.com/mcp                 | Streamable HTTP |
| context-awesome          | https://www.context-awesome.com/api/mcp      | Streamable HTTP |
| prisma-remote            | https://mcp.prisma.io/mcp                    | Streamable HTTP |
| cloudflare-observability | https://observability.mcp.cloudflare.com/mcp | Streamable HTTP |
| cloudflare-bindings      | https://bindings.mcp.cloudflare.com/mcp      | Streamable HTTP |

**Auth (v0, apify-dribbble, etc.):** Add the gateway in Admin UI, then edit it and set **Passthrough Headers** (e.g. `Authorization`) or **Authentication type** OAuth so the gateway sends the token. Do not put secrets in `gateways.txt` or in the repo.

Some remote URLs may show "Failed to initialize" (e.g. context-awesome returns 406 from this gateway). See **Troubleshooting** below. Stdio-only servers (e.g. sequential-thinking) need the translate setup in the next section or stay in Cursor.

### Local servers (stdio → SSE)

The default `./start.sh` starts the gateway and these local translate services (stdio → SSE):

| Gateway name        | URL (internal)                      | Notes                                                              |
| ------------------- | ----------------------------------- | ------------------------------------------------------------------ |
| sequential-thinking | http://sequential-thinking:8013/sse | —                                                                  |
| chrome-devtools     | http://chrome-devtools:8014/sse     | —                                                                  |
| playwright          | http://playwright:8015/sse          | —                                                                  |
| magicuidesign-mcp   | http://magicuidesign-mcp:8016/sse   | @magicuidesign/mcp                                                 |
| desktop-commander   | http://desktop-commander:8017/sse   | —                                                                  |
| puppeteer           | http://puppeteer:8018/sse           | —                                                                  |
| browser-tools       | http://browser-tools:8019/sse       | —                                                                  |
| tavily              | http://tavily:8020/sse              | Set `TAVILY_API_KEY` in .env                                       |
| filesystem          | http://filesystem:8021/sse          | Set `FILESYSTEM_VOLUME` (host path) in .env; default `./workspace` |
| reactbits           | http://reactbits:8022/sse           | reactbits-dev-mcp-server                                           |
| snyk                | http://snyk:8023/sse                | Set `SNYK_TOKEN` in .env (Snyk CLI auth)                           |
| sqlite              | http://sqlite:8024/sse              | Set `SQLITE_DB_PATH` / `SQLITE_VOLUME` in .env; default `./data`   |
| github              | http://github:8025/sse              | Set `GITHUB_PERSONAL_ACCESS_TOKEN` in .env                         |

After start, run `./scripts/register-gateways.sh` to register them (or add in Admin UI with the URLs above, Transport **SSE**). Attach tools to a virtual server and use from Cursor. Use `./start.sh gateway-only` to run only the gateway.

**Servers that stay in Cursor or as remote gateways:** context-forge (gateway wrapper), browserstack, infisical-lukbot use custom scripts or tokens; run them on the host or add their HTTP URL in Admin UI if you expose them. Remote-only servers (Context7, context-awesome, prisma, cloudflare-\*, v0, apify-dribbble) add as gateways with URL; v0 and apify need Passthrough Headers or OAuth in Admin UI.

## Connect Cursor

1. Generate a JWT (e.g. 1 week):

   ```bash
   docker exec mcpgateway python3 -m mcpgateway.utils.create_jwt_token \
     --username "$PLATFORM_ADMIN_EMAIL" --exp 10080 --secret "$JWT_SECRET_KEY"
   ```

2. Add to `~/.cursor/mcp.json` (use the gateway wrapper so the host needs no Python):

   ```json
   {
     "mcpServers": {
       "context-forge": {
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "-i",
           "-e",
           "MCP_SERVER_URL=http://host.docker.internal:4444/servers/YOUR_SERVER_UUID/mcp",
           "-e",
           "MCP_AUTH=Bearer YOUR_JWT_TOKEN",
           "-e",
           "MCP_TOOL_CALL_TIMEOUT=120",
           "ghcr.io/ibm/mcp-context-forge:latest",
           "python3",
           "-m",
           "mcpgateway.wrapper"
         ]
       }
     }
   }
   ```

   On Linux add after `"-i"`: `"--add-host=host.docker.internal:host-gateway"`. Restart Cursor.

   **Alternative: URL-based (Streamable HTTP or SSE)**
   Prefer **Streamable HTTP** (path `/mcp`); the gateway expects the path and a Bearer JWT. Example with your server UUID and a token in headers:

   ```json
   "context-forge": {
     "type": "streamableHttp",
     "url": "http://localhost:4444/servers/YOUR_SERVER_UUID/mcp",
     "headers": {
       "Authorization": "Bearer YOUR_JWT_TOKEN"
     }
   }
   ```

   For **SSE** use `"type": "sse"` and path `.../servers/YOUR_SERVER_UUID/sse`. Both transports require `Authorization: Bearer YOUR_JWT_TOKEN`; without it the gateway may return 401/404 or trigger OAuth and Cursor can show "Method Not Allowed" or "Invalid OAuth error response". To avoid storing the token in mcp.json, use the docker wrapper above.

## Environment

See `.env.example`. Required: `PLATFORM_ADMIN_EMAIL`, `PLATFORM_ADMIN_PASSWORD`, `JWT_SECRET_KEY`. Never commit `.env` or secrets.

## Troubleshooting

**"Failed to initialize gateway" when adding a gateway**
The gateway (Context Forge) checks the URL when you save. Common causes: (1) Remote server down or unreachable from the container. (2) Wrong URL or path (e.g. some servers need `/sse`). (3) Server rejects the request — e.g. **Context Awesome** (`https://www.context-awesome.com/api/mcp`) returns 406 unless the client sends `Accept: application/json, text/event-stream`; if Context Forge does not send that header, initialization fails and this is an [upstream limitation](https://github.com/IBM/mcp-context-forge/issues). Workaround: use the server from a client that supports that URL (e.g. Cursor with the URL in mcp.json) or watch [Context Forge](https://github.com/IBM/mcp-context-forge) for fixes.

If you see **"Failed to initialize gateway"** or **"Unable to connect to gateway"** for all local gateways when running `./scripts/register-gateways.sh`, the translate services must listen on `0.0.0.0` so the gateway container can reach them (docker-compose already uses `--host 0.0.0.0`). If you changed the translate command, add `--host 0.0.0.0`. Otherwise, translate containers may still be starting (first run can take 30–60s while npx installs packages): wait and run the script again, or run `REGISTER_WAIT_SECONDS=30 ./scripts/register-gateways.sh`. Ensure `./start.sh` was used (not `gateway-only`) and `docker compose ps` shows the translate services running. If translate containers are **Restarting**, they may be crashing (e.g. missing `npx` in the image): rebuild with `docker compose build --no-cache sequential-thinking`, then `./start.sh stop` and `./start.sh`.

**Script hangs on "Waiting for gateway"**
The register script polls the gateway for up to 90s. On Docker Desktop for Mac, if you use `GATEWAY_URL=http://127.0.0.1:4444`, the script now tries `localhost` first. If it still hangs, set `GATEWAY_URL=http://localhost:4444` in `.env`.

**MCP Registry shows "Failed" for some servers**
When you add a server from the registry, the gateway validates it (connects and lists tools). Failure usually means the remote server is down, slow, or unreachable from the gateway. Try **Click to Retry**. If it still fails, add the gateway manually: **Gateways → New Gateway**, enter the same name and URL (e.g. `https://mcp.deepwiki.com/sse`). Servers that need OAuth show "OAuth Config Required" in the registry; after adding them, edit the gateway and set Authentication type to OAuth with the provider’s client ID, secret, and URLs (see [Context Forge OAuth docs](https://ibm.github.io/mcp-context-forge/manage/oauth/)).

**"Method Not Allowed" or "Invalid OAuth error response" when connecting Cursor to context-forge**
You are using a URL like `http://localhost:4444/servers/UUID` without a transport path. Use `/sse` for SSE or `/mcp` for streamable HTTP (e.g. `.../servers/UUID/sse`). You must also send the JWT: use the [docker wrapper](#connect-cursor) with `MCP_SERVER_URL=.../servers/UUID/mcp` and `MCP_AUTH=Bearer YOUR_JWT_TOKEN`, or add `headers: { "Authorization": "Bearer YOUR_JWT_TOKEN" }` to the SSE URL config.

**"database disk image is malformed" or "FileLock health check failed"**
The SQLite database in `./data/mcp.db` is corrupted (e.g. after a hard shutdown or disk issue). Stop the stack, remove the DB file, and restart so the gateway creates a fresh database. See [data/README.md](data/README.md#recovery-from-sqlite-corruption).

## References

- [Context Forge](https://github.com/IBM/mcp-context-forge) – Docker, stdio wrapper, translate
- [MCP Registry](https://registry.modelcontextprotocol.io) – Discover servers; add via Admin UI
