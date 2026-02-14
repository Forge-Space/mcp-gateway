# MCP Gateway - Project Plan & Context

> **Non-tracked file** - Local project planning, AI agent context, and implementation roadmap.
> **Cost Constraint:** All features must be costless (self-hosted, open-source, no paid APIs).

**Last Updated:** 2025-02-14
**Version:** Phase 3.3 Complete

---

## 🎯 Project Overview

**MCP Gateway** is a self-hosted aggregation layer for Model Context Protocol (MCP) servers that solves IDE tool limits by providing intelligent tool routing and virtual server management.

### Problem Statement
- IDEs have tool limits (~60 tools) causing warnings and performance issues
- Managing multiple MCP servers requires multiple IDE connections
- No intelligent tool selection - users must know which tool to use

### Solution
- **Gateway Aggregation** - Single connection point for all MCP servers
- **Virtual Servers** - Organize tools into collections under tool limits
- **Tool Router** - AI-powered tool selection from natural language tasks
- **Costless** - Fully self-hosted with no recurring costs

### Key Metrics
- **Architecture:** Monorepo (Python + TypeScript)
- **Test Coverage:** 100% for testable code
- **Components:** 5 main (Gateway, Virtual Servers, Tool Router, Translate, Client)
- **Documentation:** Hierarchical structure with 7 categories
- **Observability:** Health checks, structured logging, metrics collection

---

## 📊 Current State (Phase 3.3 Complete)

### ✅ Phase 1: Foundation (Complete)
- **Package Structure** - Modular tool_router package with clean boundaries
- **Configuration Management** - GatewayConfig with env-based loading
- **Scripts & Error Handling** - Robust shell scripts with structured errors
- **JWT Authentication** - Secure token generation and validation

### ✅ Phase 2: Quality & Testing (Complete)
- **Dependency Injection** - Protocol-based GatewayClient for testability
- **Integration Tests** - End-to-end test coverage
- **CI/CD Pipeline** - GitHub Actions for lint, test, coverage
- **Test Coverage** - 100% for testable code paths

### ✅ Phase 3.1: Monorepo Build System (Complete)
- **TypeScript Integration** - NPX-compatible MCP client
- **Python Coordination** - FastMCP-based tool router
- **Build Orchestration** - Make-based build system
- **Package Publishing** - NPM package ready (@mcp-gateway/client)

### ✅ Phase 3.2: Documentation Structure (Complete)
- **Hierarchical Organization** - 7 category folders (setup, architecture, config, dev, ops, migration, tools)
- **Comprehensive Guides** - Installation, architecture overview, virtual servers
- **Cross-Referenced** - Links between related docs
- **AI-Friendly** - Clear structure for agent context loading

### ✅ Phase 3.3: Observability (Complete)
- **Health Checks** - Component-level monitoring (gateway, config)
- **Structured Logging** - Key=value format with log context
- **Metrics Collection** - Thread-safe timing and counters
- **Server Instrumentation** - Integrated into execute_task and search_tools
- **Test Coverage** - 25 tests, 100% pass rate

---

## 🏗️ Architecture Components

### 1. MCP Gateway (Context Forge)
- **Role:** Central aggregation hub
- **Tech:** IBM Context Forge, FastAPI, SQLite
- **Features:** JWT auth, virtual servers, admin UI
- **Cost:** $0 (self-hosted Docker)

### 2. Virtual Servers
- **Role:** Tool organization under IDE limits
- **Types:** cursor-default (all tools), cursor-router (single entry), custom collections
- **Cost:** $0 (configuration only)

### 3. Tool Router
- **Role:** Intelligent tool selection from natural language
- **Tech:** Python FastMCP, semantic scoring
- **Endpoints:** execute_task, search_tools
- **Cost:** $0 (local compute)

### 4. Translate Services
- **Role:** stdio→HTTP/SSE conversion for MCP servers
- **Examples:** sequential-thinking, playwright, snyk
- **Cost:** $0 (Docker containers)

### 5. TypeScript Client
- **Role:** NPX-compatible IDE connector
- **Package:** @mcp-gateway/client
- **Cost:** $0 (open-source, npm)

---

## 🚀 Future Phases (Roadmap)

### Phase 4: Performance & Caching (Next)
**Goal:** Improve response times and reduce gateway load

#### 4.1 Tool Metadata Caching
- **Problem:** Gateway API calls on every task (latency overhead)
- **Solution:** Local cache with TTL and invalidation
- **Implementation:**
  - In-memory cache (Python dict) for tool definitions
  - 5-minute TTL with manual refresh endpoint
  - Cache warming on startup
- **Cost:** $0 (local memory)

