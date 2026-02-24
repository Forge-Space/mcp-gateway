# MCP Gateway Project Overview

## Purpose
Self-hosted MCP (Model Context Protocol) gateway — aggregates, routes, and manages multiple MCP servers through a single entry point. Includes an AI-powered tool router, service manager, and Dribbble MCP server.

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
