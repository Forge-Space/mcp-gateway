# Using the gateway with AI

Map of registered tools to typical use cases. Use a virtual server in Cursor to expose tools; when you have many gateways, use multiple virtual servers so each connection stays under the tool limit (see below).

## Using the MCP Gateway with the tool router in Cursor IDE

To use the **MCP Gateway with the tool router** in Cursor (one connection that routes tasks to the right upstream tool):

1. **Prerequisites:** Docker, Docker Compose. Copy `.env.example` to `.env`, set `PLATFORM_ADMIN_EMAIL`, `PLATFORM_ADMIN_PASSWORD`, `JWT_SECRET_KEY`, and `AUTH_ENCRYPTION_SECRET` (or run `make generate-secrets`).
2. **Start the stack:** From the repo run `make start` (gateway + tool-router and other services).
3. **Register gateways and virtual server:** Run `make register`. This registers the tool-router and creates the **cursor-router** virtual server; it writes `data/.cursor-mcp-url` for the wrapper. Do not set `REGISTER_CURSOR_MCP_SERVER_NAME` if you want the default cursor-router.
4. **Set GATEWAY_JWT:** Run `make jwt`, copy the token, and add `GATEWAY_JWT=<token>` to `.env`. The tool-router needs this to call the gateway API. Refresh periodically (e.g. weekly).
5. **Point Cursor at the wrapper:** Run `make use-cursor-wrapper` so `~/.cursor/mcp.json` uses `scripts/cursor/mcp-wrapper.sh` (generates a fresh JWT per connection; no token in mcp.json; sets 2-minute MCP timeout).
6. **Pre-pull image (recommended):** Run `make cursor-pull` once so the first Cursor connection does not time out while the Context Forge image downloads.
7. **Restart Cursor:** Fully quit Cursor (Cmd+Q / Alt+F4) and reopen.

