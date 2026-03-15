# MCP Gateway Makefile Reference

> Phase 3 Command Simplification reduced the Makefile from 50+ targets to **15 core targets**.
> All deprecated commands have been removed. This guide documents the current state.

## Quick Start

```bash
make help        # Show all commands and quick-start guide
make setup       # Interactive configuration wizard
make start       # Start Docker services
make register    # Register gateways and virtual servers
make status      # Check system status
```

## Core Commands

### `make setup`
Runs the interactive Python setup wizard (`scripts/setup-wizard.py`).
Configures environment variables, authentication secrets, and IDE connections.

### `make start`
Starts the full MCP Gateway stack via `./start.sh` (Docker Compose).

### `make stop`
Stops all running services via `./start.sh stop`.

### `make register [WAIT=true]`
Registers gateways and virtual servers from `config/virtual-servers.txt`.

```bash
make register            # Register and return immediately
make register WAIT=true  # Wait up to 30s for readiness
```

### `make status [FORMAT=json|detailed]`
Comprehensive system status check via `scripts/status.py`.

```bash
make status               # Human-readable summary
make status FORMAT=json    # Machine-readable JSON
make status FORMAT=detailed # Verbose diagnostics
```

### `make list-servers`
List all virtual servers with enabled (✅) / disabled (❌) status.

### `make enable-server SERVER=<name>`
Enable a virtual server in `config/virtual-servers.txt`. Run `make register` to apply.

```bash
make enable-server SERVER=cursor-search
make register
```

### `make disable-server SERVER=<name>`
Disable a virtual server. Run `make register` to apply.

```bash
make disable-server SERVER=database-dev
make register
```

### `make ide-setup [IDE=<name>] [ACTION=<action>]`
Unified IDE setup via `scripts/ide-setup.py`. Supported IDEs: `cursor`, `windsurf`, `vscode`, `claude`, `zed`, `all`.

```bash
make ide-setup IDE=cursor                       # Install Cursor config
make ide-setup IDE=all                          # Install all detected IDEs
make ide-setup IDE=windsurf ACTION=backup       # Backup Windsurf config
make ide-setup IDE=cursor ACTION=verify         # Verify Cursor setup
make ide-setup IDE=zed ACTION=use-wrapper       # Wire wrapper script
```

Available actions: `install` (default), `backup`, `restore`, `status`, `refresh-jwt`, `use-wrapper`, `verify`.

### `make auth ACTION=<action>`
Authentication management.

```bash
make auth ACTION=generate   # Generate a JWT token
make auth ACTION=check      # Validate JWT configuration in .env
make auth ACTION=refresh    # Refresh JWT (14-day expiry)
make auth ACTION=secrets    # Generate JWT_SECRET_KEY and AUTH_ENCRYPTION_SECRET
```

### `make lint`
Run all linters (Python via `ruff`, TypeScript via `npm run lint`, Shell via `shellcheck`).
Issues are reported as warnings — non-blocking.

### `make lint-strict`
Same as `make lint` but fails on any lint error (used in CI).

### `make typecheck`
Run `mypy` type checking on `tool_router/`. Non-blocking (uses `|| true`).

### `make test`
Run the full test suite with coverage.

```bash
make test   # Runs tool_router/tests/, dribbble_mcp/tests/, tests/
            # Excludes: performance/, test_rag_manager, test_security,
            # test_specialist_integration, test_github_workflows,
            # test_scalable_architecture, tests/infrastructure/
```

Coverage gate: ≥ 80% (configured in `pyproject.toml`).

### `make deps ACTION=<action>`
Dependency management.

```bash
make deps ACTION=check     # Check for npm/pip updates
make deps ACTION=update    # Interactive npm dependency update
make deps ACTION=hooks     # Install pre-commit hooks
make deps ACTION=install   # Install all npm + pip dependencies
```

### `make clean`
Remove build artifacts, `__pycache__`, `.pyc` files, coverage reports, and temporary files.

### `make quickstart`
One-command setup: `setup → start → register → status`.

### `make help [TOPIC=<topic>]`
Show command overview and quick-start guide. Use `TOPIC=setup|ide|auth|services|n8n` for topic-specific help.

## n8n Automation Targets

| Target | Description |
|--------|-------------|
| `make n8n-start` | Start n8n container |
| `make n8n-stop` | Stop n8n container |
| `make n8n-logs` | Tail n8n logs |
| `make n8n-health` | Check n8n health |
| `make n8n-backup` | Export n8n workflows |
| `make n8n-secrets` | Generate n8n webhook secrets |

## Removed Commands

The following commands from earlier versions have been removed:

| Old Command | Replacement |
|-------------|-------------|
| `make test-python` | `make test` |
| `make test-web` | `make test` |
| `make test-integration` | `make test` |
| `make test-coverage` | `make test` (coverage always on) |
| `make security` | CI pipeline handles security scanning |
| `make security-harden` | Removed |
| `make audit` | `make deps ACTION=check` |
| `make deploy` | Docker Compose / CI pipeline |
| `make npm-publish` | `npm-release-core.yml` workflow |
| `make monitor` | `make status FORMAT=detailed` |
| `make restart` | `make stop && make start` |

## .PHONY Targets

All targets are `.PHONY` (no file outputs). Current PHONY list:

```
setup start stop register status ide-setup auth lint lint-strict
test deps help clean quickstart list-servers enable-server disable-server
n8n-start n8n-stop n8n-logs n8n-backup n8n-health n8n-secrets
```
