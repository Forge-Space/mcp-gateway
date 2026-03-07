# Architecture

## Overview

The MCP Gateway is a routing hub for the Forge Space IDP. It provides centralized access to MCP servers through a FastAPI HTTP endpoint with JWT authentication, RBAC, security middleware, audit logging, and quality gates for AI-generated code.

**Stack**: Python 3.12, FastAPI, Docker Compose, Redis (optional), Supabase (auth)

## Request Flow

```
Client (Siza webapp, Cursor IDE)
  │ POST /rpc or /rpc/stream
  │ Authorization: Bearer <Supabase JWT>
  ▼
┌─────────────────────────────────────┐
│ 1. CORS Middleware                  │
│ 2. JWT Authentication               │
│    JoseJWTValidator → JWKS → payload│
│ 3. RBAC Authorization               │
│    RBACEvaluator → role permissions  │
│ 4. Security Middleware               │
│    Input sanitization + rate limiting│
│ 5. RPC Handler                       │
│    JSON-RPC 2.0: tools/list or call  │
│ 6. Gateway Client                    │
│    HTTP → upstream MCP server        │
│ 7. Quality Gates                     │
│    Security + structure + size checks│
│ 8. Response                          │
│    JSON-RPC or SSE stream            │
└─────────────────────────────────────┘
```

## Module Map

```
tool_router/
├── http_server.py          # FastAPI app, CORS, startup hooks
├── api/                    # REST/RPC endpoints
│   ├── rpc_handler.py      # JSON-RPC 2.0 (tools/list, tools/call)
│   ├── dependencies.py     # JWT validation, SecurityContext
│   ├── audit.py            # Audit trail API
│   ├── health.py           # Health/readiness/liveness probes
│   ├── performance.py      # Cache metrics, system stats
│   └── quality_gates.py    # Code quality checks
├── security/               # Auth, RBAC, rate limiting
│   ├── auth.py             # JoseJWTValidator (JWKS-based)
│   ├── authorization.py    # RBACEvaluator (4 roles)
│   ├── security_middleware.py  # Pre-request orchestrator
│   ├── audit_logger.py     # Structured audit events
│   ├── input_validator.py  # Sanitization, injection detection
│   └── rate_limiter.py     # Token bucket (Redis backend)
├── gateway/                # Upstream MCP client
│   └── client.py           # HTTP client with retry + context propagation
├── cache/                  # Multi-tier caching (memory + Redis)
├── database/               # Supabase client + query cache
├── transport/              # Protocol adapters (HTTP, stdio)
├── ai/                     # AI-powered tool selection (optional)
├── scoring/                # Tool scoring algorithms
└── tests/                  # 1778 tests
```

## API Surface (21 endpoints)

| Tag | Endpoints |
|-----|-----------|
| **rpc** | `POST /rpc` (JSON-RPC), `POST /rpc/stream` (SSE) |
| **audit** | `GET /audit/events`, `GET /audit/summary` |
| **health** | `GET /`, `GET /health`, `GET /ready`, `GET /live`, `GET /health/database`, `POST /health/close` |
| **monitoring** | `GET /monitoring/health`, `GET /monitoring/metrics/cache`, `GET /monitoring/metrics/system`, `GET /monitoring/performance`, `POST /monitoring/metrics/cache/reset`, `POST /monitoring/cache/clear`, `GET /monitoring/cache/info`, `POST /monitoring/query-cache/invalidate` |

Full OpenAPI spec at `/docs` (Swagger) or `/openapi.json`.

## Security Model

**JWT**: Supabase RS256 tokens via JWKS. Validates issuer, audience, expiration.

**RBAC Roles**: admin (all), developer (CRUD + tools), user (read/write + tools), guest (read-only).

**Rate Limiting**: Token bucket with Redis. Per-user limits with penalty system.

**Audit Trail**: Every request logged (timestamp, user_id, IP, endpoint, details).

## Deployment (Docker Compose)

| Service | Port | Purpose |
|---------|------|---------|
| tool-router | 8030 | This gateway (FastAPI) |
| gateway | 4444 | Context Forge (upstream MCP manager) |
| service-manager | 9000 | Dynamic MCP server lifecycle |
| ollama | 11434 | AI tool selection (optional) |
| redis | 6379 | Distributed cache (optional) |

## Extension Points

**MCP Spokes**: Register via Admin UI (port 4444). No code changes needed.

**Quality Gates**: Add gate function in `api/quality_gates.py`, return `GateResult`, update weights.

**RBAC Permissions**: Extend `Permission` enum in `security/authorization.py`, add to role map.

**Cache Backends**: Implement `CacheBackend` protocol in `cache/`.

**Audit Sinks**: Extend `SecurityAuditLogger` for external systems (Sentry, Datadog).