#### 4.2 Connection Pooling
- **Problem:** New HTTP connection per request
- **Solution:** Connection pool with keep-alive
- **Implementation:**
  - Use urllib3 PoolManager (already in stdlib)
  - Max 10 connections, 30s timeout
  - Retry logic on connection errors
- **Cost:** $0 (stdlib)

#### 4.3 Async Tool Execution
- **Problem:** Sequential tool calls block main thread
- **Solution:** Async execution for independent tasks
- **Implementation:**
  - FastMCP async endpoints
  - asyncio.gather for parallel calls
  - Timeout handling per tool
- **Cost:** $0 (Python asyncio)

**Deliverables:**
- Cached tool fetching (sub-100ms after warm)
- Connection pool with metrics
- Async execute_task support
- Performance documentation

---

### Phase 5: Developer Experience (Q2 2025)
**Goal:** Simplify development, testing, and debugging

#### 5.1 CLI Development Tools
- **Tools:**
  - `mcp-gateway dev` - Start dev environment
  - `mcp-gateway test-tool` - Test single tool execution
  - `mcp-gateway validate` - Check configuration
- **Implementation:** Python Click CLI
- **Cost:** $0 (Click is free)

#### 5.2 Enhanced Testing Utilities
- **Features:**
  - Mock gateway for unit tests
  - Test fixtures for common scenarios
  - Integration test helpers
- **Implementation:** pytest fixtures and mocks
- **Cost:** $0 (pytest)

#### 5.3 Debugging Tools
- **Features:**
  - Request/response inspector
  - Tool execution replay
  - Performance profiler
- **Implementation:** Python logging with JSON output
- **Cost:** $0 (stdlib logging)

**Deliverables:**
- CLI tool package
- Test utilities module
- Debugging guide documentation
- Example test suites

---

### Phase 6: Advanced Features (Q3 2025)
**Goal:** Enable complex workflows and tool composition

#### 6.1 Tool Composition
- **Feature:** Chain multiple tools in one task
- **Example:** "Search for React docs and summarize"
  - Step 1: execute tavily_search("React documentation")
  - Step 2: execute summarize(results)
- **Implementation:** DAG-based execution planner
- **Cost:** $0 (local compute)

#### 6.2 Workflow Templates
- **Feature:** Save and reuse common task sequences
- **Examples:**
  - "Debug issue" → search logs, analyze errors, suggest fixes
  - "Code review" → check style, run tests, security scan
- **Implementation:** YAML workflow definitions
- **Cost:** $0 (local files)

#### 6.3 Custom Tool Plugins
- **Feature:** User-defined tools without MCP server
- **Use Cases:** Project-specific commands, local scripts
- **Implementation:** Python plugin system with subprocess
- **Cost:** $0 (local execution)

**Deliverables:**
- Tool composition engine
- Workflow definition format
- Plugin system with examples
- Advanced usage documentation

---

### Phase 7: Production Hardening (Q4 2025)
**Goal:** Enterprise-ready deployment and monitoring

#### 7.1 High Availability
- **Features:**
  - Multi-instance gateway with load balancing
  - Shared SQLite (NFS) or PostgreSQL migration
  - Health check endpoints for orchestrators
- **Implementation:** Docker Swarm or k8s configs
- **Cost:** $0 (self-hosted infrastructure)

#### 7.2 Advanced Observability
- **Features:**
  - Prometheus metrics export
  - Grafana dashboards
  - Distributed tracing (OpenTelemetry)
- **Implementation:** Prometheus client, OTLP exporter
- **Cost:** $0 (self-hosted Prometheus + Grafana)

#### 7.3 Security Hardening
- **Features:**
  - JWT rotation and revocation
  - Rate limiting per client
  - Audit logging
- **Implementation:** Redis for rate limits, structured audit logs
- **Cost:** $0 (self-hosted Redis)

**Deliverables:**
- HA deployment guides
- Monitoring stack (Prometheus + Grafana)
- Security best practices
- Production operations runbook

---

## 🤖 AI Agent Quick-Start Guide

