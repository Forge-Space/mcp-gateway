# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Fixed

- **AI Router robustness improvements** - Multiple bug fixes and enhancements to AI-powered tool selection:
  - **Ollama upgrade**: Update Ollama image from `0.5.6` to `0.16.1` for latest features and security fixes
  - **Timeout alignment**: Align `ROUTER_AI_TIMEOUT_MS` default to 5000ms across docker-compose.yml and .env.example
  - **Model persistence**: Add `OLLAMA_KEEP_ALIVE=24h` environment variable to prevent model unloading and cold-start latency
  - **Configurable confidence threshold**: Add `ROUTER_AI_MIN_CONFIDENCE` config field (default 0.3) for tunable AI selection threshold
  - **Brace escaping in prompts**: Escape literal braces in user input to prevent KeyError in prompt formatting
  - **HTTPError response handling**: Guard against AttributeError when `e.response` is None in Ollama error handling
  - **Improved JSON extraction**: Replace fragile brace-counting with `json.JSONDecoder().raw_decode()` for robust nested JSON parsing
  - **Centralized logging**: Replace stdlib logger with project's centralized `get_logger()` in selector.py
  - **Simplified availability timeout**: Remove unnecessary `getattr()` call, compute timeout directly as `max(0.2, timeout_seconds * 0.5)`
  - **Config initialization safety**: Move `ToolRouterConfig.load_from_environment()` to `main()` to prevent import-time crashes
  - **Initialization guards**: Add defensive checks in `execute_task()` and `search_tools()` to prevent AttributeError on uninitialized config
  - **Enhanced exception logging**: Add `exc_info=True` to broad exception handlers in server.py for full stack traces
  - **Lazy logging**: Replace f-string logs with %-style formatting to avoid unnecessary string evaluation
  - **Input validation**: Clamp `ai_confidence` and `ai_weight` to [0.0, 1.0] range in `calculate_hybrid_score()`
  - **Error handling refactor**: Separate parse and range validation for `ROUTER_AI_WEIGHT` to preserve specific ValueError messages
  - **Health status consistency**: Use `HealthStatus` enum instead of string literals in health.py API responses
  - **Improved docstrings**: Remove redundant "Args: No parameters" section from `AIRouterConfig.load_from_environment()`

- **Documentation improvements**:
  - Add blank lines before code blocks in AI_ROUTER_GUIDE.md to satisfy markdownlint MD031
  - Add language specifiers (`text`) to log code fences for proper syntax highlighting

- **Test improvements**:
  - Strengthen truncation assertion in `test_format_tool_list_truncate_long_description` to verify exact 150-char limit
  - Add response object to mocked HTTPError in `test_select_tool_http_error` to match production code
  - Add verification that tool list is truncated to 100 in `test_select_tool_too_many_tools`
  - Add return type hints (`-> None`) to all test methods in `test_health.py` for strict mypy compliance
  - Mock `AIToolSelector` creation in `test_get_ai_router_health_no_selector_provided` to avoid network calls
  - Strengthen `ai_usage_rate` assertion in `test_metrics.py` with exact calculation and tolerance check

### Added

- **AI Router with Ollama Integration**: Intelligent tool selection using local LLM
  - Hybrid scoring combining AI confidence (70%) and keyword matching (30%)
  - Automatic fallback to keyword matching on timeout or low confidence
  - Configurable via environment variables (model, timeout, weight, min_confidence)
  - Support for llama3.2:3b (default), mistral:7b, and other Ollama models
  - Docker Compose integration with Ollama service
  - Comprehensive test coverage (>85%) for AI selector and prompts
  - Detailed operational guide at `docs/operations/AI_ROUTER_GUIDE.md`

- **AI Router Observability & Management**:
  - MCP tool `get_ai_router_metrics_tool` for real-time performance metrics
    - Selection method counts (AI vs keyword)
    - AI confidence statistics
    - Fallback event tracking
    - Usage rate calculations
  - MCP tool `get_ai_router_health_tool` for health monitoring
    - Overall status (healthy/degraded/unhealthy)
    - Ollama service availability checks
    - Configuration snapshot
    - Issue detection and reporting
  - Comprehensive test coverage (96.67%) for API endpoints
  - Updated operational guide with observability best practices

- **CodeQL Security Scanning** - Added GitHub CodeQL workflow for automated security analysis
  - Scans JavaScript/TypeScript and Python code
  - Runs on push, pull requests, and weekly schedule
  - Uses security-extended and security-and-quality query suites
  - Satisfies branch protection requirements for Code Scanning

## [1.5.0] - 2026-02-14

### New Features

