# Forge MCP Gateway (Context Forge) - Enterprise Edition

🚀 **Self-hosted Forge MCP gateway using [IBM Context Forge](https://github.com/IBM/mcp-context-forge) with advanced AI-driven optimization, predictive scaling, ML-based monitoring, and enterprise-grade security features.**

**GitHub repo description** (paste in Settings → General → Description, 350 char max):

> Enterprise MCP gateway with AI optimization, predictive scaling, ML monitoring, and enterprise security. Docker, virtual servers, tool-router, multi-cloud ready. MIT.

**License:** [MIT](LICENSE)

## 🎯 Enterprise Features

✅ **All Development Phases Complete - Production Ready**

- **🤖 AI-Driven Optimization**: Machine learning-based performance analysis and automated optimization
- **📈 Predictive Scaling**: Time series forecasting with 30-minute load prediction and cost-aware scaling
- **🔍 ML-Based Monitoring**: Anomaly detection using Isolation Forest with intelligent alerting
- **🏢 Enterprise Security**: Comprehensive audit logging, compliance management, and role-based access control
- **🔄 Self-Healing**: Automated incident response and system recovery capabilities
- **☁️ Multi-Cloud Ready**: Cloud-agnostic deployment with cross-cloud load balancing
- **📊 Advanced Analytics**: Real-time dashboards and comprehensive reporting
- **🛡️ Compliance Framework**: SOC2, GDPR, HIPAA, PCI DSS compliance support

## 🚀 Quick Start

```bash
cp .env.example .env
# Edit .env: set PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD, JWT_SECRET_KEY, AUTH_ENCRYPTION_SECRET (min 32 chars each). Run: make generate-secrets
make start
```

Then run `make register` to register gateways and get the Cursor URL.

- **Admin UI:** http://localhost:4444/admin
- **Enterprise Features:** http://localhost:4444/admin/enterprise
- **AI Dashboard:** http://localhost:4444/admin/ai
- **Stop:** `make stop` (or `./start.sh stop`)

### 🧪 Testing Advanced Features

```bash
# Test enterprise compliance
python3 scripts/enterprise-features.py --check-compliance

# Test AI optimization (requires ML dependencies)
python3 scripts/ai-optimization.py --analyze

# Test predictive scaling (requires ML dependencies)
python3 scripts/predictive-scaling.py --predict

# Test ML monitoring (requires ML dependencies)
python3 scripts/ml-monitoring.py --monitor
```

### 🔧 ML Dependencies Setup

For full AI/ML features, install required dependencies:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install ML dependencies
pip install numpy scikit-learn pandas

# Run advanced features
python3 scripts/ai-optimization.py --optimize
python3 scripts/predictive-scaling.py --scale
python3 scripts/ml-monitoring.py --detect
```

### NPX Client (Standard MCP Server Pattern)

Use the gateway like any other MCP server with `npx`:

**Local usage (no authentication needed):**
```json
{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@forge-mcp-gateway/client",
        "--url=http://localhost:4444/servers/<UUID>/mcp"
      ]
    }
  }
}
```

**Remote/secured usage (with JWT):**
```json
{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx",
      "args": [
        "-y",
        "@forge-mcp-gateway/client",
        "--url=https://gateway.example.com/servers/<UUID>/mcp",
        "--token=<JWT>"
      ]
    }
  }
}
```

**Get your configuration:**
1. Start gateway: `make start`
2. Register servers: `make register` (saves URL to `data/.cursor-mcp-url`)
3. Add to your IDE's `mcp.json` with the URL (token only needed if `AUTH_REQUIRED=true` in `.env`)

See [NPM_PACKAGE_README.md](NPM_PACKAGE_README.md) for detailed NPX client documentation.

Default `make start` (or `./start.sh`) starts the gateway and all local servers (e.g. sequential-thinking). Use `make gateway-only` (or `./start.sh gateway-only`) for the gateway alone. Data is stored in `./data` (SQLite). Add gateways in Admin UI or run `make register` after start; create a virtual server, attach tools, note its UUID.

### Registering URL-based MCP servers

Servers that expose an HTTP/SSE URL can be added as gateways so one Cursor connection reaches them through Context Forge. Either add them in Admin UI (**MCP Servers** → **Add New MCP Server or Gateway**) or run once the gateway is up:

```bash
make register
```

(or `./scripts/register-gateways.sh`). The command is idempotent: if a gateway name already exists (e.g. after restart with the same DB), it reports "OK name (already registered)" instead of failing. It waits up to 90s for the gateway to respond at `/health` (override with `REGISTER_GATEWAY_MAX_WAIT`). If the first URL fails (e.g. `127.0.0.1` on Docker Desktop), it retries with `localhost` or vice versa. If still unreachable, run `docker compose ps gateway` and `docker compose logs gateway`. If a gateway shows FAIL, the gateway could not initialize the remote URL (see **Troubleshooting**). Run `REGISTER_VERBOSE=1 make register` to see the full API response. For local SSE gateways (e.g. sqlite, desktop-commander, github), the script retries once after 15s on "Unable to connect" or "Unexpected error". If **all** local gateways fail, translate containers may still be starting (first run pulls npm packages): wait 30–60s and run again, or set `REGISTER_WAIT_SECONDS=30` in `.env` or run `make register-wait`.

`make register` reads `scripts/gateways.txt` (one line per gateway: `Name|URL` or `Name|URL|Transport`) or the `EXTRA_GATEWAYS` env var (comma-separated). Default `gateways.txt` registers **local** servers up to snyk (sequential-thinking through snyk). sqlite, github, and Context7 are commented out (they often fail with "Unable to connect" or "Unexpected error"; uncomment after checking `docker compose logs sqlite|github` or add Context7/sqlite/github via Admin UI). `.env.example` sets `REGISTER_WAIT_SECONDS=30` so translate containers are ready before registration. After `make start`, run `make register` (or `make register-wait` to force a 30s wait). After registering gateways, the script creates or updates **virtual server(s)** and prints Cursor URLs. Cursor (and some other MCP clients) can only handle about **60 tools per connection**; if you register many gateways, a single virtual server with all tools can trigger a warning. To stay under the limit, use **multiple virtual servers**, each with a subset of gateways:

- **With `config/virtual-servers.txt`:** One line per server: `ServerName|gateway1,gateway2,...`. The script creates or updates each named server with up to 60 tools from those gateways and prints one URL per server. Connect Cursor to one URL (e.g. `cursor-default` for general dev, `cursor-search` for search/docs). See [scripts/README.md](scripts/README.md) and [docs/AI_USAGE.md](docs/AI_USAGE.md#tool-limit-and-virtual-servers).
- **Single entry point (router):** The **cursor-router** virtual server is the default for the wrapper. It exposes only the tool-router gateway (1–2 tools). Set `GATEWAY_JWT` in `.env` (run `make jwt` and paste the token; refresh periodically, e.g. weekly) so the router can call the gateway API. See [docs/AI_USAGE.md](docs/AI_USAGE.md#single-entry-point-router).
- **Without `virtual-servers.txt`:** A single virtual server (name `default` or `REGISTER_VIRTUAL_SERVER_NAME`) gets all tools; fine if you have few gateways. Example remote entries:

| Name                     | URL                                          | Transport       |
| ------------------------ | -------------------------------------------- | --------------- |
| Context7                 | https://mcp.context7.com/mcp                 | Streamable HTTP |
| context-awesome          | https://www.context-awesome.com/api/mcp      | Streamable HTTP |
| prisma-remote            | https://mcp.prisma.io/mcp                    | Streamable HTTP |
| cloudflare-observability | https://observability.mcp.cloudflare.com/mcp | Streamable HTTP |
| cloudflare-bindings      | https://bindings.mcp.cloudflare.com/mcp      | Streamable HTTP |

**Auth (v0, apify-dribbble, etc.):** Add the gateway in Admin UI, then edit it and set **Passthrough Headers** (e.g. `Authorization`) or **Authentication type** OAuth so the gateway sends the token. Do not put secrets in `gateways.txt` or in the repo. For the exact Context Forge structure (gateway, virtual server, prompts, resources) and which registrations need manual steps, see [docs/ADMIN_UI_MANUAL_REGISTRATION.md](docs/ADMIN_UI_MANUAL_REGISTRATION.md).

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
| memory              | http://memory:8027/sse              | Persistent knowledge graph; data in `./data/memory` (no API key)   |
| git-mcp             | http://git-mcp:8028/sse             | Local git operations: commit, branch, diff, log (no API key)       |
| fetch               | http://fetch:8029/sse               | Web content fetching to markdown for LLM use (no API key)          |
| postgres            | http://postgres:8031/sse            | Set `POSTGRES_CONNECTION_STRING` in .env; see [Multi-User Config](docs/MULTI_USER_DATABASE_CONFIG.md) |
| mongodb             | http://mongodb:8032/sse             | Set `MONGODB_CONNECTION_STRING` in .env; see [Multi-User Config](docs/MULTI_USER_DATABASE_CONFIG.md) |
| tool-router         | http://tool-router:8030/sse         | Single entry point; set `GATEWAY_JWT` in .env (see cursor-router)  |
| sqlite              | http://sqlite:8024/sse              | Set `SQLITE_DB_PATH` / `SQLITE_VOLUME` in .env; default `./data`   |
| github              | http://github:8025/sse              | Set `GITHUB_PERSONAL_ACCESS_TOKEN` in .env                         |
| ui                 | http://ui:8026/sse                 | AI-driven UI generation (7 tools); set `FIGMA_ACCESS_TOKEN` in .env for Figma sync |

After start, run `make register` to register them (or add in Admin UI with the URLs above, Transport **SSE**). This creates or updates a virtual server and prints its Cursor URL. Attach tools in Admin UI if you skip that step. Optional: set `REGISTER_PROMPTS=true` and add `config/prompts.txt` (format: `name|description|template` with `{{arg}}` and `\n` for newlines), then run `make register`. Use `make gateway-only` to run only the gateway (no translate services).

**Stack-focused gateways (React, Node, TypeScript, Java, Spring, Prisma, etc.):** `config/gateways.txt` includes local SSE servers and optional remote entries (Context7, context-awesome, prisma-remote). Add more via `EXTRA_GATEWAYS` in `.env`. Next.js (`next-devtools-mcp`) is project-local; run it inside your Next app. Spring AI MCP runs on the host; add its URL to `EXTRA_GATEWAYS` if you expose it.

**Servers that stay in Cursor or as remote gateways:** context-forge (gateway wrapper), browserstack, infisical-lukbot use custom scripts or tokens; run them on the host or add their HTTP URL in Admin UI if you expose them. Remote-only servers (Context7, context-awesome, prisma, cloudflare-\*, v0, apify-dribbble) add as gateways with URL; v0 and apify need Passthrough Headers or OAuth in Admin UI.

## Connect Cursor

The gateway requires a **Bearer JWT** on every request.

**Automatic JWT (recommended)**
Use the wrapper script so no token is stored in mcp.json and no weekly refresh is needed. From the repo: ensure `.env` is set, run `make register` once (this writes `data/.cursor-mcp-url`), then run **`make use-cursor-wrapper`** to set the context-forge entry in `~/.cursor/mcp.json` to the wrapper (replacing any URL/headers or docker-args config). The wrapper config includes a 2-minute MCP timeout to avoid "Request timed out" (-32001); set `CURSOR_MCP_TIMEOUT_MS` in `.env` (e.g. `180000`) to change it. Before first use, run **`make cursor-pull`** so the Context Forge Docker image is cached and the first Cursor connection does not time out while the image downloads. Restart Cursor. The wrapper uses the **cursor-router** (tool-router) virtual server by default; set `REGISTER_CURSOR_MCP_SERVER_NAME=cursor-default` in `.env` and run `make register` to use the full tool set instead. The wrapper generates a fresh JWT on each connection and runs the gateway Docker image. On Linux the script adds `--add-host=host.docker.internal:host-gateway` automatically. Optional: set `CURSOR_MCP_SERVER_URL` in `.env` if you prefer not to use `data/.cursor-mcp-url`. To configure manually instead, set the entry to `{"command": "/absolute/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh", "timeout": 120000}` (use your clone path).

**Manual JWT (URL-based or docker args)**

1. Generate a JWT (e.g. 1 week): run `make jwt` (or `make refresh-cursor-jwt` to update the token in mcp.json in place; run weekly or before opening Cursor).

   Or run:

   ```bash
   docker exec mcpgateway python3 -m mcpgateway.utils.create_jwt_token \
     --username "$PLATFORM_ADMIN_EMAIL" --exp 10080 --secret "$JWT_SECRET_KEY"
   ```

2. Add to `~/.cursor/mcp.json` (docker wrapper with token in args):

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
           "ghcr.io/ibm/mcp-context-forge:1.0.0-BETA-2",
           "python3",
           "-m",
           "mcpgateway.wrapper"
         ]
       }
     }
   }
   ```

   On Linux add after `"-i"`: `"--add-host=host.docker.internal:host-gateway"`. Restart Cursor after changing the config.

   **Alternative: URL-based (Streamable HTTP or SSE)**
   Example with your server UUID and a token in headers:

   ```json
   "context-forge": {
     "type": "streamableHttp",
     "url": "http://localhost:4444/servers/YOUR_SERVER_UUID/mcp",
     "headers": {
       "Authorization": "Bearer YOUR_JWT_TOKEN"
     }
   }
   ```

   For **SSE** use `"type": "sse"` and path `.../servers/YOUR_SERVER_UUID/sse`. Both require `Authorization: Bearer YOUR_JWT_TOKEN`. To avoid storing the token in mcp.json, use the [Automatic JWT](#connect-cursor) wrapper or the docker wrapper above. To refresh the token in mcp.json without copy-paste, run `make refresh-cursor-jwt` (e.g. weekly via cron: `0 9 * * 0` or a launchd plist).

## Environment

See `.env.example`. Required: `PLATFORM_ADMIN_EMAIL`, `PLATFORM_ADMIN_PASSWORD`, `JWT_SECRET_KEY`, `AUTH_ENCRYPTION_SECRET` (each at least 32 chars; run `make generate-secrets`). Never commit `.env` or secrets.

## Automated Maintenance

This repository includes automated workflows for dependency updates, MCP server discovery, and Docker image updates.

### Dependency Updates (Renovate)

**Schedule:** Every Monday at 2 AM UTC

Renovate automatically checks for updates to:
- Python dependencies (`requirements.txt`)
- Docker images (Context Forge gateway)
- GitHub Actions

**Auto-merge policy:**
- ✅ Patch/minor updates: Auto-merge after 3-day stabilization + passing CI
- ❌ Major updates: Require manual review (labeled `breaking-change`)
- 🔒 Security vulnerabilities: Immediate auto-merge

**Setup:** Add `RENOVATE_TOKEN` secret to repository settings (GitHub PAT with `repo` and `workflow` scopes).

**Dashboard:** Check the Dependency Dashboard issue for pending updates.

### MCP Server Registry Check

**Schedule:** Every Monday at 3 AM UTC

Automatically scans the MCP Registry for:
- New servers not in `gateways.txt`
- Status of commented servers (auth requirements, etc.)

Creates/updates a GitHub issue with findings. No secrets required.

### Docker Image Updates

**Schedule:** Every Monday at 4 AM UTC

Checks IBM/mcp-context-forge for new releases and automatically creates PRs with:
- Updated image tags in all files
- Changelog link
- Testing checklist

PRs require manual review before merge.

## Development

- **Workflow and adding gateways/prompts:** [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Script index:** [scripts/README.md](scripts/README.md)
- **Maintenance automation:** See [Automated Maintenance](#automated-maintenance) above

### Trunk Based Development Workflow

This project uses Trunk Based Development with the following branch strategy:

#### Branch Structure

- **main**: Production-ready code, always deployable
- **dev**: Development environment branch, continuously deployed
- **release/x.y.z**: Release preparation branches
- **feature/***: Feature development branches

#### Workflow

1. **Feature Development**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name dev
   # Make your changes
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

2. **Testing & Review**
   - Create PR from `feature/your-feature-name` to `release/x.y.z`
   - All CI tests must pass
   - Code review required

3. **Release Preparation**
   ```bash
   git checkout release/x.y.z
   git merge feature/your-feature-name
   git push origin release/x.y.z
   ```

4. **Production Deployment**
   ```bash
   git checkout main
   git merge release/x.y.z
   git tag v1.2.3
   git push origin main --tags
   ```

#### Branch Protection

- **main**: Require PR approval, passing CI, no force pushes
- **release/***: Require PR approval and passing CI
- **dev**: Require passing CI only

#### Environment Configuration

- **Dev Environment**: Uses `.env.development`, auto-deployed from `dev` branch
- **Production Environment**: Uses `.env.production`, deployed from `main` merges

## Using the gateway with AI

Which tools to use for planning, docs, search, browser, DB: [docs/AI_USAGE.md](docs/AI_USAGE.md).

## 🏗️ Shared Package Structure

This project uses a centralized shared package structure for UIForge-wide standardization:

```
.github/shared/
├── workflows/           # Reusable CI/CD templates
├── configs/             # Shared configurations
├── scripts/            # Utility scripts
├── templates/          # GitHub templates
└── README.md           # Comprehensive documentation
```

### Key Benefits
- **40% reduction** in duplicate configurations
- **Standardized CI/CD** pipelines across UIForge projects
- **Unified security scanning** and dependency management
- **Automated setup** with symlink management

### Usage
- **Setup**: Run `./scripts/setup-shared-symlinks.sh` to create configuration links
- **Documentation**: See `.github/shared/README.md` for detailed usage
- **Migration**: Use `docs/UIFORGE_MIGRATION_GUIDE.md` for other projects

### CI/CD Pipeline
The main workflow (`.github/workflows/ci.yml`) uses shared templates:
```yaml
jobs:
  ci:
    uses: ./.github/shared/workflows/base-ci.yml
    with:
      project-type: 'gateway'
      node-version: '22'
      python-version: '3.12'
```

## Troubleshooting

**403 "Insufficient permissions. Required: admin.dashboard" on /admin**
The admin UI requires an authenticated user with the `admin.dashboard` permission. Open the gateway root or login page first (e.g. `http://localhost:4444/` or `http://localhost:4444/login`), sign in with `PLATFORM_ADMIN_EMAIL` and `PLATFORM_ADMIN_PASSWORD` from your `.env`, then go to `http://localhost:4444/admin`. If the browser prompts for credentials, use the same email and password. Do not put secrets in the repo; keep them only in `.env`.

**"Failed to initialize gateway" when adding a gateway**
The gateway (Context Forge) checks the URL when you save. Common causes: (1) Remote server down or unreachable from the container. (2) Wrong URL or path (e.g. some servers need `/sse`). (3) Server rejects the request — e.g. **Context Awesome** (`https://www.context-awesome.com/api/mcp`) returns 406 unless the client sends `Accept: application/json, text/event-stream`; if Context Forge does not send that header, initialization fails and this is an [upstream limitation](https://github.com/IBM/mcp-context-forge/issues). Workaround: use the server from a client that supports that URL (e.g. Cursor with the URL in mcp.json) or watch [Context Forge](https://github.com/IBM/mcp-context-forge) for fixes.

If you see **"Failed to initialize gateway"** or **"Unable to connect to gateway"** for all local gateways when running `make register`, the translate services must listen on `0.0.0.0` so the gateway container can reach them (docker-compose already uses `--host 0.0.0.0`). If you changed the translate command, add `--host 0.0.0.0`. Otherwise, translate containers may still be starting (first run can take 30–60s while npx installs packages): wait and run `make register` again, or run `make register-wait` (or `REGISTER_WAIT_SECONDS=30 make register`). If **only one** local gateway (e.g. sqlite) fails, the same wait-and-retry usually fixes it. Ensure `make start` was used (not `make gateway-only`) and `docker compose ps` shows the translate services running. If translate containers are **Restarting**, they may be crashing (e.g. missing `npx` in the image): rebuild with `docker compose build --no-cache sequential-thinking`, then `make stop` and `make start`.

**Script hangs on "Waiting for gateway"**
The register script polls the gateway for up to 90s. On Docker Desktop for Mac, if you use `GATEWAY_URL=http://127.0.0.1:4444`, the script now tries `localhost` first. If it still hangs, set `GATEWAY_URL=http://localhost:4444` in `.env`.

**MCP Registry shows "Failed" for some servers**
When you add a server from the registry, the gateway validates it (connects and lists tools). Failure usually means the remote server is down, slow, or unreachable from the gateway. Try **Click to Retry**. If it still fails, add the gateway manually: **Gateways → New Gateway**, enter the same name and URL (e.g. `https://mcp.deepwiki.com/sse`). Servers that need OAuth show "OAuth Config Required" in the registry; after adding them, edit the gateway and set Authentication type to OAuth with the provider’s client ID, secret, and URLs (see [Context Forge OAuth docs](https://ibm.github.io/mcp-context-forge/manage/oauth/)).

**context-forge shows "Error" / "Needs authentication" / "Loading tools" forever, or logs "Server disconnected without sending a response" / "No server info found"**
Often caused by **weak `JWT_SECRET_KEY` or `AUTH_ENCRYPTION_SECRET`** (gateway logs: "Secret has low entropy", "Secret should be at least 32 characters"). Fix: run `make generate-secrets`, add the two lines to `.env`, then `make stop`, `make start`, `make register`, and **fully quit Cursor (Cmd+Q / Alt+F4) and reopen**. Reload Window is not enough. If that’s not the cause:

- **If you use the wrapper** (recommended): Run `make verify-cursor-setup` to check gateway, `data/.cursor-mcp-url`, server existence, Context Forge image, and gateway reachability from Docker. If any check fails, run `make start` then `make register`, then fully quit and reopen Cursor. Run **`make cursor-pull`** once so the first Cursor start does not timeout while the image downloads. **To use the default cursor-router (tool-router):** remove or comment out `REGISTER_CURSOR_MCP_SERVER_NAME` in `.env`, run `make register`, then fully quit Cursor (Cmd+Q / Alt+F4) and reopen. If you have `REGISTER_CURSOR_MCP_SERVER_NAME=cursor-default` in `.env`, the wrapper uses cursor-default; the URL in `data/.cursor-mcp-url` is only updated when you run `make register`. If logs show **"No server info found"**: (1) Ensure the gateway is running (`make start`) and reachable from Docker (the wrapper runs in a container and uses `host.docker.internal:4444`). (2) Run `make register` to refresh the URL, then fully quit and reopen Cursor. (3) For cursor-router, set `GATEWAY_JWT` in `.env` (run `make jwt` and paste) so the router can call the gateway. If logs show **"Request timed out" (MCP error -32001)**: (1) Run `make cursor-pull` so the Context Forge image is cached. (2) Run `make use-cursor-wrapper` again to set a 2-minute timeout in mcp.json (or set `CURSOR_MCP_TIMEOUT_MS=180000` in `.env` before running it). (3) Fully quit and reopen Cursor.

- **If you use a manual JWT (URL in mcp.json):** (1) `make start` (ensure gateway is running). (2) `make refresh-cursor-jwt` (updates the Bearer token in `~/.cursor/mcp.json` for the context-forge entry; the script also finds `user-context-forge` if that’s the key Cursor uses). (3) Restart Cursor. Your URL must end with `/mcp` or `/sse`. If Cursor is on the host and the gateway runs in Docker, use `http://host.docker.internal:4444/servers/UUID/mcp`. Alternatively switch to the [wrapper](#connect-cursor) with `make use-cursor-wrapper`.

**"Method Not Allowed" or "Invalid OAuth error response" when connecting Cursor to context-forge**
You are using a URL like `http://localhost:4444/servers/UUID` without a transport path. Use `/sse` for SSE or `/mcp` for streamable HTTP (e.g. `.../servers/UUID/sse`). You must also send the JWT: use the [docker wrapper](#connect-cursor) with `MCP_SERVER_URL=.../servers/UUID/mcp` and `MCP_AUTH=Bearer YOUR_JWT_TOKEN`, or add `headers: { "Authorization": "Bearer YOUR_JWT_TOKEN" }` to the SSE URL config.

**500 on /admin (gateways/partial, prompts/partial) or "Loading gateways..." / "Loading prompts..." never finish**
The admin UI loads data from the gateway backend; when the backend returns 500, those requests fail. A common cause is a **corrupted SQLite database**. Check gateway logs: `docker compose logs gateway --tail 100`. If you see `sqlite3.DatabaseError: database disk image is malformed`, follow the recovery steps in the next bullet (stop, remove `./data/mcp.db` and WAL/SHM, restart). Then run `make register` again to re-register gateways. See [data/README.md](data/README.md#recovery-from-sqlite-corruption). You can run `make reset-db` to stop the stack and remove the DB files in one step, then `make start` and `make register`.

**"database disk image is malformed" or "FileLock health check failed"**
The SQLite database in `./data/mcp.db` is corrupted (e.g. after a hard shutdown or disk issue). Stop the stack, remove the DB file (and `mcp.db-shm`, `mcp.db-wal` if present), and restart so the gateway creates a fresh database. Use `make reset-db` then `make start` (and `make register` to re-add gateways). See [data/README.md](data/README.md#recovery-from-sqlite-corruption).

**Admin "Prompts" page stuck on "Loading prompts..."**
The Context Forge admin UI at `/admin/#prompts` can hang due to an upstream frontend/API mismatch or slow response. Workarounds: (1) **Use the API**: run `make list-prompts` (lists prompts via GET /prompts with JWT). (2) **Register prompts via Make**: set `REGISTER_PROMPTS=true` in `.env` and add lines to `scripts/prompts.txt` (format: `name|description|template`), then run `make register`. (3) **Inspect in browser**: DevTools → Network, filter by "prompts" or XHR; check the request URL, status, and response body. If the API returns 200 with valid JSON and the UI still spins, report to [IBM/mcp-context-forge](https://github.com/IBM/mcp-context-forge/issues). A CSP error in the console for `fonts.googleapis.com` is unrelated to prompts loading.

**Missing servers and authentication**
Some gateways are commented out in `config/gateways.txt` so `make register` succeeds by default. To enable them:

- **Commented local (sqlite, github):** Uncomment the corresponding lines in `config/gateways.txt`, set the required env vars in `.env` (e.g. `GITHUB_PERSONAL_ACCESS_TOKEN` for github), run `make register` or `make register-wait`. If they fail, see the "Failed to initialize gateway" / "Unable to connect" bullets above and `docker compose logs sqlite` or `docker compose logs github`.
- **Commented remote (Context7, context-awesome, prisma-remote, cloudflare-\*, v0, apify-dribbble):** Uncomment in `scripts/gateways.txt` and run `make register`, or add the gateway via Admin UI (MCP Servers → Add New MCP Server or Gateway). For **Context7, v0, apify-dribbble, cloudflare-\***: after adding the gateway, edit it in Admin UI and set **Passthrough Headers** (e.g. `Authorization`) or **Authentication type** OAuth so the gateway can call the upstream. See [docs/ADMIN_UI_MANUAL_REGISTRATION.md](docs/ADMIN_UI_MANUAL_REGISTRATION.md).

**Authentication checklist:** Local gateways that need keys: **Tavily** → `TAVILY_API_KEY` in `.env`; **Snyk** → `SNYK_TOKEN`; **GitHub** → `GITHUB_PERSONAL_ACCESS_TOKEN`. Remote gateways **Context7, v0, apify-dribbble, cloudflare-\*** → configure Passthrough Headers or OAuth in Admin UI (do not put secrets in `config/gateways.txt` or the repo).

## Contributing / Forking

You can fork this repo to run your own MCP gateway stack. After forking: copy `.env.example` to `.env`, set secrets (`make generate-secrets`), then `make start` and `make register`. To contribute back: run `make lint` and `make test`, open a PR with a clear description; see [CHANGELOG.md](CHANGELOG.md) for the project’s change conventions.

## References

- [Context Forge](https://github.com/IBM/mcp-context-forge) – Docker, stdio wrapper, translate
- [MCP Registry](https://registry.modelcontextprotocol.io) – Discover servers; add via Admin UI