### For New AI Agents
**Context Loading Priority:**
1. Read this PLAN.md (you're here!)
2. Read `docs/architecture/OVERVIEW.md` - System architecture
3. Read `docs/architecture/TOOL_ROUTER_GUIDE.md` - Core component details
4. Read `CHANGELOG.md` - Recent changes
5. Explore `tool_router/` - Main codebase

### Key Files to Understand
```
tool_router/
├── core/
│   ├── server.py         # FastMCP endpoints (execute_task, search_tools)
│   └── config.py         # Configuration management
├── gateway/
│   └── client.py         # HTTPGatewayClient with retry logic
├── scoring/
│   └── matcher.py        # Tool relevance scoring algorithm
├── observability/
│   ├── health.py         # Health check system
│   ├── logger.py         # Structured logging
│   └── metrics.py        # Metrics collection
└── tests/                # Comprehensive test suite
```

### Common Tasks
**Run Tests:**
```bash
make test                 # All tests
make test-unit           # Unit tests only
make test-integration    # Integration tests
make coverage            # Coverage report
```

**Start Gateway:**
```bash
make start               # Start gateway stack
make register            # Register gateways & virtual servers
make stop                # Stop stack
```

**Development:**
```bash
make lint                # Ruff linter
make format              # Code formatting
make type-check          # Type checking
```

### Debugging Tips
1. **Check logs:** `docker compose logs gateway tool-router`
2. **Verify config:** `make jwt` and check `.env`
3. **Test tools:** `curl http://localhost:4444/tools`
4. **Inspect metrics:** Call `get_metrics().get_all_metrics()`
5. **Health status:** Call `HealthCheck().check_all()`

---

## 💰 Cost Constraint Principles

### Core Philosophy
**All features must be achievable at $0 recurring cost.**

### Approved Technologies
✅ **Infrastructure:**
- Docker & Docker Compose (self-hosted)
- SQLite or PostgreSQL (self-hosted)
- Nginx/Traefik (self-hosted reverse proxy)

✅ **Monitoring:**
- Prometheus (self-hosted metrics)
- Grafana (self-hosted dashboards)
- OpenTelemetry (self-hosted tracing)

✅ **Languages & Frameworks:**
- Python (free, stdlib-first)
- TypeScript/Node.js (free, npm)
- FastAPI/FastMCP (free frameworks)

✅ **Development Tools:**
- GitHub Actions (free tier: 2000 min/month)
- pytest, ruff, mypy (free tools)
- Docker Hub (free public images)

### Prohibited Technologies
❌ **Paid APIs:**
- No OpenAI, Anthropic, Google AI APIs
- No commercial LLM services
- No paid search APIs

❌ **Managed Services:**
- No AWS/GCP/Azure managed databases
- No managed Redis/monitoring services
- No commercial API gateways

❌ **Commercial Software:**
- No paid IDEs (prefer VSCode, Windsurf)
- No paid monitoring tools
- No proprietary databases

### Cost Decision Framework
**Before adding a dependency, ask:**
1. ✅ Is it free and open-source?
2. ✅ Can it run self-hosted?
3. ✅ Does it have no recurring costs?
4. ✅ Is there a free tier sufficient for our use?

If any answer is "no", find an alternative or build it ourselves.

---

## 🔧 Technology Stack Rationale

### Backend: Python + FastAPI
- **Why:** Free, excellent stdlib, FastMCP integration
- **Cost:** $0
- **Alternatives Considered:** Go (more verbose), Node.js (less mature typing)

### Frontend: TypeScript + Node.js
- **Why:** NPX compatibility, wide IDE support
- **Cost:** $0 (npm free tier)
- **Alternatives Considered:** Pure Python (no NPX support)

### Database: SQLite
- **Why:** Zero-config, file-based, sufficient for single-instance
- **Cost:** $0
- **Future:** PostgreSQL for multi-instance (also free)

### Container: Docker
- **Why:** Industry standard, free, cross-platform
- **Cost:** $0
- **Alternatives Considered:** Podman (less tooling support)

### Testing: pytest
- **Why:** Python standard, excellent fixtures
- **Cost:** $0
- **Alternatives Considered:** unittest (less features)

### CI/CD: GitHub Actions
- **Why:** Free tier sufficient (2000 min/month), integrated
- **Cost:** $0
- **Alternatives Considered:** GitLab CI (less GitHub integration)

---

## 📈 Success Metrics

### Performance Targets
- **Tool Selection:** <100ms (cached), <500ms (uncached)
- **Gateway Latency:** <50ms overhead per request
- **Test Coverage:** 100% for testable code
- **Build Time:** <30s full build
- **Startup Time:** <5s tool router, <30s gateway stack

### Quality Targets
- **Zero Regressions:** All tests pass on main
- **Lint Clean:** No ruff/mypy errors
- **Documentation:** Every feature documented before release
- **Test Coverage:** Maintain 100% for new code

### User Experience Targets
- **Setup Time:** <10 minutes from clone to working
- **IDE Tool Limit:** Never exceed 60 tools
- **Error Messages:** Clear, actionable, with links to docs
- **Response Quality:** >90% correct tool selection

---

## 🔄 Development Workflow

### For Feature Development
1. **Plan:** Update this PLAN.md with feature details
2. **Branch:** `feat/<scope>-<description>`
3. **Implement:** TDD approach (tests first)
4. **Document:** Update relevant docs in `docs/`
5. **Test:** `make test coverage` (100% required)
6. **Lint:** `make lint format type-check`
7. **Commit:** Follow conventional commits
8. **PR:** Template checklist, get review
9. **Merge:** Squash or rebase, update CHANGELOG.md

### For Bug Fixes
1. **Reproduce:** Write failing test
2. **Fix:** Minimal change to pass test
3. **Verify:** All tests pass
4. **Document:** Add troubleshooting if needed
5. **Branch:** `fix/<scope>-<description>`
6. **Commit:** Conventional commits
7. **PR:** Link to issue, get review

### For Documentation
1. **Identify Gap:** What's missing or unclear?
2. **Research:** Verify technical accuracy
3. **Write:** Clear, concise, with examples
4. **Cross-Link:** Link from/to related docs
5. **Review:** Technical accuracy check
6. **Branch:** `docs/<topic>`

---

## 🎓 Learning Resources

### MCP Protocol
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

### Project-Specific
- `docs/architecture/OVERVIEW.md` - System design
- `docs/architecture/TOOL_ROUTER_GUIDE.md` - Tool router deep dive
- `docs/operations/MONITORING.md` - Observability guide
- `CHANGELOG.md` - Change history

### Python Best Practices
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Linter](https://docs.astral.sh/ruff/)

---

## 🐛 Troubleshooting Guide

### Common Issues

**Gateway Not Starting:**
- Check Docker: `docker ps`
- Check logs: `docker compose logs gateway`
- Verify JWT: `make jwt` and check `.env`
- Ports in use: `lsof -i :4444`

**Tool Router Not Finding Tools:**
- Verify gateway URL: `curl http://localhost:4444/tools`
- Check JWT in env: `echo $GATEWAY_JWT`
- Review logs: `docker compose logs tool-router`
- Test health: `HealthCheck().check_all()`

**Tests Failing:**
- Clean cache: `rm -rf .pytest_cache __pycache__`
- Reinstall deps: `pip install -e .`
- Check versions: `python --version` (need 3.9+)
- Verbose output: `pytest -vv --tb=short`

**High Latency:**
- Check metrics: `get_metrics().get_all_metrics()`
- Enable debug logs: `setup_logging(level="DEBUG")`
- Profile tool selection: Look at `pick_best_tools` timing
- Gateway health: `HealthCheck().check_gateway_connection()`

---

## 📝 Notes for Future Development

### Performance Optimizations
- Consider Rust for tool scoring if Python becomes bottleneck
- Explore gRPC for gateway communication (lower latency)
- Implement request batching for multiple tool calls
- Add circuit breakers for unreliable MCP servers

### Feature Ideas (Backlog)
- **Tool Versioning:** Track and select tool versions
- **Usage Analytics:** Anonymous usage patterns for optimization
- **Tool Marketplace:** Community-contributed tool collections
- **Offline Mode:** Cache tools for offline development
- **Mobile Client:** React Native MCP client

### Known Limitations
- SQLite single-writer (not issue for current scale)
- Tool scoring is heuristic (could use embeddings)
- No tool execution timeout per tool (global only)
- JWT refresh not implemented (manual rotation)

### Security Considerations
- JWT secret must be rotated regularly (manual for now)
- No rate limiting yet (add in Phase 7)
- Audit logging not comprehensive (add in Phase 7)
- Input validation basic (enhance as needed)

---

## 🤝 Contributing Guidelines

### Before You Start
1. Read this PLAN.md completely
2. Review `docs/architecture/OVERVIEW.md`
3. Set up development environment (`make dev`)
4. Run tests to verify setup (`make test`)

### Code Style
- **Python:** Ruff + mypy (strict mode)
- **TypeScript:** Prettier + ESLint
- **Max Line Length:** 88 chars (Python), 100 (TS)
- **Type Hints:** Required for all functions
- **Docstrings:** Required for public APIs

### Commit Messages
Follow Angular conventional commits:
```
feat(router): add caching for tool metadata
fix(client): retry on network timeout
docs(ops): add monitoring guide
test(scoring): add edge cases for empty query
chore(deps): update pytest to 8.4.2
```

### Testing Requirements
- **Unit Tests:** All business logic
- **Integration Tests:** End-to-end flows
- **Coverage:** 100% for new code
- **Performance:** No regressions in benchmarks

---

## 📞 Contact & Support

This is a self-hosted project with no commercial support. For issues:
1. Check this PLAN.md
2. Review documentation in `docs/`
3. Search existing issues on GitHub
4. Open new issue with reproduction steps

**Maintainer:** Lucas Santana
**Repository:** [mcp-gateway](https://github.com/lucassantana/mcp-gateway)
**License:** MIT

---

**Remember:** Every feature must be costless. If it requires money, find another way or skip it.
