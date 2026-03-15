# MCP Gateway Project Overview

## Purpose
Self-hosted MCP (Model Context Protocol) gateway — the central AI tool routing hub for the Forge Space ecosystem ("The Open Full-Stack AI Workspace"). Aggregates, routes, and manages multiple MCP servers through a single entry point. Includes an AI-powered tool router, service manager, and Dribbble MCP server. Key differentiator: MCP-native composable architecture enabling multi-LLM support and custom tool chains.

## Tech Stack
- **Language**: Python 3.11+ (primary), TypeScript (npm wrapper/entry)
- **Build**: setuptools, npm for TS wrapper
- **Testing**: pytest with coverage (>=80%)
- **Linting**: ruff (Python), ESLint (TypeScript), shellcheck (bash)
- **Formatting**: ruff format (Python), Prettier (TypeScript)
- **Infrastructure**: Docker Compose, Colima (macOS)
- **Auth**: JWT-based authentication
- **Database**: SQLite (mcp.db)

## Repository Structure
```
mcp-gateway/
├── tool_router/        # Core Python: AI tool routing, scoring, caching
│   ├── ai/            # AI-powered tool selection (feedback, prompts, selector)
│   ├── core/          # Core server logic
│   ├── scoring/       # Tool matching and scoring
│   ├── cache/         # Caching layer
│   ├── security/      # Security modules
│   ├── training/      # Specialist training
│   ├── specialists/   # Domain specialist modules
│   ├── gateway/       # Gateway client
│   ├── tools/         # Tool definitions
│   ├── mcp_tools/     # MCP tool implementations
│   └── tests/         # Python test suite
├── dribbble_mcp/      # Dribbble design search MCP server
├── service-manager/   # Docker service lifecycle manager
├── src/               # TypeScript entry (index.ts — npm wrapper)
├── scripts/           # Setup, registration, IDE config, utilities
├── docker/            # Docker configurations
├── config/            # Configuration files
├── apps/              # Application configs
└── patterns/          # Shared patterns (from forge-patterns)
```

## Key Subsystems
- **Tool Router**: AI-powered routing of MCP tool calls to the best server
- **Scoring/Matcher**: Ranks tools by relevance for incoming requests
- **Service Manager**: Docker container lifecycle (sleep/wake, health checks)
- **Gateway Client**: Connects to upstream MCP servers
- **Specialist Coordinator**: Manages domain-specific AI specialists

## Package Info
- **Name**: mcp-gateway
- **Version**: 1.7.7
- **Python package**: mcp-gateway (setuptools)
- **npm package**: npx wrapper entry point
- **Upstream dependency**: @forgespace/core (forge-patterns)

## Coverage & CI
- 94.27% test coverage (gate: 80%), 1794+ tests passing (zero conftest exclusions)
- CI `--ignore`: only `performance/`. Zero unit file exclusions.
- pyproject.toml `addopts` is single source of truth for pytest flags — NEVER use `--override-ini`
- `filterwarnings` config: DeprecationWarning as error, ResourceWarning ignored
- 4-job CI pipeline: lint → test → build → security
- Release pipeline: `release-automation.yml` → `make test` → pyproject.toml addopts
- `CLAUDE.md` is gitignored — use `git add -f CLAUDE.md` to stage
- Test restoration COMPLETE: 184 → 904 → 1567 → 1670 → 1794+ tests
- v1.7.7 released (2026-02-28): Python 3.14 deprecation cleanup + coverage 91→94%
- v1.7.6: Docker/scripts cleanup, v1.7.5: hono IP spoofing fix
- v1.7.7+: PR #93 merged (2026-03-01) — all 1188 ruff lint errors fixed, per-file-ignores for non-source dirs
- Current state (2026-03-15): 0 open PRs; CI green; main at commit 62ceb99
  - PRs #182-#190 all merged; version 1.11.0; 1994 tests; coverage 91.30%
  - Phase 1 FR-2: make list-servers / enable-server / disable-server (scripts/utils/manage-servers.py)
  - Phase 2 IDE Integration: all 5 IDEs (Zed added), mcp-wrapper.sh fixed, cross-platform detection
  - Security: audit endpoints RBAC enforced (AUDIT_READ required)
  - Coverage: api/gateway/observability unblinded from omit list
  - tests/ dir added to CI (excluding stale infrastructure/ and integration files)
- Remaining excluded: performance/ only (via --ignore). Zero conftest exclusions.
- Known: repository-dispatch needs PAT, GitGuardian API key expired (non-blocking)
- v1.8.1+ (2026-03-07): PR #103 webapp routing, #129 OpenAPI enrichment, #132 rate limit headers, #133 ARCHITECTURE.md — all MERGED
- Issue templates added (PR #131 MERGED). 3 good-first-issues created (#134-#136)
- Tooling analysis: P0 gaps identified — security scans non-blocking, FastAPI/uvicorn not pinned, Dockerfile uses Python 3.14 (should be 3.12)
- Recommended additions: OpenTelemetry (P1), Semgrep+Trivy (P1), prometheus-client (P2)- v1.12.0 released (2026-03-15 session 7): PRs #199-#202
  - GET/PATCH /servers*, GET /ide/detect API (38 tests; 1860 total)
  - SQLite conn leak fix in RAGManagerTool; fastapi-common-bugs skill +2 patterns
  - Admin UI wired to real gateway API (PR #202 open; build passes)
  - Next: merge PR #202 → Phase 3 Advanced Features or Phase 4 Multi-Cloud