In Cursor you will see the **context-forge** (or **user-context-forge**) MCP server with the tool-router’s tools (e.g. `execute_task`). Describe a task in chat; the router selects the best upstream tool and runs it via the gateway. To confirm setup: run `make verify-cursor-setup` from the repo. For manual JWT or URL-based config, see [How to add the gateway to Cursor](#how-to-add-the-gateway-to-cursor-cursormcpmcpjson) and [README – Connect Cursor](../README.md#connect-cursor).

## Tool limit and virtual servers

Cursor (and some MCP clients) warn or misbehave when a single connection exposes **more than ~60 tools**. With many gateways registered, one virtual server that includes every tool can exceed this.

**Approach:** Use **multiple virtual servers**, each with a subset of gateways (up to 60 tools per server). Define them in `config/virtual-servers.txt`:

- Format: one line per server, `ServerName|gateway1,gateway2,...` (gateway names must match `config/gateways.txt`).
- After editing, run `make register`. The script creates or updates each server and prints a Cursor URL per server.
- In Cursor, connect to **one** URL depending on the task (e.g. `cursor-default` for general dev, `cursor-search` for search/docs, `cursor-browser` for browser automation). You can add more than one virtual server as separate MCP entries in Cursor if you want to switch between them.

If `virtual-servers.txt` is absent, the script creates a single virtual server (`default`) with all tools—fine when you have few gateways. See [scripts/README.md](../scripts/README.md) and the main [README](../README.md#registering-url-based-mcp-servers).

### Single entry point (router)

The **cursor-router** virtual server exposes only the **tool-router** gateway (1–2 tools: `execute_task`, optional `search_tools`). The Cursor wrapper uses cursor-router by default; ensure `GATEWAY_JWT` is set in `.env` (run `make jwt` and paste; refresh periodically) so the router can call the gateway API. When you call `execute_task` with a task description, the router fetches all tools from the gateway, picks the best match by keyword scoring (name + description), and invokes it via the gateway API. Use this when you want one Cursor connection that routes to the best tool without hitting the 60-tool limit. Tool selection in v1 is keyword-based (no LLM/embeddings).

| Use case                                | Gateway / tool                                                                                            |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Planning, complex reasoning             | sequential-thinking                                                                                       |
| Docs lookup                             | Context7, context-awesome (if configured)                                                                 |
| Web search                              | tavily (set `TAVILY_API_KEY` in .env)                                                                     |
| Local files                             | filesystem (set `FILESYSTEM_VOLUME` in .env)                                                              |
| Browser / UI automation                 | playwright, puppeteer, browser-tools, chrome-devtools                                                     |
| Database                                | sqlite (local), prisma-remote (if added)                                                                  |
| Discovery                               | MCP Gateway’s radar_search or [MCP Registry](https://registry.modelcontextprotocol.io) to find more tools |
| Single entry point (route to best tool) | cursor-router virtual server (tool-router gateway; requires `GATEWAY_JWT`)                                |

Auth-required gateways (v0, apify-dribbble, Context7 API key, etc.) must be configured in Admin UI with Passthrough Headers or OAuth; see [ADMIN_UI_MANUAL_REGISTRATION.md](ADMIN_UI_MANUAL_REGISTRATION.md).

### Which virtual server should I use?

| If you want…                                         | Use this virtual server                   | Notes                                                                                                                                                                                                             |
| ---------------------------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **One connection that picks the right tool for you** | **cursor-router** (tool-router, ~2 tools) | Default for the Cursor wrapper. Set `GATEWAY_JWT` in `.env` (run `make jwt`). No 60-tool limit; router calls the gateway for you.                                                                                 |
| **General dev: files, search, browser, reasoning**   | **cursor-default**                        | sequential-thinking, filesystem, tavily, playwright, desktop-commander, chrome-devtools (under 60 tools). Set `REGISTER_CURSOR_MCP_SERVER_NAME=cursor-default` and run `make register` to point the wrapper here. |
| **Only web/search and docs**                         | **cursor-search**                         | tavily (and similar). Lightweight.                                                                                                                                                                                |
| **Only browser and UI automation**                   | **cursor-browser**                        | playwright, puppeteer, browser-tools, chrome-devtools, desktop-commander (~80 tools; may hit limits in some clients).                                                                                             |

Server names in the Admin UI may differ if you changed them (e.g. custom-default, custom-browser); use the **Description** column (“Tools from: …”) to match. Use **View Details** on a server to see its exact tool list.

### How to add the gateway to Cursor (`~/.cursor/mcp.json`)

**Option A – Wrapper (recommended, no JWT in mcp.json)**
From the mcp-gateway repo (with `.env` set and gateway running):

1. Run `make register` so `data/.cursor-mcp-url` exists (optionally set `REGISTER_CURSOR_MCP_SERVER_NAME` for a server other than cursor-router).
2. Run **`make use-cursor-wrapper`**. This sets the context-forge (or user-context-forge) entry in `~/.cursor/mcp.json` to use `scripts/cursor/mcp-wrapper.sh`; the wrapper reads the URL from `data/.cursor-mcp-url` and uses a fresh JWT.
3. For **cursor-router**: set `GATEWAY_JWT` in `.env` (run `make jwt`, paste the token). Refresh it periodically (e.g. weekly).
4. Fully quit Cursor (Cmd+Q / Alt+F4) and reopen.

**Option B – Manual URL + JWT**
Add an entry with the server URL and a Bearer token. Get the URL from the Admin UI (Virtual Servers → server → URL, e.g. `http://localhost:4444/servers/fa8ef86945da4b399fed241a8d0bfd4f`) and append `/mcp` or `/sse`. Get a JWT with `make jwt`. Example (Streamable HTTP):

```json
"context-forge": {
  "type": "streamableHttp",
  "url": "http://localhost:4444/servers/YOUR_SERVER_UUID/mcp",
  "headers": { "Authorization": "Bearer YOUR_JWT_TOKEN" }
}
```

Refresh the token regularly (e.g. `make refresh-cursor-jwt` or paste a new `make jwt`). Full details and docker-wrapper variant: [README – Connect Cursor](../README.md#connect-cursor).

### Context-forge shows "Error" or logs "NO SERVER INFO FOUND" / "Server not yet created"

Those messages mean the MCP client (Cursor) could not get server info from the gateway. Fix in order:

1. **Check setup:** From the repo run `make verify-cursor-setup`. It checks gateway health, `data/.cursor-mcp-url`, server ID, Context Forge image, and gateway reachability from Docker.
2. **Ensure URL file and server exist:** Run `make start` then `make register`. That (re)creates virtual servers and writes `data/.cursor-mcp-url`. If you ran `make reset-db` earlier, the old server UUID is gone—register again.
3. **cursor-router only:** Set `GATEWAY_JWT` in `.env` (run `make jwt`, paste the token). Without it the server has 0 tools and the gateway can report no server info.
4. **Reconnect Cursor:** Fully quit Cursor (Cmd+Q / Alt+F4) and reopen. Reload Window is not enough.

If it still fails: from the repo run `make verify-cursor-setup` and follow its output; see also [README troubleshooting](../README.md#troubleshooting) and [ADMIN_UI_MANUAL_REGISTRATION.md](ADMIN_UI_MANUAL_REGISTRATION.md).

### Context-forge logs "Request timed out" (MCP error -32001)

Cursor’s default MCP server-creation timeout is 60 seconds. The wrapper starts a Docker container that must connect to the gateway; if the Context Forge image is not cached, the first run can exceed 60s and Cursor reports -32001. Fix:

1. **Pre-pull the image:** From the repo run `make cursor-pull` so the image is cached before Cursor starts the wrapper.
2. **Increase client timeout:** Run `make use-cursor-wrapper` again; it sets `"timeout": 120000` (2 minutes) in `~/.cursor/mcp.json` for the context-forge entry. Optionally set `CURSOR_MCP_TIMEOUT_MS=180000` in `.env` before running it for 3 minutes.
3. **Fully restart Cursor:** Quit Cursor (Cmd+Q / Alt+F4) and reopen.
