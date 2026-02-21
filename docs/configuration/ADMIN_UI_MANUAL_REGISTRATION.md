# Manual registration via MCP Gateway Admin UI

This document describes **registrations that must be done manually** in the MCP Gateway Admin UI (e.g. gateways that require authentication, or when you prefer not to use `scripts/register-gateways.sh`). It uses the **exact request structure** required by the [MCP Gateway API](https://ibm.github.io/mcp-gateway/manage/api-usage/).

**References:** [MCP Gateway API Usage](https://ibm.github.io/mcp-gateway/manage/api-usage/), [OAuth Integration](https://ibm.github.io/mcp-gateway/manage/oauth/), [MCP Gateway Docs](https://ibm.github.io/mcp-gateway/).

---

## When to use the Admin UI

- **Gateways that need auth:** v0, apify-dribbble, Context7 (API key), or any server that expects `Authorization` or custom headers. Configure Passthrough Headers or OAuth in the gateway edit screen.
- **Remote gateways** you prefer not to put in `EXTRA_GATEWAYS` or `config/gateways.txt` (e.g. to avoid committing URLs).
- **Virtual server:** create or edit a server and attach tools; Cursor connects to `.../servers/<SERVER_UUID>/mcp` or `.../sse`.
- **Prompts / resources:** optional; add via Admin UI or API if you use them.

Local gateways (sequential-thinking, playwright, sqlite, etc.) are normally registered by `./scripts/register-gateways.sh`; you can also add them manually using the same structures below.

---

## 1. Gateway (MCP server)

Gateways are upstream MCP servers or peer gateways. The Admin UI “Add New MCP Server or Gateway” form and the API expect the same logical fields.

### 1.1 Request body (API)

`POST /gateways` with `Content-Type: application/json`:

| Field         | Type   | Required | Description                                                                                    |
| ------------- | ------ | -------- | ---------------------------------------------------------------------------------------------- |
| `name`        | string | Yes      | Unique identifier (slug); used in tool names (e.g. `gateway__tool_name`).                      |
| `url`         | string | Yes      | Full URL of the MCP endpoint (e.g. `https://mcp.example.com/mcp` or `http://host:port/sse`).   |
| `description` | string | No       | Human-readable description.                                                                    |
| `transport`   | string | No       | One of: `STREAMABLEHTTP`, `SSE`, `STDIO`, `WEBSOCKET`. Omit to let the gateway infer from URL. |

**Transport by URL:**

- Path ends with `/mcp` or Streamable HTTP → use `STREAMABLEHTTP`.
- Path ends with `/sse` → use `SSE`.

**Example (no auth):**

```json
{
  "name": "prisma-remote",
  "url": "https://mcp.prisma.io/mcp",
  "description": "Prisma MCP server for database tools",
  "transport": "STREAMABLEHTTP"
}
```

**Example (local SSE):**

```json
{
  "name": "sequential-thinking",
  "url": "http://sequential-thinking:8013/sse",
  "description": "Sequential thinking MCP server",
  "transport": "SSE"
}
```

### 1.2 Gateways that require manual auth (Admin UI)

After adding the gateway, **edit it** and set authentication so the gateway can call the upstream server.

| Gateway                      | URL                                                                      | Transport      | Auth requirement                                |
| ---------------------------- | ------------------------------------------------------------------------ | -------------- | ----------------------------------------------- |
| **Context7**                 | `https://mcp.context7.com/mcp`                                           | STREAMABLEHTTP | API key: set Passthrough Headers (see below).   |
| **v0**                       | `https://mcp.v0.dev`                                                     | STREAMABLEHTTP | Vercel/token: Passthrough Headers or OAuth.     |
| **apify-dribbble**           | `https://mcp.apify.com/sse?actors=practicaltools/apify-dribbble-scraper` | SSE            | Apify API token: Passthrough Headers or OAuth.  |
| **prisma-remote**            | `https://mcp.prisma.io/mcp`                                              | STREAMABLEHTTP | Depends on Prisma Cloud; configure if prompted. |
| **cloudflare-observability** | `https://observability.mcp.cloudflare.com/mcp`                           | STREAMABLEHTTP | Cloudflare auth if required.                    |
| **cloudflare-bindings**      | `https://bindings.mcp.cloudflare.com/mcp`                                | STREAMABLEHTTP | Cloudflare auth if required.                    |

**Do not put secrets in `gateways.txt` or in the repo.** Configure them only in the Admin UI (or via API with secrets from env).

### 1.3 Passthrough Headers (Bearer / API key)

When the upstream server expects a Bearer token or API key:

1. In Admin UI: **Gateways** → select the gateway → **Edit**.
2. Set **Authentication type** (or equivalent) to use **Passthrough Headers** (or “Custom headers”).
3. Add a header that the upstream expects, for example:
   - **Header name:** `Authorization`
   - **Header value:** `Bearer <your-api-key-or-token>`

Context Forge may expose this as “Passthrough Headers” or “X-Upstream-Authorization” depending on version; the effect is that the gateway forwards this header to the MCP server. Store the secret in a secure place (env var, secrets manager); do not commit it.

### 1.4 OAuth (Admin UI)

For OAuth 2.0 (e.g. v0, or a provider that uses Authorization Code or Client Credentials):

1. **Gateways** → gateway → **Edit**.
2. Set **Authentication type** = **OAuth**.
3. Choose **Grant type:** `client_credentials` or `authorization_code`.
4. Fill:
   - **Client ID**
   - **Client Secret** (stored encrypted)
   - **Token URL**
   - **Scopes** (space-separated)
   - For Authorization Code: **Authorization URL**, **Redirect URI** (e.g. `https://your-gateway-host/oauth/callback`).

**Example OAuth config (API shape, for reference):**

```json
{
  "name": "GitHub MCP",
  "url": "https://github-mcp.example.com/sse",
  "auth_type": "oauth",
  "oauth_config": {
    "grant_type": "authorization_code",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "authorization_url": "https://github.com/login/oauth/authorize",
    "token_url": "https://github.com/login/oauth/access_token",
    "redirect_uri": "https://gateway.example.com/oauth/callback",
    "scopes": ["repo", "read:user"]
  }
}
```

Use the Admin UI fields that map to this structure; exact field names may vary by UI version.

---

## 2. Virtual server

A virtual server groups tools (from one or more gateways) into a single endpoint. Cursor connects to:

- Streamable HTTP: `http://localhost:4444/servers/<SERVER_UUID>/mcp`
- SSE: `http://localhost:4444/servers/<SERVER_UUID>/sse`

**Which server to use:** See [AI_USAGE.md – Which virtual server should I use?](AI_USAGE.md#which-virtual-server-should-i-use) for a short guide (router vs default vs search vs browser).

### 2.1 Create server (API)

`POST /servers`:

```json
{
  "server": {
    "name": "default",
    "description": "All registered tools",
    "associated_tools": ["<tool_id_1>", "<tool_id_2>"]
  }
}
```

- `name`: unique label.
- `description`: optional.
- `associated_tools`: array of **tool IDs** from `GET /tools` (e.g. `GET /tools?limit=0&include_pagination=false` then collect `id` for each tool).

Tool IDs are returned by the API (e.g. after gateways sync); they are opaque strings. To attach all tools: list tools, collect all `id` values, then pass them in `associated_tools`.

### 2.2 Update server (API)

`PUT /servers/<SERVER_ID>`:

```json
{
  "name": "default",
  "description": "All registered tools",
  "associated_tools": ["<tool_id_1>", "<tool_id_2>"]
}
```

In the Admin UI you typically select the server, then add/remove tools by ID or by list selection; the UI sends the same structure under the hood.

### 2.3 Get server UUID

- **Admin UI:** **Servers** (or **Virtual servers**) → select the server → copy the **ID** or the URL path containing the UUID.
- **API:** `GET /servers?include_pagination=false` and read `id` for the desired server.
- **CLI:** From repo root run `make list-servers` to list virtual servers (id, name, tool count) via the API.

Use this UUID in Cursor’s `mcp.json` as `.../servers/<UUID>/mcp` or `.../servers/<UUID>/sse`.

**Note:** The Admin UI “Virtual MCP Servers” page may show “No tags found” or “Showing 0 - 0 of 0 items” even when virtual servers exist (e.g. created via `make register` or `POST /servers`). That can be a display bug in the Admin UI. To confirm servers exist, use `make list-servers` or call `GET /servers` with an admin JWT.

---

## 3. Prompt (optional)

Prompts are Jinja2-style templates with arguments. Register only if you use them.

### 3.1 Request body (API)

`POST /prompts`:

```json
{
  "prompt": {
    "name": "code-review",
    "description": "Review code for best practices",
    "template": "Review the following code and suggest improvements:\n\n{{code}}",
    "arguments": [
      {
        "name": "code",
        "description": "Code to review",
        "required": true
      }
    ]
  }
}
```

- `name`: unique identifier.
- `template`: body with `{{variable}}` placeholders.
- `arguments`: array of `{ "name", "description", "required" }` for each placeholder.

---

## 4. Resource (optional)

Resources are URI-based data sources. Register only if you use them.

### 4.1 Request body (API)

`POST /resources`:

```json
{
  "resource": {
    "name": "config-file",
    "uri": "file:///etc/config.json",
    "description": "Application configuration file",
    "mime_type": "application/json",
    "content": "{\"key\": \"value\"}"
  }
}
```

- `name`: unique identifier.
- `uri`: URI of the resource.
- `mime_type`: optional (e.g. `application/json`, `text/plain`).
- `content`: optional inline content.

---

## 5. Quick reference: manual gateways

Copy-paste–friendly list for **remote gateways** you add in Admin UI. Fill auth (Passthrough Headers or OAuth) after creating the gateway.

| Name                     | URL                                                                      | Transport      |
| ------------------------ | ------------------------------------------------------------------------ | -------------- |
| Context7                 | `https://mcp.context7.com/mcp`                                           | STREAMABLEHTTP |
| context-awesome          | `https://www.context-awesome.com/api/mcp`                                | STREAMABLEHTTP |
| prisma-remote            | `https://mcp.prisma.io/mcp`                                              | STREAMABLEHTTP |
| cloudflare-observability | `https://observability.mcp.cloudflare.com/mcp`                           | STREAMABLEHTTP |
| cloudflare-bindings      | `https://bindings.mcp.cloudflare.com/mcp`                                | STREAMABLEHTTP |
| v0                       | `https://mcp.v0.dev`                                                     | STREAMABLEHTTP |
| apify-dribbble           | `https://mcp.apify.com/sse?actors=practicaltools/apify-dribbble-scraper` | SSE            |

**Auth:** v0 and apify-dribbble require token/API key or OAuth; configure in the gateway edit screen. Context7 often requires an API key (Passthrough Header `Authorization: Bearer <key>`). See [MCP Gateway OAuth](https://ibm.github.io/mcp-gateway/manage/oauth/) for OAuth setup.

---

## Troubleshooting: Virtual MCP Servers page stuck on "Loading servers..."

If the Admin UI **Virtual MCP Servers** page shows a spinner and "Loading servers..." indefinitely:

- **Common cause: corrupted SQLite database.** The gateway’s GET /servers request fails with 500 and the UI never gets a valid response. Check gateway logs: `docker compose logs gateway --tail 80`. If you see `sqlite3.DatabaseError: database disk image is malformed`, the DB is corrupted.
- **Fix:** Run `make reset-db` (stops the stack and removes `./data/mcp.db` and WAL/SHM files), then `make start` and `make register`. The gateway will create a fresh DB and you can re-add gateways; the Virtual MCP Servers page should then load (empty or with servers). See [data/README.md](data/README.md) and README troubleshooting.
- If the logs show a different error, follow **Troubleshooting: GET /servers returns 500** below; you can still use the **Add New Server** form on the same page to create a server manually.

---

## Troubleshooting: GET /servers returns 500 or virtual server create fails

If `make list-servers` returns **HTTP 500** or `make register` reports **virtual server create failed (HTTP 500)**:

- **Scripts now retry** – `list-servers.sh` and `register-gateways.sh` retry `GET /servers` without query params when the first request returns 500; some gateway versions fail on `limit=0&include_pagination=false`.
- **Delayed retries** – For 5xx or 408, `register-gateways.sh` does up to 2 extra attempts after a configurable delay (default 5s). Set `REGISTER_GET_SERVERS_RETRY_DELAY=5` in `.env` (or `0` to disable).
- **Create when GET fails (opt-in)** – If GET /servers is still non-200 after all retries, set `REGISTER_VIRTUAL_SERVER_CREATE_WHEN_GET_FAILS=true` to attempt create-only (POST) for virtual servers; no update, possible duplicates if you run register again. See `.env.example`.
- **Check gateway logs** – Run `docker compose logs gateway` and look for Python tracebacks or errors around the `/servers` route. Report issues to [IBM/mcp-gateway](https://github.com/IBM/mcp-gateway/issues).
- **Verbose register** – Run `REGISTER_VERBOSE=1 make register` to see the first few lines of failed POST/PUT response bodies.

If virtual server create fails with **HTTP 400**:

- The script prints the gateway’s response body (validation error). It then retries with a flat body and `associatedTools` (camelCase), unless the response contains "This transaction is inactive" (see below).
- If both attempts fail, check that tool IDs are valid (e.g. run `curl -s -H "Authorization: Bearer $(make jwt)" "$GATEWAY_URL/tools?include_pagination=false" | jq '.[0:3]'` and confirm each tool has an `id`).

If the gateway returns **"Failed to register server: This transaction is inactive"** (HTTP 400):

- This is a known upstream issue in some mcp-gateway versions: the gateway DB session/transaction is not active when `POST /servers` is called (often when `GET /servers` has already returned 500).
- **Workarounds:** (1) Create virtual servers manually in the Admin UI: open the gateway URL (e.g. `http://localhost:4444`), go to Virtual MCP Servers, add a server and attach tools by gateway or tool ID. (2) Retry `make register` after a minute. When `GET /servers` returns non-200, the script skips virtual server create/update and prints the same guidance.

**Same error in the Admin UI:** If you see "Failed to register server: This transaction is inactive" when clicking **Add Server** in the Virtual Servers page, the same upstream bug is affecting the UI. Try: (1) **Use fewer servers and tools** — the UI warns that more than 12 MCP servers or more than 6 tools can impact performance; start with one gateway and a small set of tools, then add more. (2) Refresh the page and try again. (3) Restart the gateway (`docker compose restart gateway`), wait ~30s, then try adding a minimal virtual server (one MCP server, few tools). If it still fails, report at [IBM/mcp-gateway issues](https://github.com/IBM/mcp-gateway/issues) with your gateway version and that the error occurs both via API and in the Admin UI.

---

## Troubleshooting: Prompts page infinite loading

If the Admin UI **Prompts** page stays on "Loading prompts...", the frontend may be failing to handle the API response (upstream MCP Gateway). You can:

- **List prompts via script:** from repo root run `./scripts/list-prompts.sh` (uses .env and gateway JWT; works in any shell). **Create prompts via API:** `POST /prompts` (see [MCP Gateway API Usage](https://ibm.github.io/mcp-gateway/manage/api-usage/)); JWT from gateway container as in `register-gateways.sh`.
- **Register prompts via script:** set `REGISTER_PROMPTS=true` in `.env`, add lines to `config/prompts.txt`, run `./scripts/register-gateways.sh`.
- **Check Network tab:** In DevTools → Network, find the prompts request; confirm URL, status code, and response shape. If the API returns 200 with valid JSON and the UI still spins, report to [IBM/mcp-gateway](https://github.com/IBM/mcp-gateway/issues).
