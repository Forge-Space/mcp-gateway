# Manual registration via Context Forge Admin UI

This document describes **registrations that must be done manually** in the Context Forge Admin UI (e.g. gateways that require authentication, or when you prefer not to use `scripts/register-gateways.sh`). It uses the **exact request structure** required by the [Context Forge API](https://ibm.github.io/mcp-context-forge/manage/api-usage/).

**References:** [Context Forge API Usage](https://ibm.github.io/mcp-context-forge/manage/api-usage/), [OAuth Integration](https://ibm.github.io/mcp-context-forge/manage/oauth/), [Context Forge Docs](https://ibm.github.io/mcp-context-forge/).

---

## When to use the Admin UI

- **Gateways that need auth:** v0, apify-dribbble, Context7 (API key), or any server that expects `Authorization` or custom headers. Configure Passthrough Headers or OAuth in the gateway edit screen.
- **Remote gateways** you prefer not to put in `EXTRA_GATEWAYS` or `scripts/gateways.txt` (e.g. to avoid committing URLs).
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

Use this UUID in Cursor’s `mcp.json` as `.../servers/<UUID>/mcp` or `.../servers/<UUID>/sse`.

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

**Auth:** v0 and apify-dribbble require token/API key or OAuth; configure in the gateway edit screen. Context7 often requires an API key (Passthrough Header `Authorization: Bearer <key>`). See [Context Forge OAuth](https://ibm.github.io/mcp-context-forge/manage/oauth/) for OAuth setup.

---

## Troubleshooting: Prompts page infinite loading

If the Admin UI **Prompts** page stays on "Loading prompts...", the frontend may be failing to handle the API response (upstream Context Forge). You can:

- **List prompts via script:** from repo root run `./scripts/list-prompts.sh` (uses .env and gateway JWT; works in any shell). **Create prompts via API:** `POST /prompts` (see [Context Forge API Usage](https://ibm.github.io/mcp-context-forge/manage/api-usage/)); JWT from gateway container as in `register-gateways.sh`.
- **Register prompts via script:** set `REGISTER_PROMPTS=true` in `.env`, add lines to `scripts/prompts.txt`, run `./scripts/register-gateways.sh`.
- **Check Network tab:** In DevTools → Network, find the prompts request; confirm URL, status code, and response shape. If the API returns 200 with valid JSON and the UI still spins, report to [IBM/mcp-context-forge](https://github.com/IBM/mcp-context-forge/issues).