- **uiforge-mcp server** – New local translate service (port 8026) providing 7 AI-driven UI generation tools: `scaffold_full_application` (React/Next.js/Vue/Angular + Tailwind + Shadcn/ui), `generate_ui_component` (style-aware components with audit), `generate_prototype` (interactive HTML prototypes with navigation), `generate_design_image` (SVG/PNG mockups via satori + resvg), `fetch_design_inspiration` (extract colors/typography from URLs), `figma_context_parser` (read Figma nodes → Tailwind mapping), `figma_push_variables` (write design tokens to Figma Variables API). Plus 1 MCP resource: `application://current-styles` (session-scoped design context). Set `FIGMA_ACCESS_TOKEN` in `.env` for Figma tools. Added to `cursor-default` virtual server. Built from [uiforge-mcp](https://github.com/LucasSantana-Dev/uiforge-mcp) via `Dockerfile.uiforge`.
- **MCP servers for AI development** – 5 new free MCP servers added to the gateway for enhanced AI-assisted development workflows:
  - **memory** (port 8027) – Anthropic reference server (`@modelcontextprotocol/server-memory`). Persistent knowledge graph that stores and retrieves context across sessions. No API key required.
  - **git-mcp** (port 8028) – Anthropic reference server (`@modelcontextprotocol/server-git`). Local git operations (commit, branch, diff, log) complementing the GitHub gateway. No API key required.
  - **fetch** (port 8029) – Anthropic reference server (`@modelcontextprotocol/server-fetch`). Web content fetching and markdown conversion for LLM consumption. No API key required.
  - **Context7** (remote) – Up-to-date library/framework documentation lookup (`https://mcp.context7.com/mcp`). Free tier works without API key; configure key in Admin UI Passthrough Headers for higher rate limits. Uncommented in `gateways.txt`.
  - **DeepWiki** (remote) – AI-powered codebase documentation for any public GitHub repo (`https://mcp.deepwiki.com/mcp`). Free, no authentication required.
- **cursor-default expanded** – `virtual-servers.txt` cursor-default now includes memory and fetch gateways alongside existing ones. `git-mcp` moved to dedicated `cursor-git` virtual server to stay under Cursor's 60-tool limit.
- **Port overrides** – `.env` optional vars: `MEMORY_PORT`, `GIT_MCP_PORT`, `FETCH_PORT`.

### Fixed

- **memory persistence** – Mount `./data/memory` volume and set `MEMORY_FILE_PATH=/data/memory.jsonl` so the knowledge graph survives container restarts. Added `MEMORY_VOLUME` to `.env.example`.
- **git-mcp volume** – Mount `GIT_REPO_VOLUME` (default `./workspace`) into the container and pass `--repository /repos` so the server can access a git repository. Added `GIT_REPO_VOLUME` to `.env.example` and updated README.

## [0.1.1] - 2025-02-14

### Code Refactoring

- **Clean Code Refactoring: Improved Naming Conventions**
  - Refactored Python codebase for better readability and maintainability
    - `tool_router/core/config.py`: Renamed `jwt` → `jwt_auth_token`, `from_env()` → `load_from_environment()`, `timeout_ms` → `timeout_milliseconds`, `max_retries` → `maximum_retry_attempts`
    - `tool_router/core/server.py`: Improved variable names in `execute_task` and `search_tools` functions
    - `tool_router/gateway/client.py`: Renamed `_headers()` → `_build_authentication_headers()`, `_make_request()` → `_execute_http_request_with_retry()`
    - `tool_router/args/builder.py`: Renamed `TASK_PARAM_NAMES` → `COMMON_TASK_PARAMETER_NAMES`, improved variable clarity
    - `tool_router/scoring/matcher.py`: Renamed `_tokens()` → `_extract_normalized_tokens()`, `_expand_with_synonyms()` → `_enrich_tokens_with_synonyms()`, `score_tool()` → `calculate_tool_relevance_score()`, `pick_best_tools()` → `select_top_matching_tools()`
    - `tool_router/observability/health.py`: Updated to use new config property names
    - `tool_router/observability/metrics.py`: Renamed `duration_ms` → `duration_milliseconds`, improved variable names
  - Refactored TypeScript client for consistency
    - `src/index.ts`: Renamed `TIMEOUT_MS` → `REQUEST_TIMEOUT_MILLISECONDS`, `gatewayRequest()` → `sendGatewayRequest()`, improved variable names
  - Refactored shell scripts for better clarity
    - `scripts/lib/gateway.sh`: Renamed `compose_cmd()` → `detect_docker_compose_command()`, `get_jwt()` → `generate_or_retrieve_jwt_token()`, `wait_for_health()` → `wait_for_healthy_gateway_status()`, `fetch_servers_list()` → `fetch_registered_servers_list()`
    - `scripts/gateway/register.sh`: Updated to use renamed functions
  - Maintained backward compatibility with aliases where appropriate
  - All changes follow Clean Code principles: intention-revealing names, pronounceable names, searchable names, no mental mapping

### Added

- **Phase 3.3: Observability and Health Checks**
  - Comprehensive observability module (`tool_router/observability/`)
  - Health check system with component-level monitoring
    - Gateway connectivity checks with latency tracking
    - Configuration validation
    - Readiness and liveness probes
    - JSON-serializable health check results
  - Structured logging infrastructure
    - Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Structured log formatting for easy parsing
    - Log context manager for adding contextual fields
  - Metrics collection system
    - Thread-safe metrics collector
    - Timing metrics with statistical summaries (avg, min, max)
    - Counter metrics for tracking events
    - Timing context manager for automatic duration tracking
    - Global metrics singleton for application-wide tracking
  - Server instrumentation
    - Integrated logging and metrics into `execute_task` and `search_tools`
    - Detailed performance tracking for all operations
    - Error tracking with categorized counters
    - Tool selection metrics
  - Comprehensive test coverage (25 tests, 100% pass rate)
  - Monitoring documentation (`docs/operations/MONITORING.md`)
    - Health check usage examples
    - Metrics collection patterns
    - Integration examples (FastAPI, Prometheus, Docker)
    - Troubleshooting guides

- **Phase 3.2: Hierarchical Documentation Structure**
  - Created organized documentation hierarchy with 7 categories
  - Added comprehensive documentation index (`docs/README.md`)
  - New documentation structure:
    - `docs/setup/` - Installation and IDE configuration
    - `docs/architecture/` - System architecture and design
    - `docs/configuration/` - Configuration and deployment
    - `docs/development/` - Development and contributing
    - `docs/operations/` - Operations and maintenance
    - `docs/migration/` - Migration and upgrade guides
    - `docs/tools/` - CI/CD and automation tools
  - New documentation files:
    - `docs/setup/INSTALLATION.md` - Complete installation guide
    - `docs/architecture/OVERVIEW.md` - System architecture overview
    - `docs/architecture/VIRTUAL_SERVERS.md` - Virtual servers guide
  - Reorganized existing documentation into logical categories
  - Added quick links and common tasks sections
  - Improved navigation with cross-references

- **Test Coverage Boost to 100%**
  - Added 10 comprehensive error path tests for gateway client
  - Coverage for all testable code modules: 100%
  - Total test suite: 55 tests (45 existing + 10 new)
  - Error scenarios covered:
    - HTTP 5xx server errors with retry logic
    - HTTP 4xx client errors (no retry)
    - Network errors (URLError) with exponential backoff
    - Timeout errors with retry
    - JSON decode errors (immediate failure)
    - Mixed error scenarios across retries
    - Successful retry after transient failures
  - Updated coverage configuration to exclude MCP runtime (tested via integration)

- **Phase 3.1: Monorepo Build System**
  - Unified build system coordinating TypeScript and Python packages
  - Makefile targets for cross-platform development workflow
    - `make build`: Build both TypeScript client and Python package
    - `make clean`: Clean all build artifacts
    - `make install`: Install all dependencies
    - `make dev`: Complete development environment setup
    - `make check`: Run all quality checks (lint + test)
    - `make ci`: Full CI pipeline simulation
  - Enhanced CI/CD workflow with dedicated build job
  - NPM configuration (`.npmrc`) for strict engine and exact versions
  - Build system configuration in `pyproject.toml`
  - Cross-platform compatibility using `python3 -m` for all Python tools

- **Phase 1: Foundation Architecture Improvements**
  - Restructured `tool_router` package with modular organization:
    - `tool_router/core/` - Server and configuration
    - `tool_router/gateway/` - Gateway client
    - `tool_router/tools/` - Tool execution logic
    - `tool_router/scoring/` - Tool matching and scoring
    - `tool_router/args/` - Argument building
    - `tool_router/tests/unit/` - Unit tests
    - `tool_router/tests/integration/` - Integration tests
  - Created centralized configuration management (`tool_router/core/config.py`)
    - Type-safe `GatewayConfig` and `ToolRouterConfig` dataclasses
    - Environment variable validation with clear error messages
    - Configurable timeouts, retries, and tool selection parameters
  - Standardized shell script error handling (`scripts/lib/errors.sh`)
    - Standard exit codes for common failure scenarios
    - Dependency checking utilities
    - Gateway and Docker health checks
    - Environment and file validation helpers
- **Phase 2: Quality & Testing Improvements**
  - Implemented dependency injection for gateway client
    - Created `HTTPGatewayClient` class with constructor injection
    - Added `GatewayClient` protocol for interface abstraction
    - Removed direct `os.environ` access from client code
    - Maintained backward compatibility with module-level functions
  - Comprehensive integration test suite (12 tests)
    - End-to-end workflow tests (tool selection → argument building → execution)
    - Gateway client integration tests with retry logic validation
    - Configuration validation and error handling tests
    - Mock-based tests for network failures and edge cases
  - Enhanced CI/CD pipeline
    - Multi-version Python testing (3.9, 3.10, 3.11, 3.12)
    - Code coverage reporting with pytest-cov (67% coverage)
    - Codecov integration for coverage tracking
    - Coverage configuration in `pyproject.toml`
  - Comprehensive unit test coverage (45 total tests)
    - Configuration management tests (11 tests for GatewayConfig and ToolRouterConfig)
    - 100% coverage for args, scoring, and config modules
    - 79% coverage for gateway client with error path testing

### Changed

- Moved test files to `tool_router/tests/unit/` directory
- Updated all imports to use new module structure
- Updated `pyproject.toml` test paths to `tool_router/tests`
- Enhanced `.env.example` with tool-router configuration variables
- **IDE-Agnostic Refactoring** – Removed Cursor-specific coupling to support any MCP-compatible IDE:
  - Renamed `scripts/cursor/` → `scripts/mcp-client/`
  - Environment variables: `CURSOR_*` → `MCP_CLIENT_*` (backward compatible)
  - File paths: `data/.cursor-mcp-url` → `data/.mcp-client-url`
  - Makefile targets: `cursor-pull` → `mcp-client-pull` (aliased for compatibility)
  - Virtual servers: `cursor-router` → `mcp-router`, `cursor-default` → `mcp-default`
  - Function names: `get_context_forge_key()` → `get_mcp_client_key()` (aliased)
  - All old variables and targets continue to work via backward compatibility
  - See [docs/IDE_AGNOSTIC_MIGRATION.md](docs/IDE_AGNOSTIC_MIGRATION.md) for migration guide
- **Scripts Cleanup** – Removed all backward compatibility symlinks from scripts root directory:
  - Removed 12 symlinks that were pointing to subdirectory scripts
  - Updated Makefile to use subdirectory paths directly
  - Updated all documentation and workflow files with new paths
  - Result: Clean scripts directory with only essential subdirectories (gateway/, cursor/, virtual-servers/, utils/, lib/)
- **Scripts Reorganization** – Reorganized scripts directory by functional domain:
  - Created subdirectories: `gateway/`, `cursor/`, `virtual-servers/`, `utils/`
  - Moved scripts to appropriate domains (e.g., `register-gateways.sh` → `gateway/register.sh`)
  - Updated all script internals to calculate `SCRIPT_DIR` as parent directory
  - Created backward compatibility symlinks at old script locations
  - Updated `Makefile` shellcheck target to check subdirectories
  - Updated `start.sh` to reference new script paths
  - Updated `scripts/README.md` with new organization structure
- **Config Files Migration** – Completed migration of configuration files to `/config`:
  - Removed old config files from `scripts/` directory (`gateways.txt`, `virtual-servers.txt`, `prompts.txt`, `resources.txt`)
  - All scripts now use `CONFIG_DIR` variable pointing to `/config`
  - Updated `data/README.md` to reference new config locations
  - Backward compatibility maintained via fallback paths during transition
- **NPX Client Package** – Standard MCP server NPX wrapper for connecting to gateway:
  - Created `@mcp-gateway/client` NPM package with TypeScript source
  - Enables standard `npx` usage pattern like other MCP servers
  - Users can configure gateway in IDE's `mcp.json` using `npx -y @mcp-gateway/client`
  - **JWT authentication is optional** - not required for local development (`AUTH_REQUIRED=false`)
  - Supports both CLI arguments (`--url`, `--token`) and environment variables
  - Cross-platform Node.js client (no Docker/Bash dependencies)
  - Comprehensive documentation in `NPM_PACKAGE_README.md` and `PUBLISHING.md`
  - Added TypeScript build configuration (`tsconfig.json`, `package.json`)
  - Updated main README with NPX usage section showing local (no auth) and remote (with auth) examples
  - Updated `.env.example` and `.env` with comments explaining `AUTH_REQUIRED` setting

### Changed

- **uiforge Dynamic Configuration** – Converted uiforge to use translate pattern for per-user FIGMA_ACCESS_TOKEN configuration:
  - Modified `docker-compose.yml` to use translate pattern instead of standalone image
  - Removed hardcoded `FIGMA_ACCESS_TOKEN` from container environment
  - Users now configure `FIGMA_ACCESS_TOKEN` in IDE's `mcp.json` env object (per-user, not in .env)
  - Updated `.env.example` to document FIGMA_ACCESS_TOKEN as IDE-configured key
  - Added UI/Design Development configuration example in `docs/IDE_SETUP_GUIDE.md`
  - Enables multi-user setup without sharing Figma tokens in repository

- **CodeRabbit Configuration** – Comprehensive AI code review setup for IDE, GitHub, and CLI:
  - `.coderabbit.yaml` – Centralized configuration with assertive review profile, enabled linters (shellcheck, ruff, markdownlint, yamllint, hadolint, gitleaks, trufflehog, actionlint), path-based instructions for shell scripts, Python, Dockerfiles, YAML, and Markdown files
  - `docs/CODERABBIT_SETUP.md` – Complete setup guide covering GitHub integration, IDE extension installation, and CLI usage with authentication, review commands, and troubleshooting
- **Optimal MCP Stack Configurations** – 26 new stack profiles (13 stacks × 2 variants each) optimized for various tech stacks, all using tool-router for IDE compatibility:
  - **Node.js/TypeScript** (Full + Minimal) – JavaScript/TypeScript development with Node.js runtime
  - **React/Next.js** (Full + Minimal) – Modern web application development with React and Next.js
  - **Mobile Development** (Full + Minimal) – React Native and Flutter mobile application development
  - **Database Development** (Full + Minimal) – Database design, queries, and ORM management
  - **Java/Spring Boot** (Full + Minimal) – Enterprise Java development with Spring Boot framework
  - **Python Development** (Full + Minimal) – Python application development and data science
  - **AWS Cloud** (Full + Minimal) – AWS cloud infrastructure and serverless development
  - **Testing & QA** (Full + Minimal) – Comprehensive testing and quality assurance
  - **Code Quality & Security** (Full + Minimal) – Code analysis, security scanning, and quality enforcement
  - **Full-Stack Universal** (Full + Minimal) – Comprehensive full-stack development with all tools
  - **Monorepo Universal** (Full + Minimal) – Optimized for monorepo architectures (Nx, Turborepo, Lerna)
  - **DevOps & CI/CD** (Full + Minimal) – DevOps workflows, CI/CD pipelines, and infrastructure automation
- **Comprehensive Documentation** – 5 new documentation files with clear, step-by-step guides:
  - `docs/MCP_STACK_CONFIGURATIONS.md` – Complete guide to all stack profiles with use cases, required API keys, and configuration examples
  - `docs/IDE_SETUP_GUIDE.md` – IDE-specific configuration examples for Cursor, VSCode, Windsurf, and JetBrains with copy-paste ready configs
  - `docs/ENVIRONMENT_CONFIGURATION.md` – Minimal .env approach guide with migration instructions and security best practices
  - `docs/TOOL_ROUTER_GUIDE.md` – How tool-router works, architecture diagrams, and performance details
  - `docs/MONOREPO_VS_SINGLE_REPO.md` – Choosing the right profile based on project architecture
- **Minimal .env Configuration Philosophy** – Stack-specific API keys now configured in IDE's mcp.json instead of .env file for better security and portability
- **Environment Configuration** – Updated `.env.example` and `.env` with minimal configuration approach:
  - Added philosophy header explaining gateway infrastructure vs. stack-specific credentials separation
  - Moved stack-specific API keys (GitHub, Snyk, Tavily, database connections) to IDE configuration
  - Added clear documentation references and migration instructions
- **Virtual Server Definitions** – Updated `scripts/virtual-servers.txt` with 26 new stack profiles, all using tool-router for IDE compatibility
- **Gateway Registration** – Added notes to `scripts/gateways.txt` indicating GitHub gateway configuration requirements and IDE setup references

### Documentation

- **Documentation Principles** – All new documentation follows 6 core principles:
  1. **Clarity First** – Simple language, no jargon, explain technical terms
  2. **Step-by-Step** – Numbered steps with clear outcomes
  3. **Visual Aids** – Code examples, ASCII/mermaid diagrams, tables
  4. **Quick Start** – "5-minute setup" paths for common use cases
  5. **Troubleshooting** – Common errors and solutions included
  6. **Copy-Paste Ready** – All commands and configs ready to use

## [1.6.1] - 2026-02-14

### Fixed

- **Tool router HTTP error handling** – Added proper exception handling with retry logic for transient failures in `gateway_client.py`. Network errors (5xx, timeouts, connection failures) now retry up to 3 times with exponential backoff. Specific exceptions (HTTPError, URLError, TimeoutError, JSONDecodeError) are caught and handled appropriately instead of broad Exception catches.
- **JWT validation** – Enhanced `get_jwt()` in `scripts/lib/gateway.sh` to validate JWT format (three base64 segments separated by dots) and strip whitespace before validation. Prevents empty or malformed tokens from being used in API calls, which previously caused cryptic authentication failures.
- **Virtual server registration race condition** – Added retry logic with configurable attempts (`REGISTER_TOOLS_SYNC_RETRIES`, default 3) and delay (`REGISTER_TOOLS_SYNC_DELAY`, default 5s) in `register-gateways.sh` to ensure tools are fully synced before creating virtual servers. Counts expected gateways and waits for tool list to stabilize, preventing incomplete virtual servers.
- **Tool argument building** – Improved `build_arguments()` in `args.py` to handle multiple required parameters intelligently. Added support for common parameter names (prompt, question, input, text, message, command) and validates parameter types before assignment. Only fills string-type parameters to avoid type mismatches.
- **Tool scoring algorithm** – Enhanced scoring in `scoring.py` with synonym expansion (search/find/lookup, create/make/add, etc.), partial substring matching, and weighted scoring (name matches × 10, description × 3, gateway × 2). Improved tool selection accuracy for ambiguous queries.
- **Error handling in server.py** – Replaced broad `except Exception` with specific exception types (ValueError, ConnectionError) and added exception type names to error messages for better debugging. Programming errors now propagate instead of being silently caught.

### Changed

- **Tool router retry configuration** – Added constants `MAX_RETRIES=3` and `RETRY_DELAY=2` in `gateway_client.py` for configurable retry behavior.
- **Token extraction** – Modified `_tokens()` in `scoring.py` to include single-character tokens for better matching (previously filtered out tokens with length ≤ 1).

## [1.6.0] - 2026-02-14

### Added

- **Database MCP servers** – 3 new database servers for TypeScript/Node.js development:
  - **postgres** (port 8031) – Anthropic reference server (`@modelcontextprotocol/server-postgres`). Read-only PostgreSQL queries and schema inspection. Requires `POSTGRES_CONNECTION_STRING` in `.env`.
  - **mongodb** (port 8032) – Official MongoDB server (`mongodb-mcp-server`). Comprehensive database operations for collections, documents, and indexes. Requires `MONGODB_CONNECTION_STRING` in `.env`.
  - **prisma-remote** (remote) – Prisma ORM server (`https://mcp.prisma.io/mcp`). Type-safe database queries and migrations for PostgreSQL, MongoDB, MySQL, SQLite. Uncommented in `gateways.txt`.
- **Client-agnostic virtual servers** – Two new virtual servers that work with any MCP client (Cursor, Windsurf, VSCode, Antigravity, etc.):
  - **database** – PostgreSQL, MongoDB, Prisma ORM tools for database-focused workflows.
  - **fullstack** – Complete dev workflow with database tools + memory + git-mcp + fetch.
- **Connection string examples** – `.env` includes commented examples for `POSTGRES_CONNECTION_STRING` and `MONGODB_CONNECTION_STRING` with placeholder values.
- **Automated dependency updates** – Renovate integration for weekly automated dependency updates with breaking change detection. Auto-merges patch/minor updates after 3-day stabilization period when all CI checks pass. Major updates require manual review. Configuration in `.github/renovate.json` and workflow in `.github/workflows/renovate.yml`.
- **MCP Server Registry monitoring** – Weekly automated check for new MCP servers from the official registry. Creates/updates GitHub issues with new server discoveries and status of commented servers. Script: `scripts/utils/check-mcp-registry.py`, workflow: `.github/workflows/mcp-server-check.yml`.
- **Docker image update automation** – Weekly check for Context Forge updates from IBM/mcp-context-forge releases. Automatically creates PRs with version bumps across all relevant files (docker-compose.yml, scripts, CI, docs). Script: `scripts/utils/check-docker-updates.sh`, workflow: `.github/workflows/docker-updates.yml`.

### Changed

- **MCP server cleanup** – Removed problematic servers from `scripts/gateways.txt`: context-awesome (HTTP 406 upstream bug), apify-dribbble (niche use case). Updated comments to explain why servers are commented (auth required, timing issues, etc.).
- **Prisma remote server** – Uncommented `prisma-remote` in `gateways.txt` for TypeScript ORM support.

### Documentation

- **Multi-user database configuration guide** – New `docs/MULTI_USER_DATABASE_CONFIG.md` explaining deployment-level vs per-user configuration options for PostgreSQL and MongoDB. Covers per-deployment instances (recommended), Admin UI Passthrough Headers (advanced), and environment-based multi-tenancy patterns.
- **Database connection string documentation** – Enhanced `.env` comments to clarify that connection strings are deployment-level configuration shared across all users of a gateway instance. Added guidance for multi-user/multi-tenant scenarios.
- **README database entries** – Updated PostgreSQL and MongoDB table entries to link to multi-user configuration guide.
- **Automated Maintenance section** – Added comprehensive documentation for automation workflows in README.md, including setup instructions, schedule details, and how to configure secrets.
- **Development guide updates** – Updated docs/DEVELOPMENT.md with maintenance automation section covering Renovate configuration, MCP registry checks, and Docker update process.

## [1.4.3] - 2026-02-13

### Fixed

- **tool-router GATEWAY_JWT** – Updated `GATEWAY_JWT` in `.env` with fresh token (7-day expiry) so the tool-router container can authenticate with the gateway API. The tool-router now successfully fetches all 134 tools and routes tasks to the best matching upstream tool via `execute_task` and `search_tools`.
- **tool-router container restart** – Restarted tool-router container after JWT update to pick up the new environment variable.

### Changed

- **Virtual environment setup** – Created `.venv` with PyJWT and ruff for local development. Container fallback for JWT generation still works when venv is not activated.

### Verified

- **cursor-router virtual server** – Confirmed 2 tools (`execute_task`, `search_tools`) are registered and exposed through the gateway at `/servers/ec088b9ca9e04fd0bdf353e9d2df1501/mcp`.
- **Windsurf IDE configuration** – Verified `context-forge` entry in `~/.codeium/windsurf/mcp_config.json` points to `cursor-mcp-wrapper.sh` for auto-JWT connection.
- **Quality checks** – All 22 pytest tests pass, shellcheck clean, ruff clean.

## [1.4.2] - 2026-02-13

### Added

- **Cursor MCP timeout and cursor-pull** – `make use-cursor-wrapper` now sets `"timeout": 120000` (2 min) in `~/.cursor/mcp.json` for the context-forge entry to reduce MCP error -32001 (Request timed out). Optional `CURSOR_MCP_TIMEOUT_MS` in `.env` (e.g. 180000) overrides the value. New `make cursor-pull` pulls the Context Forge Docker image so the first Cursor start does not timeout while the image downloads.
- **verify-cursor-setup: image and Docker→gateway checks** – `make verify-cursor-setup` now checks that the Context Forge image is present and that the gateway is reachable from inside a container at `host.docker.internal:PORT`. Adds hint for -32001 (run `make cursor-pull`, re-run `make use-cursor-wrapper`, restart Cursor).

### Documentation

- **Cursor IDE + tool router** – [docs/AI_USAGE.md](docs/AI_USAGE.md) now has a step-by-step section "Using the MCP Gateway with the tool router in Cursor IDE" (prerequisites, start, register, GATEWAY_JWT, use-cursor-wrapper, cursor-pull, restart). New subsection "Context-forge logs Request timed out (MCP error -32001)" with fix steps. Fixed typo: "make###" → "###" in troubleshooting heading. README Connect Cursor and troubleshooting updated for timeout, cursor-pull, and verify checks.

## [1.4.1] - 2026-02-13

### Changed

- **.cursor/ ignored and removed from repo** – `.cursor/` is now in `.gitignore` and has been removed from the repository. Rules, skills, and hooks remain local-only; the remote no longer tracks `.cursor/`. Use your own `.cursor/` (or a shared config elsewhere) for Cursor IDE setup.

## [1.4.0] - 2026-02-13

### Added

- **Pre-commit lint and test** – Local hooks `make lint` and `make test` added to `.pre-commit-config.yaml` so CI-equivalent lint (shellcheck + ruff) and tests (pytest) run before commit when shellcheck and pytest are available (e.g. Dev Container or CI).

### Changed

- **CI lint** – Shellcheck now runs with `-S warning` so info-level (SC1091) does not fail the job. Fixed warnings: export `COMPOSE` where used by `get_jwt`, initialize `servers_code`/`servers_body` before `fetch_servers_list` in register-gateways.sh, replace `ids=($(...))` with `read -ra ids` in cleanup-duplicate-servers.sh, remove unused `id_to_sig` map; in gateway.sh use `_` for unused loop variable and SC2034 disable for caller-set `servers_body`; in log.sh use `var=''` for empty string assignments (SC1007).
- **CI secret scan** – Trufflehog base/head set by event: on push use `github.event.before` and `github.sha` so the scan has a diff; on pull_request keep default_branch and HEAD. Fixes "BASE and HEAD commits are the same" on push to main.
- **Gateway image** – Image `ghcr.io/ibm/mcp-context-forge:1.0.0-RC-1` not found; pin to `1.0.0-BETA-2` in docker-compose.yml, .github/workflows/ci.yml, scripts/cursor-mcp-wrapper.sh, README, and docs/DEVELOPMENT.md.
- **CI Trivy** – Tool-router scan now uses `ignore-unfixed: true` so unfixed base-image CVEs do not fail CI; re-check periodically for upstream fixes.
- **Ruff** – Removed unused `import pytest` from `tool_router/test_scoring.py` (ruff auto-fix).
- **Pre-commit** – Removed overlap between ruff hooks: local hook now runs only `make shellcheck` (ruff runs once via astral-sh/ruff-pre-commit). Added Makefile target `shellcheck`; `make lint` still runs shellcheck + ruff for CI.

### Documentation

- **Run CI-like checks locally** – docs/DEVELOPMENT.md now has a "Run CI-like checks locally" section with a table of CI job → local command (make lint, make test, Docker build/smoke, Trivy, pre-commit).

## [1.3.0] - 2026-02-13

### Added

- **Pre-commit hooks** – `.pre-commit-config.yaml` with gitleaks (secret detection), detect-private-key, check-yaml/check-json, trailing-whitespace, end-of-file-fixer, check-added-large-files (max 1MB), check-merge-conflict, and Ruff for `tool_router/`. `make pre-commit-install` installs the hook; see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#pre-commit). Pre-commit complements CI (Trufflehog secret scan, lint, test, Trivy).
- **.gitignore** – Python/coverage entries: `.pytest_cache/`, `__pycache__/`, `.ruff_cache/`, `.mypy_cache/`, `htmlcov/`, `.coverage`, `*.cover`, `bandit-report.json`.
- **Trivy gateway image scan** – CI Trivy job now also scans the gateway image `ghcr.io/ibm/mcp-context-forge:1.0.0-RC-1` (report only; exit-code 0 so upstream findings do not fail the build). Inline comment in workflow explains that the image is external/pre-built and fixes belong upstream (IBM/mcp-context-forge).

### Changed

- **Commit/PR rule** – `.cursor/rules/commit-pr-release.mdc`: explicit rule to never add Cursor co-authoring in commits.
- **.gitignore** – Replaced generic `test.js` with `test.local.js` and `*.temp.js` so only ad-hoc/local test artifacts are ignored and legitimate `test.js` files are not excluded.
- **CI** – Merged gateway health smoke into the build job so smoke runs on the same runner as the Docker build (avoids cross-job image reuse); removed standalone smoke job.
- **LICENSE** – Added copyright holder "MCP Gateway Contributors" to the MIT copyright line (standard format).

## [1.2.0] - 2026-02-13

### Added

- **Trivy image scan** – CI workflow now includes a Trivy job that builds the tool-router image and runs Trivy for vulnerability scanning (CRITICAL,HIGH; exit-code 1 so findings fail the build).

### Changed

- **Trufflehog pinned** – Secret scan uses `trufflesecurity/trufflehog@v3.93.3` instead of `@main` for reproducible CI.
- **Gateway image pinned** – `docker-compose.yml` and `scripts/cursor-mcp-wrapper.sh` use `ghcr.io/ibm/mcp-context-forge:1.0.0-RC-1` instead of `latest` for reproducible deploys.

### Documentation

- **Contributing / Forking** – README now has a short "Contributing / Forking" section: fork setup and how to contribute (lint, test, PR, CHANGELOG).
- **DEVELOPMENT.md Next steps** – Updated to reflect Trufflehog pin, Trivy in CI, and gateway image locations (`docker-compose.yml`, `scripts/cursor-mcp-wrapper.sh`).

## [1.1.0] - 2026-02-13

### Added

- **CI, lint, and tests** – GitHub Actions workflow (`.github/workflows/ci.yml`): shellcheck on `start.sh` and `scripts/**/*.sh`, ruff on `tool_router/`, pytest for tool_router (gateway_client, scoring, args), Docker build (sequential-thinking + tool-router), gateway health smoke, and optional Trufflehog secret scan. Makefile: `make lint` (shellcheck + ruff), `make test` (pytest). Root `pyproject.toml` and `requirements.txt` for Python deps; Dockerfile.tool-router uses them. `.cursor/`: COMMANDS.md documents `make lint`, `make test`, and CI; rule `mcp-gateway-ci.mdc` (Bash/Docker + Python); format-edited hook skips when no package.json or file under scripts/tool_router. See [.cursor/COMMANDS.md](.cursor/COMMANDS.md).

- **verify-cursor-setup and GATEWAY_JWT** – When the Cursor URL points to cursor-router and the server has 0 tools, `make verify-cursor-setup` now fails with a clear message to set `GATEWAY_JWT` (run `make jwt`, paste into `.env`, then `make start` and `make register`).

- **DevContainer** – `.devcontainer/` for one-click dev: Ubuntu base, repo mounted at `/workspace`, postCreate installs shellcheck and pip deps (requirements.txt, ruff, pytest). Use "Reopen in Container" in VS Code/Cursor. Documented in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#dev-container-optional) and README Prerequisites.

- **Next steps and docs** – [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) now has a "Dev Container" section and a "Next steps (after setup)" section (CI, local lint/test, gateway updates, Python deps, Cursor). CI secret scan uses `trufflesecurity/trufflehog@main` (no v4 tag).

- **How to add gateway to Cursor (mcp.json)** – [docs/AI_USAGE.md](docs/AI_USAGE.md) now has a "How to add the gateway to Cursor (~/.cursor/mcp.json)" section: Option A (wrapper via `make use-cursor-wrapper`) and Option B (manual streamableHttp URL + JWT), with link to README Connect Cursor.

- **Context-forge "Error" / "NO SERVER INFO FOUND"** – [docs/AI_USAGE.md](docs/AI_USAGE.md) troubleshooting: step-by-step fix (run `make verify-cursor-setup`, then `make start` + `make register`, set `GATEWAY_JWT` for cursor-router, full Cursor restart) when context-forge shows Error or logs "NO SERVER INFO FOUND" / "Server not yet created".

- **generate-secrets**

- **list-servers** – `make list-servers` and `scripts/list-servers.sh`: list virtual MCP servers (id, name, tool count) via the gateway API. Use when the Admin UI "Virtual MCP Servers" page shows "No tags found" or 0 items but servers were created via `make register` or the API; see [docs/ADMIN_UI_MANUAL_REGISTRATION.md](docs/ADMIN_UI_MANUAL_REGISTRATION.md).

### Changed

- **Scripts refactor** – Scripts now use shared `scripts/lib/bootstrap.sh` and `scripts/lib/gateway.sh`: single place for bootstrap (SCRIPT_DIR, REPO_ROOT, load_env), JWT generation, Docker Compose detection, gateway URL normalization, and HTTP response parsing. Reduced duplication across register-gateways, list-servers, list-prompts, verify-cursor-setup, refresh-cursor-jwt, use-cursor-wrapper, cursor-mcp-wrapper, and cleanup-duplicate-servers. `register-gateways.sh` virtual server create/update and 400 flat-body retry logic extracted into `create_or_update_virtual_server` and reused for both the virtual-servers.txt loop and the single default server branch. See scripts/README.md "Lib / shared behavior".

- **Default virtual server for context-forge wrapper** – When `REGISTER_CURSOR_MCP_SERVER_NAME` is unset, `make register` now writes `data/.cursor-mcp-url` for **cursor-router** (tool-router) instead of cursor-default. Users who want the full tool set must set `REGISTER_CURSOR_MCP_SERVER_NAME=cursor-default` and run `make register`. cursor-router requires `GATEWAY_JWT` in `.env`.

### Fixed

- **Virtual MCP Servers infinite loading** – When the Admin UI Virtual MCP Servers page stays on "Loading servers...", the usual cause is GET /servers returning 500 due to a **corrupted SQLite DB** (`database disk image is malformed`). [docs/ADMIN_UI_MANUAL_REGISTRATION.md](docs/ADMIN_UI_MANUAL_REGISTRATION.md) now has a dedicated "Virtual MCP Servers page stuck on Loading servers..." section: check gateway logs and run `make reset-db` then `make start` and `make register` to recover.

- **fetch_servers_list exit code** – `fetch_servers_list` now always returns 0 so the register script does not exit under `set -e` when GET /servers remains non-200 after retries; the caller decides behavior from `servers_code` and `servers_body`.

- **GET /servers HTTP 500 and virtual server create failures** – `list-servers.sh` retries `GET /servers` without query params when the gateway returns 500/502/503 (some Context Forge versions fail on `limit=0&include_pagination=false`). `register-gateways.sh` uses a shared `fetch_servers_list` helper: same initial retry, then for 5xx/408 up to 2 delayed retries (delay configurable via `REGISTER_GET_SERVERS_RETRY_DELAY`, default 5s; set to 0 to disable). Optional `REGISTER_VIRTUAL_SERVER_CREATE_WHEN_GET_FAILS=true` allows create-only (POST) when GET /servers still fails after retries (no update, possible duplicates if run again). See [docs/ADMIN_UI_MANUAL_REGISTRATION.md](docs/ADMIN_UI_MANUAL_REGISTRATION.md#troubleshooting-get-servers-returns-500-or-virtual-server-create-fails) and `.env.example`.

- **Virtual server create HTTP 400** – On 400, the script prints the gateway response (validation error) and retries with a flat request body and `associatedTools` (camelCase), for gateway versions that do not accept the nested `{"server": {"associated_tools": ...}}` shape. When the gateway returns "This transaction is inactive", the script skips the flat-body retry and prints a workaround (Admin UI or retry later). Docs now note that the same error can appear in the Admin UI when clicking Add Server, with workarounds (fewer servers/tools, restart gateway, report upstream). When GET /servers returns non-200 (and the opt-in create flag is not set), the script skips virtual server create/update and suggests Admin UI or retry.

- **context-forge "No server info found"** – When `REGISTER_CURSOR_MCP_SERVER_NAME` is unset, `make register` writes `data/.cursor-mcp-url` for the default virtual server (cursor-router). Avoids stale or wrong server UUID after DB reset or first run. Wrapper validates URL format and suggests `make start && make register` when the file is missing; README and verify-cursor-setup troubleshooting updated.

- **verify-cursor-setup and context-forge troubleshooting** – `make verify-cursor-setup` now fetches the server by ID and shows which server the URL points to (name and tool count). If the server has 0 tools, it warns to set GATEWAY_JWT and run make register (for cursor-router). If the URL points to cursor-default, it suggests removing REGISTER_CURSOR_MCP_SERVER_NAME from .env to use default cursor-router. README troubleshooting updated: clear steps to use cursor-router (remove REGISTER_CURSOR_MCP_SERVER_NAME, make register, full Cursor restart) and to fix "No server info found" (gateway reachable from Docker, make register, GATEWAY_JWT for cursor-router).

### Added

- **generate-secrets** – `make generate-secrets` prints `JWT_SECRET_KEY` and `AUTH_ENCRYPTION_SECRET` (32-byte base64) for pasting into `.env`. Weak or short secrets cause gateway warnings and context-forge "Server disconnected" / "Needs authentication". See README troubleshooting and `.env.example`.

- **REGISTER_CURSOR_MCP_SERVER_NAME** – When set, `make register` writes `data/.cursor-mcp-url` only for that virtual server (e.g. `cursor-default`). If unset, the last server in `virtual-servers.txt` wins. After register, script prints which server URL was written. See `.env.example` and scripts/README.md.

- **Full Cursor restart and "No server info found"** – `make verify-cursor-setup` and `make use-cursor-wrapper` now tell users to fully quit Cursor (Cmd+Q / Alt+F4) and reopen; Reload Window is not enough. README troubleshooting: if logs show "No server info found" or "Server not yet created" after a full restart, try `REGISTER_CURSOR_MCP_SERVER_NAME=cursor-default`, run `make register`, then quit and reopen Cursor again.

- **Cleanup duplicate virtual servers** – `scripts/cleanup-duplicate-servers.sh` and `make cleanup-duplicates`: remove virtual servers that have the same set of associated tools, keeping one per unique tool set (prefers server names listed in `virtual-servers.txt`). Use `CLEANUP_DRY_RUN=1 make cleanup-duplicates` to report only. Requires jq and gateway running. See [scripts/README.md](scripts/README.md).

- **Tool router (single entry point)** – New **tool-router** MCP server (Python) that exposes 1–2 tools (`execute_task`, optional `search_tools`). Registered as a gateway and exposed via the **cursor-router** virtual server. When Cursor connects to cursor-router, it sees only the router’s tools; `execute_task(task, context)` fetches all tools from the gateway (GET /tools with JWT), selects the best match by keyword scoring, and invokes it via POST /rpc. Requires `GATEWAY_JWT` in `.env` (run `make jwt`, paste, refresh periodically). `scripts/gateways.txt`: tool-router entry; `scripts/virtual-servers.txt`: cursor-router|tool-router. Docker service `tool-router` (Dockerfile.tool-router, port 8030). Docs: README “Single entry point (router)”, [docs/AI_USAGE.md](docs/AI_USAGE.md#single-entry-point-router), .env.example and scripts/README.md.

- **Automatic JWT for Cursor (context-forge)** – `scripts/cursor-mcp-wrapper.sh`: run as the Cursor MCP command for context-forge; generates a fresh JWT on each connection and execs the gateway Docker image so no token is stored in mcp.json and no weekly refresh is needed. `make register` writes the container MCP URL to `data/.cursor-mcp-url` (gitignored) for the wrapper; optional `CURSOR_MCP_SERVER_URL` in `.env` overrides. README "Connect Cursor": new "Automatic JWT (recommended)" subsection; .env.example and scripts/README.md document the wrapper and `data/.cursor-mcp-url`. On Linux the wrapper adds `--add-host=host.docker.internal:host-gateway` automatically.
- **Verify Cursor (wrapper) setup** – `scripts/verify-cursor-setup.sh` and `make verify-cursor-setup`: check gateway health, presence and content of `data/.cursor-mcp-url`, and that the server UUID in that URL exists on the gateway. Use when context-forge shows Error in Cursor to see which check fails; then run `make start`, `make register`, and restart Cursor as needed. README troubleshooting updated for wrapper vs manual JWT.

- **Switch to Cursor wrapper** – `scripts/use-cursor-wrapper.sh` and `make use-cursor-wrapper`: set the context-forge (or user-context-forge) entry in `~/.cursor/mcp.json` to the automatic JWT wrapper command, replacing any URL/headers or docker-args config. Requires jq and `make register` (or `CURSOR_MCP_SERVER_URL`). README Connect Cursor section updated to recommend this one-step switch.

- **Refresh Cursor JWT in mcp.json** – `scripts/refresh-cursor-jwt.sh` and `make refresh-cursor-jwt`: update the Bearer token for the context-forge entry in `~/.cursor/mcp.json` in place (docker args or streamableHttp/SSE headers). Uses `CURSOR_MCP_JSON` for path (default `~/.cursor/mcp.json`). Requires jq. Creates a backup (`mcp.json.bak`) before overwriting. README documents running it weekly (e.g. cron `0 9 * * 0`) for manual JWT configs.

### Changed

- **Weak secrets and context-forge** – `.env.example` and README now require `JWT_SECRET_KEY` and `AUTH_ENCRYPTION_SECRET` of at least 32 characters; document that weak values cause "Server disconnected" / "Needs authentication". `start.sh` error message and README quick start mention `make generate-secrets`. Troubleshooting bullet for context-forge errors updated with weak-secrets fix (generate-secrets → update .env → make stop/start/register → restart Cursor). scripts/README.md documents `make generate-secrets`.

- **refresh-cursor-jwt** – Script now tries MCP keys `context-forge` and `user-context-forge` (Cursor may show the server as "user-context-forge"); set `CONTEXT_FORGE_MCP_KEY` if your key differs. For URL/streamableHttp configs, the script now sets `headers.Authorization` even when `headers` was missing. README troubleshooting updated with a quick-fix sequence (make start → make refresh-cursor-jwt → restart Cursor) and URL/host.docker.internal notes.

- **Virtual server registration: no duplicate tool sets** – When `virtual-servers.txt` is used, `scripts/register-gateways.sh` now filters tools by gateway using `.gatewaySlug`, `.gateway_slug`, `.gateway.slug`, or `.gateway.name` (Context Forge API). If two virtual server lines would attach the same set of tool IDs, only the first is created/updated; the second is skipped with a warning to avoid duplicate servers with identical tools. See [scripts/virtual-servers.txt](scripts/virtual-servers.txt).

- **make jwt: standalone generator** – `make jwt` now prefers a local script (`scripts/create_jwt_token_standalone.py`) that builds the same JWT as Context Forge without loading gateway config, so no SQLite/BASIC_AUTH/admin password logs appear. Requires PyJWT (`pip install pyjwt`) when using the standalone path. If the script is unavailable or PyJWT is missing, the target falls back to `docker exec … create_jwt_token` with stderr suppressed. Uses `PLATFORM_ADMIN_EMAIL`, `JWT_SECRET_KEY`; optional `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_EXP_MINUTES`.

### Security

- **.env.example placeholders** – Replaced weak example values (`my-test-key`, `changeme`, `my-test-salt`) with `REPLACE_WITH_STRONG_SECRET` / `REPLACE_ME` so they are not used in production; added a note that placeholder values must not be used in production.

### Added

- **Virtual servers for Cursor 60-tool limit** – `scripts/virtual-servers.txt`: define multiple virtual servers (format `ServerName|gateway1,gateway2,...`). When present, `make register` creates or updates each server with up to 60 tools from the listed gateways and prints one Cursor URL per server. Use one URL in Cursor (e.g. `cursor-default`) to stay under the ~60-tool limit. Docs: README (virtual server behaviour and 60-tool note), [scripts/README.md](scripts/README.md) (virtual-servers.txt), [docs/AI_USAGE.md](docs/AI_USAGE.md#tool-limit-and-virtual-servers) (tool limit and virtual servers), [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) (when to use virtual-servers.txt).

- **Registration reliability** – `.env.example` now sets `REGISTER_WAIT_SECONDS=30` by default so translate containers (e.g. sqlite) are ready before gateways are registered, reducing "Unable to connect to gateway" on first run. `make register-wait` runs register with a 30s wait. `scripts/gateways.txt`: context-awesome and prisma-remote commented out (often unreachable or 406); sqlite, github, and Context7 commented out so `make register` / `make register-wait` succeed by default (uncomment or add via Admin UI after checking logs or setting API keys). README and scripts/README.md updated. **register-gateways.sh**: on "Unable to connect" or "Unexpected error" for local SSE gateways (ports 8013–8029), script retries once after 15s; local-fail hint and HAS_LOCAL_FAIL now include sqlite/github (8022–8029).

- **README context-forge Cursor failure** – Troubleshooting: if context-forge shows Error in Cursor or logs "No stored tokens found" / "Client error for command fetch failed", add JWT to MCP config (`headers.Authorization = Bearer <token>`), run `make jwt`, restart Cursor. Connect Cursor section now states that the gateway requires a Bearer JWT on every request.

- **README "Missing servers and authentication"** – New Troubleshooting subsection: how to uncomment local gateways (sqlite, github) and remote gateways (Context7, context-awesome, prisma-remote, cloudflare-\*, v0, apify-dribbble); short authentication checklist (local .env keys vs Admin UI Passthrough Headers/OAuth for remote). Links to docs/ADMIN_UI_MANUAL_REGISTRATION.md.

- **register-gateways.sh Cursor URLs** – After creating/updating the virtual server, the script now prints both `Cursor (mcp):` and `Cursor (sse):` URLs on separate lines for easier copy-paste and to match README (mcp vs sse transport).

- **make reset-db** – Stops the stack and removes `./data/mcp.db`, `mcp.db-shm`, and `mcp.db-wal` for recovery from SQLite corruption ("database disk image is malformed"). After running it, use `make start` then `make register`. README troubleshooting: new bullet linking admin 500s (gateways/partial, prompts/partial, "Loading gateways...") to corrupted DB and `make reset-db`; existing "database disk image is malformed" bullet updated to mention `make reset-db`. scripts/README.md documents the new target.

- **.env.example and Make-first** – .env.example: grouped sections (Required, Register script, Optional translate services, Optional debug), Make-first header, REGISTER_VERBOSE and MCPGATEWAY_CONTAINER. Makefile: `gateway-only` target. README, .cursor/COMMANDS.md, docs/DEVELOPMENT.md, scripts/README.md: prefer `make start`, `make register`, `make jwt`, `make list-prompts`, `make gateway-only`; script invocations as alternatives. Troubleshooting and prompts workaround use make where applicable.

- **Project structure and productivity** – [scripts/README.md](scripts/README.md): index of scripts and commands (start, register, list-prompts, JWT, gateways/prompts/resources format). [.cursor/COMMANDS.md](.cursor/COMMANDS.md): replaced with mcp-gateway-specific workflows (no npm; use Docker and scripts). [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): local dev loop, adding gateways/prompts/resources, troubleshooting links. [docs/AI_USAGE.md](docs/AI_USAGE.md): which tools for planning, docs, search, browser, DB. [scripts/prompts.txt](scripts/prompts.txt): task-breakdown prompt and format comment. [scripts/resources.txt](scripts/resources.txt): format comment and example resource. [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md): current setup (virtual server name, gateways/prompts location). [Makefile](Makefile): targets `start`, `stop`, `register`, `jwt`, `list-prompts`. README: Development subsection (links to DEVELOPMENT.md, scripts/README.md), Using the gateway with AI (link to AI_USAGE.md), make shortcuts.

- **Gateways and register script (stack-focused)** – `scripts/gateways.txt`: header naming stack (React, Node, TypeScript, Java, Spring, Tailwind, Next.js, Jest, Prisma), optional third column Transport (SSE / STREAMABLEHTTP), remote section with Context7, context-awesome, prisma-remote uncommented; cloudflare-\*, v0, apify-dribbble remain commented (auth in Admin UI). `scripts/register-gateways.sh`: transport in POST /gateways (from column or inferred from URL); after gateways, optional virtual server create/update (REGISTER_VIRTUAL_SERVER=true, default) using jq, sync delay 3s, GET /tools then PUT or POST /servers with all tool IDs, prints server UUID and Cursor URL; optional REGISTER_PROMPTS from scripts/prompts.txt (name|description|template, {{arg}} and \\n); optional REGISTER_RESOURCES from scripts/resources.txt (name|uri|description|mime_type). `.env.example`: EXTRA_GATEWAYS with Transport, REGISTER_VIRTUAL_SERVER, REGISTER_VIRTUAL_SERVER_NAME, REGISTER_PROMPTS, REGISTER_RESOURCES; note Context7/Prisma auth in Admin UI. README: gateways.txt format, virtual server output, subsection "Stack-focused gateways" (Next.js project-local, Spring on host). Optional `scripts/prompts.txt` with one code-review prompt (format documented in file).

- **docs/ADMIN_UI_MANUAL_REGISTRATION.md** – Documentation for registrations that must be done manually in the Context Forge Admin UI: exact API/UI structure for gateways (name, url, transport, auth), virtual servers (associated_tools), prompts, and resources; which gateways require Passthrough Headers or OAuth (Context7, v0, apify-dribbble, etc.); quick-reference table for remote gateways. README links to this doc for auth and manual setup.

- **Local translate services: reactbits, snyk, sqlite, github** – Four new stdio→SSE translate services (ports 8022–8025). reactbits runs `reactbits-dev-mcp-server`; snyk runs `snyk mcp -t stdio --experimental` (set `SNYK_TOKEN` in .env); sqlite runs `mcp-sqlite` (npm) with configurable `SQLITE_DB_PATH` and `SQLITE_VOLUME`; github runs `@modelcontextprotocol/server-github` (set `GITHUB_PERSONAL_ACCESS_TOKEN` in .env). `scripts/gateways.txt`, `.env.example`, and README table updated.

- **Logging and UX in bash scripts** – Added `scripts/lib/log.sh` with TTY-aware colors and helpers: `log_step`, `log_info`, `log_ok`, `log_warn`, `log_fail`, `log_err`. `start.sh`, `scripts/register-gateways.sh`, and `scripts/list-prompts.sh` now use them for consistent section headers (==>), success (✓), warnings (⚠), and errors (✗). Colors disabled when stdout is not a TTY (pipes/CI stay plain).

- **scripts/list-prompts.sh** – Script to list prompts via GET /prompts (JWT from gateway, .env). Works in any shell (e.g. fish); README and docs/ADMIN_UI_MANUAL_REGISTRATION.md now point to it instead of inline curl/JWT commands.

- **Admin Prompts page infinite loading** – README and docs/ADMIN_UI_MANUAL_REGISTRATION.md now document the issue and workarounds: use GET/POST /prompts with JWT, register via REGISTER_PROMPTS and scripts/prompts.txt, or inspect Network tab and report upstream to IBM/mcp-context-forge.

- **register-gateways.sh auth reminder** – After "Done.", the script now prints a single line pointing to docs/ADMIN_UI_MANUAL_REGISTRATION.md for gateways that need API keys or OAuth (Context7, v0, apify-dribbble, etc.), so users know to configure them in Admin UI.

- **register-gateways.sh curl timeouts** – POST to /gateways now uses --connect-timeout 10 and --max-time 45 so the script does not hang when the gateway is slow to validate URLs.
- **register-gateways.sh idempotent for "already exists"** – When the API returns "Gateway name already exists" (e.g. after restart with same DB), the script now reports "OK name (already registered)" instead of FAIL, so re-running after start is safe.
- **Translate services bind to 0.0.0.0** – All translate commands in docker-compose now pass `--host 0.0.0.0` so the SSE server accepts connections from the gateway container (default was 127.0.0.1, causing "Unable to connect to gateway" when registering local gateways). README Troubleshooting updated.
- **SQLite corruption recovery** – README Troubleshooting and data/README.md now document how to fix "database disk image is malformed" / "FileLock health check failed": stop stack, remove `./data/mcp.db` (and `-shm`/`-wal` if present), restart; re-register gateways after.

- **README: URL-based Cursor connection** – Documented correct virtual server paths (`/sse` and `/mcp`) and that auth (Bearer JWT) is required; added troubleshooting for "Method Not Allowed" and "Invalid OAuth error response" when the path or auth is missing.

- **data/README.md** – Documents the data directory (SQLite persistence) and lists the nine local Docker translate services (name, port, internal URL) for reference.
- **Local translate services for all stdio MCP servers** – `./start.sh` now starts gateway plus nine translate services (sequential-thinking, chrome-devtools, playwright, magicuidesign-mcp, desktop-commander, puppeteer, browser-tools, tavily, filesystem). Each runs stdio→SSE via `mcpgateway.translate`; `scripts/gateways.txt` and `./scripts/register-gateways.sh` register them. Optional env: `TAVILY_API_KEY`, `FILESYSTEM_PATH`, `FILESYSTEM_VOLUME`. README table and "Servers that stay in Cursor or as remote gateways" note; `.env.example` documents optional ports and filesystem/tavily vars.

### Fixed

- **Translate image build race** – All translate services shared the same image and `build` block, so Compose built in parallel and multiple services tried to export the same tag, causing "already exists" and CANCELED. The build is now defined only on `sequential-thinking`; other services use the same image and no longer trigger a build, so the image is built once and reused.
- **Translate containers crash (FileNotFoundError: npx)** – Dockerfile.translate now installs `npm` so `npx` is available in the image; translate services no longer restart loop. Register script shows API error message on FAIL and suggests checking `docker compose logs <service>` on 503.

- **register-gateways.sh** – Script retries gateway `/health` every 3s for up to 90s (`REGISTER_GATEWAY_MAX_WAIT`) instead of failing immediately on "health got 000". If health fails with the current host, it retries with the other (localhost ↔ 127.0.0.1) for another 90s to handle Docker Desktop and similar environments. Final error suggests `docker compose ps gateway` and `docker compose logs gateway`. Optional `REGISTER_WAIT_SECONDS` for translate containers. FAIL suggests `REGISTER_VERBOSE=1`. README and `.env.example` updated.
- **register-gateways.sh health check** – Health-check loop now prints progress to stderr every 3s (elapsed time and "OK after Ns" on success) so the script does not appear stuck. When `GATEWAY_URL` uses 127.0.0.1, the script tries localhost first, then 127.0.0.1 as fallback, so Docker Desktop for Mac usually succeeds without a long wait. `.env.example` and README Troubleshooting updated (localhost vs 127.0.0.1 on Mac).
- **register-gateways.sh FAIL output** – On registration failure, script now shows API `detail` when present (in addition to `message`). Shorter per-FAIL hint (docker compose logs). Single end-of-run hint when any local translate gateway failed: REGISTER_VERBOSE=1, REGISTER_WAIT_SECONDS=30, docker compose ps.

- **Dockerfile.translate build** – Context Forge image has no package manager; base switched to `python:3.12-slim`, install Node via apt-get and `mcp-contextforge-gateway` via pip so the translate service (e.g. sequential-thinking) builds and runs.

### Changed

- **register-gateways.sh feedback** – Script now prints progress: "Register gateways – checking environment...", "Waiting for gateway at URL (up to Ns)...", "Gateway ready at URL", "Generating JWT...", "JWT generated.", "Registering gateways from EXTRA_GATEWAYS/scripts/gateways.txt...", and "Done." so the user sees each phase.
- **start.sh feedback** – Script now prints progress: "MCP Gateway – checking environment...", "Using: docker compose", and a clear message before each action (e.g. "Building and starting gateway + translate services (first run may take 1–2 min)..."). Success output shows Admin UI URL using PORT from .env and next steps (register, stop).
- **README Troubleshooting** – Added "Failed to initialize gateway" (e.g. Context Awesome 406 / Accept header) and MCP Registry "Failed" (retry or add manually, OAuth pointer).
- **Default start includes all local servers** – `./start.sh` now starts the gateway and sequential-thinking (and any future local translate services); removed profile so they always run. Use `./start.sh gateway-only` for gateway alone. README and register script updated.
- **Register gateways script and URL-based docs** – `scripts/register-gateways.sh` registers gateways from `scripts/gateways.txt` (Name|URL|Transport per line) or `EXTRA_GATEWAYS` in .env. JWT from gateway container. README: "Registering URL-based MCP servers" with table, auth note (v0/apify in Admin UI), and sequential-thinking "Failed to initialize" troubleshooting.
- **Optional sequential-thinking service** – `./start.sh sequential-thinking` starts the gateway plus a translate container that runs the [sequential-thinking](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) MCP server (stdio→SSE). Add gateway in Admin UI with URL `http://sequential-thinking:8013/sse`, Transport SSE. `Dockerfile.translate` (Node on top of Context Forge image) and compose profile `sequential-thinking` added; README and .env.example updated.
- **Single start script, gateway-only Docker** – One script: `./start.sh` (start) and `./start.sh stop` (stop). Removed `scripts/` (down.sh, full-setup.sh, up.sh, setup-context-forge-cursor.sh), `Dockerfile.translate`, and `docs/TROUBLESHOOTING.md`. Docker Compose now has only the gateway service; data in `./data`. README and `.env.example` reduced to gateway-only. Pipeline rule updated to reference `start.sh` and README.
- **Removed gateway registration automation** – Deleted scripts that automated adding MCP servers: `register-gateways.sh`, `register-gateways-admin-ui.py`, `configure-gateways-via-admin-ui.py`, `run-configure-admin-ui.sh`, and shared modules `gateways_config.py`, `mcpgateway_admin.py`. Gateways are added manually via Admin UI (Gateways). Removed `requirements.txt` and `requirements-playwright.txt`. Updated README (setup step 3 = add gateways in Admin UI), full-setup.sh (no register step), TROUBLESHOOTING.md, and .env.example (dropped GATEWAY_WAIT, REGISTER_DELAY, REGISTER_TIMEOUT, ADMIN_UI_TIMEOUT, REGISTER_PROFILES).
- **Docs cleanup** – Removed redundant docs (A2A_AGENTS_AND_RESOURCES, MCP_REGISTRY_AND_GROUPS, MCP_SERVERS_RECOMMENDED, MCPMARKET_SKILLS, PIPELINE). Setup pipeline and references consolidated into README. TROUBLESHOOTING.md trimmed to essential issues (gateway not ready, 503, network, port, venv). Single source of truth: README + TROUBLESHOOTING.

### Added

- **run-configure-admin-ui.sh starts gateway if unreachable** – The runner sources `.env`, defaults `GATEWAY_URL` from `PORT` when unset, and if the gateway is not reachable it runs `docker compose up -d` (or `docker-compose up -d`), waits for `/health` (honors `UP_WAIT_GATEWAY`), then runs the Playwright configure script. So `./scripts/run-configure-admin-ui.sh` can be run without starting the stack first.
- **Configure all MCP gateways via web admin panel** – Playwright script `scripts/configure-gateways-via-admin-ui.py` logs in to the admin UI, adds gateways from the canonical list (and `EXTRA_GATEWAYS`), then creates/updates the virtual server via the admin API (JWT). Credentials from `.env`. Optional: `pip install -r requirements-playwright.txt` and `playwright install chromium`. Shared gateways list in `scripts/gateways_config.py`; admin API helpers in `scripts/mcpgateway_admin.py`. README "Configure via Admin UI (automated)" and [docs/PIPELINE.md](docs/PIPELINE.md), [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) updated.
- **Python script to register gateways (Option B)** – When `./scripts/register-gateways.sh` times out (HTTP 000) or you prefer not to use the shell script, use `python scripts/register-gateways-admin-ui.py`. The script builds a JWT from `.env` and registers gateways and creates/updates the `mcpmarket` virtual server via the admin API. API responses are normalized for array or wrapped shapes. Requires Python 3.10+ and `pip install -r requirements.txt`. See README (Option B) and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
- **Tools separated and tagged by technology** – Docker Compose profiles for toggling: `full` (all 5 mcpmarket-style), `node` (task-master, superpowers, chrome-browser), `python` (beads, gpt-researcher), `reference` (time, fetch, memory, sequential-thinking, filesystem, git). Existing 5 services have multiple profiles; 6 reference translate services under profile `reference`. `scripts/register-gateways.sh` includes reference gateways; failed gateways (e.g. profile not up) are skipped.
- **MCP registry and groups** – [docs/MCP_REGISTRY_AND_GROUPS.md](docs/MCP_REGISTRY_AND_GROUPS.md): how to use the admin MCP registry at http://localhost:4444/admin/#mcp-registry, link to [official MCP Registry](https://registry.modelcontextprotocol.io), and server groups (reference, node, python) for adding servers and organizing tools. README points to the registry doc.
- **Reference profile: filesystem and git** – `translate-filesystem` (path `/workspace`, volume `FILESYSTEM_WORKSPACE`) and `translate-git` (working dir `/repo`, volume `GIT_REPO_PATH`) under profile `reference`; ports 8014, 8015. `.env.example` and register-gateways.sh updated.
- **register-gateways.sh JWT** – Script now generates the Bearer token from the gateway container (`sh -c '...'` using container env) so the JWT secret always matches the gateway. Prefer container token when the gateway container is running; fall back to `MCPGATEWAY_BEARER_TOKEN` from `.env` only when the container is not running.
- **Java & Spring AI MCP** – [docs/MCP_SERVERS_RECOMMENDED.md](docs/MCP_SERVERS_RECOMMENDED.md) "Java & Spring AI MCP" section: links to [modelcontextprotocol/java-sdk](https://github.com/modelcontextprotocol/java-sdk) and [Spring AI MCP](https://docs.spring.io/spring-ai-mcp/reference/overview.html); run Java servers on host and add via `EXTRA_GATEWAYS`.
- **A2A recommendation** – [docs/A2A_AGENTS_AND_RESOURCES.md](docs/A2A_AGENTS_AND_RESOURCES.md) "Recommended for this gateway" subsection: when to enable A2A and register agents.
- **.env.example** – Optional reference profile ports (`TIME_PORT`, `FETCH_PORT`, `MEMORY_PORT`, `SEQUENTIAL_THINKING_PORT`) and stdio commands; comment listing profiles (full, node, python, reference).
- **scripts/up.sh** – Start stack with profiles without caring about `docker compose` vs `docker-compose`: `./scripts/up.sh full reference`; no args = gateway only. Picks compose command automatically.
- **scripts/down.sh** – Tear down stack with same profile args as `up.sh` (e.g. `./scripts/down.sh full reference`) so all containers and the network are removed. Avoids "Network mcp-gateway-net Resource is still in use" when you previously started with profiles. See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
- **Host all planned MCP servers** – `Dockerfile.translate` extends Context Forge with Node.js so all translate services (Python and Node-based) run in Docker. All translate services use image `mcp-gateway-translate:latest`; `./scripts/up.sh full reference` builds it if missing, then starts the stack. `.dockerignore` added for faster builds. README and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) updated for hosting all servers.

### Changed

- **Gateway URL resolution** – `get_base_url()` in `mcpgateway_admin.py` uses `PORT` from `.env` when `GATEWAY_URL` is unset (default `http://127.0.0.1:4444`), so scripts stay in sync with `docker-compose` port mapping.
- **Option B Python script (register-gateways-admin-ui.py)** – Uses JWT (from `PLATFORM_ADMIN_EMAIL` and `JWT_SECRET_KEY` in `.env`) for admin API auth instead of Selenium/session cookies. Removes dependency on Chrome and Selenium; requires only `python-dotenv`, `requests`, and `PyJWT`. Fixes 401 "Authorization token required" and connection-aborted errors. Honors `REGISTER_DELAY` (default 25s after gateway health) and `GATEWAY_WAIT` (default 90s for gateway health poll) from `.env` so users can wait longer for a slow-starting gateway. Reduces 503 "Unable to connect to gateway" when run right after `./scripts/up.sh`. See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for "Gateway not reachable". See README (Option B) and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
- **.cursor as global config** – Removed LukBot-specific content so this repo works as a global Cursor config for any project. Session context, COMMANDS.md, and skills (backend-express, frontend-react-vite, e2e-playwright, mcp-docs-search) are now generic; LukBot-only skills (discord-commands, music-queue-player, lukbot-docker-dev, prisma-redis-lukbot) removed. README Cursor connection step no longer links to LukBot; template is inline.
- **README** – "Profiles (toggle by technology)" recommends `./scripts/up.sh [profiles]` so profile start works on systems where `docker compose` does not support `--profile`; direct `docker-compose` examples for copy-paste. "Full stack: registering gateways" notes that script registers all gateways and skips unreachable ones; pointer to Java & Spring AI MCP in MCP_SERVERS_RECOMMENDED.md.
- **docs/PIPELINE.md** – Step 2 mentions profiles (node, python, reference). [docs/MCP_SERVERS_RECOMMENDED.md](docs/MCP_SERVERS_RECOMMENDED.md) "Adding to Context Forge" includes profiles and register-gateways behavior.

## [1.0.0] - 2026-02-04

### Changed

- **scripts/ and docs/ cleanup** – Removed `docs/PROJECT_STATE.md` (content duplicated in README and .env). Slimmed `scripts/README.md` to a compact command/file index and file-format summary. Tightened `docs/DEVELOPMENT.md` (shorter sections, same content). Kept `docs/DEVELOPMENT.md`, `docs/AI_USAGE.md`, `docs/ADMIN_UI_MANUAL_REGISTRATION.md` as the only docs; all scripts and data files retained as essential.

- **Script output (color and structure)** – All scripts now use `scripts/lib/log.sh`: `log_section` (bold section titles), `log_line` (separator), `log_step`, `log_ok`, `log_info`, `log_warn`, `log_fail`, `log_err`. Colors only when stdout is a TTY; pipes/CI stay plain. Applied to start.sh, register-gateways.sh, verify-cursor-setup.sh, use-cursor-wrapper.sh, refresh-cursor-jwt.sh, cursor-mcp-wrapper.sh, list-prompts.sh, cleanup-duplicate-servers.sh.

## [0.1.0]

### Added

- **Git repository** – Initialized git repo with `.gitignore` for env/secrets (`.env`, `.cursor/.env.mcp`), SQLite data files (`data/*.db*`), OS/IDE artifacts, logs, and build output.
- **Docker Compose** – `docker-compose.yml` with gateway service and optional translate sidecars (profile `full`) for stdio-to-SSE: beads, gpt-researcher, task-master, superpowers, chrome-browser. Gateway-only: `docker compose up -d`; full stack: `docker compose --profile full up -d`.
- **Gateway registration** – `scripts/register-gateways.sh` for idempotent registration of translate endpoints with the gateway (internal Docker URLs). Documented manual `POST /gateways` and virtual server creation in README.
- **Documentation** – README updated with run modes (gateway only vs full stack), registration steps, Cursor connection (Docker wrapper), and env vars. `.env.example` extended with optional Compose ports, stdio commands, and API keys for upstream MCP servers.
- **mcpmarket skills** – README documents adding [mcpmarket.com/tools/skills](https://mcpmarket.com/tools/skills) as global Cursor rules at `~/.cursor/rules/` or `~/.cursor/skills-cursor/` (no rule files in this repo). [docs/MCPMARKET_SKILLS.md](docs/MCPMARKET_SKILLS.md) lists all skills and mcpmarket server URLs.
- **Virtual server API** – `POST /servers` body uses `{"server":{...}}`. Scripts and README updated. `register-gateways.sh`: portable `sed '$d'` instead of `head -n -1`.
- **Virtual server "mcpmarket"** – Created via API (id `d80befa083604f8393729069e399d21e`) when gateways are unavailable (gateway-only mode); add tools after running full stack and `./scripts/register-gateways.sh`.
- **MCP servers from mcpservers.org, mcp.so & reference** – [docs/MCP_SERVERS_RECOMMENDED.md](docs/MCP_SERVERS_RECOMMENDED.md) extended with a section of free, good servers from [mcpservers.org](https://mcpservers.org/), [mcp.so](https://mcp.so/), and [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) (Time, Fetch, Memory, Sequential Thinking, Filesystem, Git, Playwright, Puppeteer, Firecrawl, Brave Search) plus links to those indexes in Curated lists.
- **A2A agents, tools, prompts, resources** – [docs/A2A_AGENTS_AND_RESOURCES.md](docs/A2A_AGENTS_AND_RESOURCES.md) added: A2A (Agent-to-Agent) in Context Forge (enable, register, associate with virtual server), free A2A resources ([a2aprotocol.org](https://www.a2aprotocol.org/en), [A2A GitHub](https://github.com/a2aproject/A2A)), and pointers for MCP tools, prompts, and resources. Optional `.env` vars for A2A documented in `.env.example`.
- **Middleware & plugins** – README section added: no custom middleware/plugins in this repo; Context Forge’s built-in plugin system and observability (OpenTelemetry, Prometheus) documented; reverse proxy (nginx/Caddy) only when needed (TLS, rate limiting, logging).
- **Implement docs to Context Forge** – `scripts/register-gateways.sh` now creates or updates the virtual server `mcpmarket` and associates all tools from `GET /tools` with it (requires `jq`). Optional `EXTRA_GATEWAYS` in `.env` (format: `name|url,name|url`) registers additional gateways (e.g. reference servers run on the host). README and [docs/MCP_SERVERS_RECOMMENDED.md](docs/MCP_SERVERS_RECOMMENDED.md) updated.
- **Setup pipeline and Cursor configuration** – [docs/PIPELINE.md](docs/PIPELINE.md) documents the setup sequence: Environment → Start stack → Register gateways (full stack) → **Cursor configuration** → Restart Cursor. README updated with pipeline section and Cursor configuration as step 4. `.cursor/rules/pipeline-cursor-config.mdc` added so the agent includes Cursor Configuration when documenting or automating setup. `scripts/full-setup.sh` runs the full pipeline (optionally with `USE_FULL_STACK=1` for full stack); Cursor must be restarted after.
