# Development

## Dev Container (optional)

VS Code or Cursor can run the repo inside a container so lint and test work without installing shellcheck/ruff/pytest on the host.

**Prerequisites:** [Dev Containers extension](https://code.visualstudio.com/docs/devcontainers/containers), Docker or Podman.

- **"Failed to reopen folder in container" / `docker info` exit code 1:** The Docker **daemon** is not running. On macOS, start **Docker Desktop** (Applications or Spotlight). Ensure the menu bar shows Docker as running; then run **Reopen in Container** again. If the Server section of `docker info` is empty, the engine is down—use Docker menu → **Troubleshoot → Restart Docker Desktop**. See [Docker Desktop troubleshoot](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/).

1. Clone the repo and open the folder in VS Code/Cursor.
2. When prompted **Reopen in Container** (or Command Palette → **Dev Containers: Reopen in Container**), accept.
3. The container installs shellcheck, Python deps (`requirements.txt`), ruff, and pytest. Workspace is `/workspace` (repo root).
4. Inside the container: `make lint`, `make test`, and `make start` (Docker from host may need to be exposed; see your OS setup).

This matches the pattern used by [IBM MCP Context Forge](https://github.com/IBM/mcp-context-forge) (clone → code . → Reopen in Container). Our container does not run the gateway itself; use the host’s `make start` or run Docker from inside the container if Docker-in-Docker is configured.

## Local dev loop

1. Edit `config/gateways.txt`, `config/prompts.txt`, or `.env`.
2. `make start` (or `make gateway-only` for gateway only).
3. `make register`; optionally `make list-prompts` to verify prompts.
4. Test in Cursor with the URL from `make register` or Admin UI. Use the [Automatic JWT wrapper](../README.md#connect-cursor) for context-forge.

## Adding a gateway

- **No auth:** Add `Name|URL` or `Name|URL|Transport` to `config/gateways.txt`, or `EXTRA_GATEWAYS` in `.env`. Run `make register`.
- **Auth (API key, OAuth):** Add in Admin UI → edit gateway → Passthrough Headers or OAuth. See [ADMIN_UI_MANUAL_REGISTRATION.md](ADMIN_UI_MANUAL_REGISTRATION.md).

~60 tools per Cursor connection: use `config/virtual-servers.txt` (one server per line: `ServerName|gateway1,gateway2,...`), then `make register`. See [AI_USAGE.md – Tool limit](AI_USAGE.md#tool-limit-and-virtual-servers). Duplicate servers: `make cleanup-duplicates` (`CLEANUP_DRY_RUN=1` to report only).

## Prompts / resources

Format: prompts `name|description|template` ({{arg}}, `\n`); resources `name|uri|description|mime_type`. Set `REGISTER_PROMPTS=true` or `REGISTER_RESOURCES=true`, edit `config/prompts.txt` or `config/resources.txt`, run `make register`. See [scripts/README.md](../scripts/README.md) and `.env.example`.

## Troubleshooting

[README – Troubleshooting](../README.md#troubleshooting). SQLite corruption: [data/README.md](../data/README.md#recovery-from-sqlite-corruption).

## Pre-commit

Pre-commit runs secret detection (gitleaks), private-key detection, YAML/JSON checks, trailing-whitespace/EOF fixers, large-file check, merge-conflict check, and Ruff on `tool_router/` before each commit. CI still runs full lint, test, Trufflehog secret scan, and Trivy.

1. Install pre-commit: `pip install pre-commit` or `pip install -e ".[dev]"` (adds pre-commit from pyproject.toml dev deps).
2. Install the git hook: `make pre-commit-install` or `pre-commit install`.
3. (Optional) Run on the whole repo once: `pre-commit run --all-files`.

The gitleaks hook uses the default `gitleaks` id so pre-commit installs the binary; no need to install gitleaks on the system. To use a system-installed gitleaks instead, change the hook id to `gitleaks-system` in `.pre-commit-config.yaml` and install gitleaks (e.g. `brew install gitleaks` on macOS).

## Automated Maintenance

This repository includes three automated workflows that run weekly to minimize manual maintenance.

### Renovate (Dependency Updates)

**Schedule:** Monday 2 AM UTC
**Workflow:** `.github/workflows/renovate.yml`
**Config:** `.github/renovate.json`

Automatically updates:
- Python dependencies (`requirements.txt`)
- Docker images (Context Forge gateway)
- GitHub Actions

**Auto-merge behavior:**
- Patch/minor: Auto-merge after 3-day stabilization + passing CI
- Major: Manual review required (labeled `breaking-change`)
- Security: Immediate auto-merge

**Setup:**
1. Go to repository Settings → Secrets → Actions
2. Add `RENOVATE_TOKEN` secret (GitHub PAT with `repo` and `workflow` scopes)
3. Renovate will run on schedule or via manual workflow dispatch

**Monitoring:**
- Check the "Dependency Dashboard" issue for pending updates
- Review auto-merged PRs in the PR history
- Major updates appear as PRs requiring review

### MCP Server Registry Check

**Schedule:** Monday 3 AM UTC
**Workflow:** `.github/workflows/mcp-server-check.yml`
**Script:** `scripts/utils/check-mcp-registry.py`

Scans the MCP Registry API for:
- New servers not in `gateways.txt`
- Updates to existing servers
- Status of commented servers

Creates/updates a GitHub issue with findings. No secrets required.

**Manual run:**
```bash
python3 scripts/utils/check-mcp-registry.py
cat mcp-registry-report.md
```

### Docker Image Updates

**Schedule:** Monday 4 AM UTC
**Workflow:** `.github/workflows/docker-updates.yml`
**Script:** `scripts/utils/check-docker-updates.sh`

Checks IBM/mcp-context-forge for new releases and creates PRs with:
- Updated image tags in all files
- Link to release changelog
- Testing checklist

**Manual run:**
```bash
./scripts/utils/check-docker-updates.sh
cat docker-update-report.md
```

**Files updated by automation:**
- `docker-compose.yml`
- `scripts/cursor-mcp-wrapper.sh`
- `.github/workflows/ci.yml`
- `Makefile`
- `README.md`
- `docs/DEVELOPMENT.md`

### Modifying Automation

**Change schedule:**
Edit the `cron` expression in workflow files:
```yaml
schedule:
  - cron: '0 2 * * 1'  # Monday 2 AM UTC
```

**Disable auto-merge:**
In `.github/renovate.json`, set `automerge: false` for specific package rules.

**Add MCP servers to monitoring:**
Add to `gateways.txt` (active) or keep commented (monitoring only).

## Next steps (after setup)

- **CI:** Runs on push/PR (lint, test, build, Trivy image scan, smoke, secret scan). Trufflehog is pinned to `v3.93.3` in [.github/workflows/ci.yml](../.github/workflows/ci.yml). Trivy scans the tool-router image (fail on CRITICAL/HIGH, unfixed vulns ignored) and the gateway image `ghcr.io/ibm/mcp-context-forge:1.0.0-BETA-2` (report only; upstream image).
- **Lint/test locally:** Install shellcheck and ruff (e.g. `brew install shellcheck`, `pip install ruff`), then `make lint` and `make test`; or use the Dev Container above.

## Run CI-like checks locally

Run the same checks CI runs so failures are caught before push:

| CI job | Local command |
|--------|----------------|
| Lint | `make lint` (requires shellcheck and ruff; or use Dev Container) |
| Test | `make test` (requires Python 3.12, `pip install -r requirements.txt pytest`) |
| Docker build + gateway smoke | `docker compose build sequential-thinking tool-router`, then create a minimal `.env` (see CI workflow), `docker compose up -d gateway`, then `curl -sf http://localhost:4444/health` (requires Docker and a pullable gateway image tag) |
| Trivy | `trivy image mcp-gateway-tool-router:latest` (optional; install [Trivy](https://github.com/aquasecurity/trivy) or run in Dev Container) |
| Secret scan | `pre-commit run --all-files` (includes secret checks), or run Trufflehog manually with base/head refs |

Gateway smoke requires the gateway image to be pullable (see [docker-compose.yml](../docker-compose.yml)); if the image tag is missing or changed upstream, update the tag in `docker-compose.yml` and `scripts/cursor-mcp-wrapper.sh`.
- **Gateway updates:** Watch [IBM/mcp-context-forge](https://github.com/IBM/mcp-context-forge) releases; update the gateway image tag in `docker-compose.yml` and `scripts/cursor-mcp-wrapper.sh` when upgrading.
- **Python deps:** Bump versions in `requirements.txt` / `pyproject.toml` and run `make test`; rebuild tool-router image if needed.
- **Cursor:** Keep `GATEWAY_JWT` set for cursor-router; run `make verify-cursor-setup` if the IDE shows "Error" or "No server info found".
