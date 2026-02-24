# System Architecture Overview

## Purpose
Guide Serena when editing code related to the MCP Gateway's overall architecture, component interactions, and data flow.

## Key Files
- `docs/architecture/OVERVIEW.md` — Complete architecture documentation
- `PROJECT_CONTEXT.md` — Project roadmap and implementation status
- `docker-compose.yml` — Core service orchestration
- `config/gateways.txt` — Gateway definitions
- `config/virtual-servers.txt` — 79 virtual server configurations

## Architecture

**System Flow**:
```
IDE/Client → NPX Client → MCP Gateway (Port 4444) → Virtual Servers → Upstream Services
```

**5 Core Services**:
1. Gateway (Context Forge): Aggregates 20+ MCP servers, JWT auth, Admin UI
2. Service Manager: Docker lifecycle, sleep/wake, resource monitoring
3. Tool Router: Dynamic tool selection with AI/keyword scoring
4. Web Admin: Next.js UI for configuration management
5. Filesystem Server: File operations

**Data Flow**:
- JWT authentication on every request (7-day tokens)
- Virtual servers group tools to stay under IDE 60-tool limit
- Tool router exposes 1-2 tools, queries gateway API dynamically
- Translate services convert stdio MCP servers to HTTP/SSE

**Component Interactions**:
- NPX client handles JWT generation and protocol translation
- Gateway routes requests to virtual servers by UUID
- Virtual servers filter tools from upstream gateways
- Service manager handles Docker pause/unpause for efficiency

## Critical Constraints
- Virtual servers MUST NOT exceed 60 tools per IDE connection
- JWT tokens expire after 7 days maximum
- Gateway startup MUST complete under 10 seconds
- All secrets MUST be 32+ characters
- Tool router response time MUST be under 500ms (actual: 50-100ms)
- Service health checks MUST respond within 5 seconds
