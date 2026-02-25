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
- **Version**: 1.7.0
- **Python package**: mcp-gateway (setuptools)
- **npm package**: npx wrapper entry point
- **Upstream dependency**: @forgespace/core (forge-patterns)

## Coverage & CI
- 88.98% test coverage (gate: 80%), 267 tests passing
- Infrastructure modules excluded via `[tool.coverage.run] omit` (directory wildcards)
- Test exclusions via `--ignore` flags in Makefile and ci.yml (aligned)
- pyproject.toml `addopts` is single source of truth for pytest flags — NEVER use `--override-ini`
- 4-job CI pipeline: lint → test → build → security
- Release pipeline: `release-automation.yml` → `make test` → pyproject.toml addopts
- `CLAUDE.md` is gitignored — use `git add -f CLAUDE.md` to stage
- PR #64 (2026-02-25): Fixed coverage collection by removing `--override-ini`