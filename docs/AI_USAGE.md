# Using the gateway with AI

Map of registered tools to typical use cases. Use a virtual server in Cursor to expose tools; when you have many gateways, use multiple virtual servers so each connection stays under the tool limit (see below).

## Tool limit and virtual servers

Cursor (and some MCP clients) warn or misbehave when a single connection exposes **more than ~60 tools**. With many gateways registered, one virtual server that includes every tool can exceed this.

**Approach:** Use **multiple virtual servers**, each with a subset of gateways (up to 60 tools per server). Define them in `scripts/virtual-servers.txt`:

- Format: one line per server, `ServerName|gateway1,gateway2,...` (gateway names must match `gateways.txt`).
- After editing, run `make register`. The script creates or updates each server and prints a Cursor URL per server.
- In Cursor, connect to **one** URL depending on the task (e.g. `cursor-default` for general dev, `cursor-search` for search/docs, `cursor-browser` for browser automation). You can add more than one virtual server as separate MCP entries in Cursor if you want to switch between them.

If `virtual-servers.txt` is absent, the script creates a single virtual server (`default`) with all tools—fine when you have few gateways. See [scripts/README.md](../scripts/README.md) and the main [README](../README.md#registering-url-based-mcp-servers).

### Single entry point (router)

The **cursor-router** virtual server exposes only the **tool-router** gateway (1–2 tools: `execute_task`, optional `search_tools`). When you call `execute_task` with a task description, the router fetches all tools from the gateway, picks the best match by keyword scoring (name + description), and invokes it via the gateway API. Use this when you want one Cursor connection that routes to the best tool without hitting the 60-tool limit. Set `GATEWAY_JWT` in `.env` (run `make jwt` and paste; refresh periodically). Tool selection in v1 is keyword-based (no LLM/embeddings).

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
