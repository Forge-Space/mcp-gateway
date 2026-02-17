# MCP Gateway - Project Context & Guide

**Version**: 0.7.0
**Last Updated**: 2025-02-16
**Status**: Active Development - Phase 7 (Next.js Admin UI)

---

## 📋 Executive Summary

**What**: MCP Gateway is a universal router and proxy for Model Context Protocol (MCP) servers, enabling IDEs (Windsurf, Cursor) to connect to multiple MCP servers through a single gateway with intelligent AI-powered tool selection.

**Why**: Simplifies MCP server management, provides intelligent tool routing using local LLMs (Ollama), and offers centralized observability for MCP ecosystems.

**Current State (v0.7.0)**: Production-ready AI router with Ollama integration, monorepo architecture, YAML-based configuration system, comprehensive observability APIs, automated IDE configuration generation, unified CLI tool, feature toggle system, and 86.20% test coverage — up from a 43.14% baseline measured immediately after the architecture migration.

---

## 🎯 Project Vision & Strategy

### Core Mission
Enable seamless integration between AI-powered IDEs and MCP servers through intelligent routing, robust lifecycle management, and developer-friendly tooling.

### Strategic Pillars
1. **Intelligence First**: AI-powered tool selection with hybrid scoring (AI + keyword matching)
2. **Developer Experience**: CLI-first approach with automated configuration generation
3. **Observability**: Real-time metrics and health monitoring for production deployments
4. **Pragmatic Architecture**: Enhance existing systems rather than rebuild from scratch

### Success Metrics
- **Performance**: <2s AI router response time, 60% faster startup with selective server loading ✅
- **Accuracy**: 30%+ improvement in tool selection vs. keyword-only matching ✅
- **Coverage**: ≥85% test coverage achieved (86.20%) ✅
- **Adoption**: Seamless IDE integration for Windsurf and Cursor users ✅
- **Developer Experience**: <2 min from install to first connection ✅

---

## 🏗️ Architecture Overview

### System Components

```text
┌─────────────────────────────────────────────────────────────┐
│                         IDEs                                 │
│              (Windsurf, Cursor, Claude Desktop)             │
└────────────────────┬────────────────────────────────────────┘
                     │ MCP Protocol
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Gateway (Port 4444)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Tool Router  │  │  Next.js     │  │   Gateway    │     │
│  │  (Python)    │  │  Admin UI    │  │   Client     │     │
│  │  + FastMCP   │  │  (React)     │  │  (TypeScript)│     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
│         │                                                    │
│         ├─► AI Selector (Ollama) ──► Hybrid Scoring        │
│         ├─► Keyword Matcher ────────► Fallback Logic       │
│         ├─► Feature Toggles ─────────► 17 Controls         │
│         └─► Observability ───────────► Metrics/Health      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Virtual MCP Servers (JSON-based configs)            │
│  brave-search, github, filesystem, memory, puppeteer, etc.  │
│  Enable/disable for optimized resource usage                │
└─────────────────────────────────────────────────────────────┘
```
```

### Project Structure (Target Monorepo Architecture - Partially Migrated)

```
mcp-gateway/
├── apps/
│   ├── tool-router/          # Python MCP server (self-contained)
│   │   ├── src/tool_router/
│   │   ├── tests/{unit,integration,e2e}/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── web-admin/            # Next.js admin UI
│   └── mcp-client/           # TypeScript client
├── config/
│   ├── development/          # Dev YAML configs
│   ├── production/           # Prod YAML configs
│   ├── test/                 # Test YAML configs
│   └── schemas/              # JSON validation schemas
├── docker/
│   └── docker-compose.yml
├── docker-compose.yml          # Root-level (legacy, to be moved)
├── scripts/
│   ├── lib/                  # Shared libraries
│   └── migrate-architecture.sh
└── docs/
    ├── architecture/
    └── CONFIG_MIGRATION.md
```

**Migration Status**: The repository is partially migrated to the monorepo structure. The `apps/tool-router/` structure is implemented, but the root-level `tool_router/` directory still exists for backward compatibility. See `MIGRATION_SUMMARY.md` for complete migration details and timeline.

### Legacy Structure (Pre-Migration)

**Note**: The root-level `tool_router/` directory structure is deprecated and maintained only for backward compatibility during the migration period. All new development should target the `apps/tool-router/` structure shown above.

### Technology Stack

**Backend (Tool Router)**
- Python 3.9+ (3.14 compatible)
- FastMCP for MCP protocol
- Ollama for AI tool selection (llama3.2:3b default)
- pytest for testing (≥85% coverage requirement)
- PyYAML for configuration parsing

**Frontend (Admin UI)**
- Context Forge Admin UI (existing legacy system, currently in use)
- Next.js Admin UI (Phase 7 replacement, planned migration Q1 2026)
  - Migration owner: TBD
  - Context Forge will be deprecated post-migration
  - Next.js UI will provide feature toggle management, virtual server lifecycle, gateway monitoring
- React components for server management
- Real-time status updates via WebSocket

**Configuration**
- YAML-based configs (gateways, prompts, resources)
- Environment-specific: development, production, test
- JSON Schema validation
- Backward compatible with .txt format
- yq for shell script parsing

**Infrastructure**
- Docker Compose for orchestration (docker/docker-compose.yml)
- Ollama service (local LLM)
- PostgreSQL for persistence (Context Forge)
- Redis for caching (optional)

**DevOps**
- Make for automation
- Unified `mcp` CLI tool (bash)
- Shell completions (bash, zsh, fish)
- GitHub Actions for CI/CD
- Pre-commit hooks (ruff, shellcheck, prettier)

**CLI Tools**
- `mcp wizard` - Interactive setup wizard
- `mcp ide detect` - Detect installed IDEs
- `mcp logs` - View gateway logs
- `mcp doctor` - Health check and diagnostics
- `mcp completion` - Shell completion generation

---

## 📊 Current Implementation Status

### ✅ Completed Features (Sprints 1-6)

#### Sprint 1: AI Router Foundation
- **Status**: 100% Complete
- **Coverage**: 88.29% (22 tests)
- **Features**:
  - Ollama integration with llama3.2:3b model
  - Hybrid scoring: AI confidence (70%) + keyword matching (30%)
  - Automatic fallback on timeout/low confidence
  - Configurable via environment variables
  - Docker Compose integration
  - Comprehensive operational guide

#### Sprint 2: Observability & Management
- **Status**: 100% Complete
- **Coverage**: 96.67% (API module: 98%)
- **Features**:
  - `get_ai_router_metrics_tool` - Real-time performance metrics
  - `get_ai_router_health_tool` - Health status and diagnostics
  - Selection method tracking (AI vs keyword)
  - Confidence statistics and fallback monitoring
  - Updated operational documentation

#### Sprint 3: IDE Configuration Generator
- **Status**: 100% Complete
- **Coverage**: 100% (IDE config API)
- **Features**:
  - Python API: `generate_ide_config()`
  - CLI tool: `scripts/ide/generate-config.sh`
  - Makefile commands: `ide-config`, `ide-windsurf`, `ide-cursor`
  - MCP tool: `generate_ide_config_tool`
  - Support for local and remote (JWT) connections
  - Auto-detection of server UUIDs with fallback

#### Sprint 4: Virtual Server Lifecycle Backend
- **Status**: 100% Complete
- **Coverage**: ≥85%
- **Features**:
  - Enable/disable servers via configuration
  - Shell scripts: `enable.sh`, `disable.sh`, `list-enabled.sh`
  - Makefile commands: `enable-server`, `disable-server`, `list-enabled`
  - REST API endpoints for lifecycle management
  - MCP tools for programmatic control
  - Backward compatible configuration format
  - ~60% faster startup with selective loading

#### Sprint 5: Unified CLI Tool
- **Status**: 100% Complete
- **Coverage**: Shell scripts validated with shellcheck
- **Features**:
  - Unified `mcp` CLI tool for common operations
  - Interactive setup wizard with `gum` integration
  - Arrow-key navigation for server selection
  - Automatic JWT generation and storage
  - Shell completions (bash, zsh, fish)
  - ASCII art banners with `figlet` (optional)
  - Health check and diagnostics (`mcp doctor`)
  - IDE detection and configuration

#### Sprint 6: Feature Toggle System
- **Status**: 100% Complete
- **Coverage**: ≥85% (feature management module)
- **Features**:
  - YAML-based configuration (`config/features.yaml`)
  - 17 fine-grained feature controls
  - Categories: CORE, API, TOOL, UI
  - Environment variable overrides
  - REST API for feature management
  - Backward compatibility with `ROUTER_AI_ENABLED`
  - Runtime feature checking
  - Comprehensive test suite

#### Sprint 7: Test Coverage Improvements
- **Status**: 100% Complete
- **Overall Coverage**: 86.20% (up from 72.74%)
- **Achievements**:
  - 74 new tests added (163 → 237 total tests)
  - Modules at 100%: config.py, args/builder.py, prompts.py, metrics.py
  - Modules above 95%: gateway/client.py (97.62%), health.py (95%)
  - Comprehensive error path coverage
  - Edge case testing for all critical modules

### 🚧 In Progress

#### Sprint 8: Next.js Admin UI
- **Status**: Planning Phase
- **Goal**: Visual management interface for gateway operations
- **Estimated Coverage**: ≥85%
- **Planned Features**:
  - Feature toggle management dashboard
  - Virtual server lifecycle management UI
  - Gateway status monitoring
  - Real-time metrics visualization
  - Responsive design with Tailwind CSS
  - Dark mode support

---

## 🎯 Functional Requirements

### FR-001: AI-Powered Tool Selection
**Priority**: P0 (Critical)
**Status**: ✅ Implemented

**Description**: Route user queries to the most appropriate MCP tool using AI analysis combined with keyword matching.

**Acceptance Criteria**:
- ✅ AI selector returns tool recommendation in <2s
- ✅ Hybrid scoring combines AI (70%) and keyword (30%) scores
- ✅ Automatic fallback to keyword-only on timeout/error
- ✅ Configurable confidence threshold (default: 0.3)
- ✅ Support for multiple Ollama models

**Business Rules**:
- BR-001.1: AI confidence below threshold triggers keyword fallback
- BR-001.2: Timeout after 5000ms triggers keyword fallback
- BR-001.3: Tool selection logged for observability
- BR-001.4: Model kept alive for 24h to prevent cold starts

---

### FR-002: Server Lifecycle Management
**Priority**: P1 (High)
**Status**: ✅ Implemented

**Description**: Enable administrators to enable/disable virtual servers to optimize resource usage and startup time.

**Acceptance Criteria**:
- ✅ Servers can be marked as enabled/disabled in configuration
- ✅ Disabled servers not created during `make register`
- ✅ CLI commands: `make enable-server`, `make disable-server`
- ✅ API endpoints for programmatic control
- ✅ Backward compatible with existing server configs
- ✅ ~60% faster startup with selective loading

**Business Rules**:
- BR-002.1: Default state is `enabled=true` for all servers
- BR-002.2: Disabled servers cannot be accessed via gateway
- BR-002.3: Enable/disable operations logged for audit
- BR-002.4: Configuration format: `Name|gateways|enabled`

---

### FR-003: IDE Configuration Automation
**Priority**: P1 (High)
**Status**: ✅ Implemented

**Description**: Automate generation and injection of MCP configuration for Windsurf and Cursor IDEs.

**Acceptance Criteria**:
- ✅ Generate valid JSON config for Windsurf
- ✅ Generate valid JSON config for Cursor
- ✅ Support local (no auth) and remote (JWT) connections
- ✅ CLI tool with argument parsing and validation
- ✅ Makefile integration for ease of use
- ✅ MCP tool for programmatic access

**Business Rules**:
- BR-003.1: Config format follows IDE-specific requirements
- BR-003.2: Server UUID auto-detected from gateway API
- BR-003.3: Fallback to server name if UUID unavailable
- BR-003.4: JWT tokens never logged or exposed

---

### FR-005: Feature Toggle Management
**Priority**: P1 (High)
**Status**: ✅ Implemented

**Description**: Centralized feature flag management system for runtime control of functionality without code changes.

**Acceptance Criteria**:
- ✅ YAML configuration file with 17 feature controls
- ✅ Environment variable overrides
- ✅ REST API for feature management
- ✅ Backward compatibility with existing env vars
- ✅ Runtime feature checking
- ✅ Comprehensive test coverage (≥85%)

**Business Rules**:
- BR-005.1: Features organized by category (CORE, API, TOOL, UI)
- BR-005.2: Environment variables take precedence over YAML
- BR-005.3: Some features require restart (e.g., AI router)
- BR-005.4: Naming convention: `FEATURE_<CATEGORY>_<NAME>`

---

### FR-006: Unified CLI Tool
**Priority**: P1 (High)
**Status**: ✅ Implemented

**Description**: Single command-line interface for all common gateway operations, replacing multiple scripts.

**Acceptance Criteria**:
- ✅ Interactive setup wizard with arrow-key navigation
- ✅ Automatic IDE detection
- ✅ JWT generation and storage
- ✅ Shell completions for bash/zsh/fish
- ✅ Health checks and diagnostics
- ✅ <2 min setup time for new users

**Business Rules**:
- BR-006.1: All operations accessible via `mcp` command
- BR-006.2: Graceful fallback when optional tools unavailable
- BR-006.3: Clear error messages with actionable guidance
- BR-006.4: Idempotent operations (safe to run multiple times)

---

### FR-004: Observability & Monitoring
**Priority**: P1 (High)
**Status**: ✅ Implemented

**Description**: Provide real-time metrics and health status for AI router and gateway operations.

**Acceptance Criteria**:
- ✅ Metrics API returns selection counts and confidence stats
- ✅ Health API reports Ollama availability and config status
- ✅ MCP tools for IDE integration
- ✅ JSON output for programmatic consumption
- ✅ Error handling with descriptive messages

**Business Rules**:
- BR-004.1: Metrics reset on server restart
- BR-004.2: Health status: healthy/degraded/unhealthy
- BR-004.3: Issues array lists detected problems
- BR-004.4: Metrics include AI usage rate calculation

---

## 🔧 Non-Functional Requirements

### NFR-001: Performance
- **AI Router Response Time**: <2s (95th percentile)
- **Keyword Fallback**: <100ms
- **Startup Time**: <30s with all servers enabled
- **Startup Time (Selective)**: <12s with 40% servers enabled
- **Gateway Throughput**: >100 requests/second

### NFR-002: Reliability
- **Availability**: 99.9% uptime for gateway
- **Error Rate**: <0.1% for tool routing
- **Fallback Success**: 100% (keyword matching always available)
- **Data Persistence**: Configuration survives restarts

### NFR-003: Scalability
- **Virtual Servers**: Support 100+ server configurations
- **Concurrent Connections**: Handle 50+ simultaneous IDE connections
- **Model Loading**: Ollama model cached for 24h
- **Memory Usage**: <2GB for gateway + router

### NFR-004: Security
- **Authentication**: JWT tokens for remote connections
- **Secrets Management**: Environment variables only, never hardcoded
- **Input Validation**: All user inputs sanitized
- **Audit Logging**: All enable/disable operations logged
- **Secrets Scanning**: Pre-commit hooks block credential leaks

### NFR-005: Maintainability
- **Test Coverage**: ≥85% for all modules (achieved: 86.20%) ✅
- **Documentation**: README, CHANGELOG, operational guides, PROJECT_CONTEXT.md
- **Code Quality**: Ruff linting, type hints, consistent style
- **Commit Conventions**: Angular conventional commits
- **CI/CD**: Automated linting, testing, security scans
- **Modular Architecture**: Clear separation of concerns (ai/, api/, core/, gateway/)

### NFR-006: Usability
- **CLI First**: All operations available via command line
- **Makefile Integration**: Simple `make` commands for common tasks
- **Error Messages**: Clear, actionable error descriptions
- **Documentation**: Comprehensive guides for operators and developers

---

## 📐 Business Rules & Constraints

### Configuration Management
- **BR-C-001**: All configuration via environment variables or config files
- **BR-C-002**: Configuration changes require server restart
- **BR-C-003**: Invalid configuration prevents server startup
- **BR-C-004**: Default values provided for all optional settings

### AI Router Behavior
- **BR-AI-001**: AI confidence threshold configurable (default: 0.3)
- **BR-AI-002**: Hybrid weight configurable (default: 0.7 AI, 0.3 keyword)
- **BR-AI-003**: Timeout configurable (default: 5000ms)
- **BR-AI-004**: Model selection configurable (default: llama3.2:3b)
- **BR-AI-005**: Fallback to keyword matching is mandatory, never fail

### Server Lifecycle
- **BR-LC-001**: Disabled servers consume no resources
- **BR-LC-002**: Enable/disable operations are idempotent
- **BR-LC-003**: Configuration format backward compatible
- **BR-LC-004**: All 79 existing configs maintained

### Testing & Quality
- **BR-QA-001**: All new features require ≥85% test coverage
- **BR-QA-002**: Tests must cover success, error, and edge cases
- **BR-QA-003**: Pre-commit hooks enforce linting and formatting
- **BR-QA-004**: CI pipeline must pass before merge

### Documentation
- **BR-DOC-001**: CHANGELOG.md updated with every feature/fix
- **BR-DOC-002**: README.md updated when behavior changes
- **BR-DOC-003**: Operational guides for production features
- **BR-DOC-004**: This PROJECT_CONTEXT.md updated with major changes

---

## 🗺️ Roadmap & Phases

### Phase 1: Foundation (Weeks 1-2) ✅ COMPLETE
**Goal**: Establish AI-powered routing with observability

**Deliverables**:
- ✅ Ollama integration with hybrid scoring
- ✅ Metrics and health APIs
- ✅ Comprehensive test coverage (88%+)
- ✅ Operational documentation

**Success Metrics**:
- ✅ <2s AI response time
- ✅ 30%+ accuracy improvement
- ✅ 96.67% API test coverage

---

### Phase 2: Developer Experience (Week 3) ✅ COMPLETE
**Goal**: Automate IDE setup and configuration

**Deliverables**:
- ✅ IDE config generator API
- ✅ CLI tools for Windsurf and Cursor
- ✅ Makefile integration
- ✅ MCP tool for programmatic access

**Success Metrics**:
- ✅ 100% test coverage for IDE config
- ✅ <5 min setup time for new users
- ✅ Zero manual JSON editing required

---

### Phase 3: Lifecycle Management (Week 4) ✅ COMPLETE
**Goal**: Optimize resource usage with selective server loading

**Deliverables**:
- ✅ Enable/disable server configuration
- ✅ CLI commands for lifecycle management
- ✅ REST API endpoints for programmatic control
- ✅ MCP tools for IDE integration
- ✅ Backward compatible config format
- ✅ Shell scripts validated with shellcheck
- ✅ JSON-based configuration with schema validation

**Success Metrics**:
- ✅ 60% faster startup with selective loading
- ✅ Zero breaking changes to existing configs
- ✅ <1s enable/disable operation time

**Completion Date**: Week 4

---

### Phase 4: Admin UI Enhancement (Week 5) ⏸️ DEFERRED
**Goal**: Visual management interface for server lifecycle

**Status**: Deferred to Phase 6 (CLI-first approach adopted)

**Rationale**:
- REST API backend complete and documented
- CLI tools provide immediate value for automation
- UI can be built later using existing API
- Reduces complexity and maintenance burden

**Deliverables Completed**:
- ✅ REST API endpoints (3 endpoints)
- ✅ MCP tools (4 tools)
- ✅ Comprehensive API documentation
- ✅ Integration examples (JS, Python, cURL)

**Deferred to Phase 6**:
- ⏸️ Server list with enable/disable toggles
- ⏸️ IDE config generator UI component
- ⏸️ Real-time status indicators
- ⏸️ Copy-to-clipboard functionality

---

### Phase 5: Command Simplification (Week 5) ✅ COMPLETE
**Goal**: Streamline common operations with unified CLI

**Deliverables**:
- ✅ Unified `mcp` CLI tool
- ✅ Interactive setup wizard
- ✅ Auto-detection of installed IDEs
- ✅ Server management commands
- ✅ Gateway control commands
- ✅ Comprehensive CLI documentation
- ✅ Makefile integration

**Success Metrics**:
- ✅ <2 min from install to first connection
- ✅ 80% reduction in command complexity
- ✅ Zero configuration for local development
- ✅ All commands tested and working

**Completion Date**: Week 5

---

### Phase 6: Feature Toggle & Test Coverage (Week 6) ✅ COMPLETE
**Goal**: Centralized feature management and comprehensive test coverage

**Deliverables**:
- ✅ YAML-based feature toggle system
- ✅ 17 fine-grained feature controls
- ✅ REST API for feature management
- ✅ Test coverage improvements (72.74% → 86.20%)
- ✅ 74 new tests added
- ✅ 100% coverage on critical modules

**Success Metrics**:
- ✅ ≥85% overall test coverage achieved
- ✅ Zero breaking changes
- ✅ Backward compatibility maintained

**Completion Date**: Week 6

---

### Phase 7: Next.js Admin UI (Week 7-8) 🚧 PLANNED
**Goal**: Build visual interface using existing REST API

**Deliverables**:
- [ ] Next.js application with Tailwind CSS
- [ ] Feature toggle management dashboard
- [ ] Virtual server lifecycle management UI
- [ ] Gateway status monitoring
- [ ] Real-time metrics visualization
- [ ] Responsive design with dark mode
- [ ] JWT authentication integration

**Estimated Completion**: Week 8

---

## 🔄 Development Workflow

### Daily Operations
1. **Feature Development**:
   ```bash
   git checkout -b feat/feature-name
   # Develop with TDD approach
   make lint test
   git commit -m "feat(scope): description"
   ```

2. **Testing**:
   ```bash
   make test                    # Run all tests
   make test-coverage           # With coverage report
   pytest tool_router/api/tests/ -v  # Specific module
   ```

3. **Quality Checks**:
   ```bash
   make lint                    # Ruff + shellcheck
   make format                  # Auto-format code
   pre-commit run --all-files   # Run all hooks
   ```

### Release Process
1. Update `CHANGELOG.md` with version and changes
2. Update `package.json` version (if applicable)
3. Commit: `chore: bump version to vX.Y.Z`
4. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Push: `git push origin main --tags`
6. Create GitHub release with changelog notes

### Documentation Updates
- **When**: Every feature, fix, or architectural change
- **What**: Update CHANGELOG.md, README.md, and this PROJECT_CONTEXT.md
- **How**: Include in the same PR as the code changes
- **Review**: Documentation changes reviewed alongside code

---

## 📚 Key Documentation

### For Operators
- **AI Router Guide**: `docs/operations/AI_ROUTER_GUIDE.md`
  - Configuration options
  - Monitoring and troubleshooting
  - Performance tuning
  - Best practices

### For Developers
- **README.md**: Quick start and setup
- **CHANGELOG.md**: Version history and changes
- **Architecture Docs**: `docs/architecture/`
- **Development Guides**: `docs/development/`

### For Users
- **Setup Guides**: `docs/setup/`
- **Configuration**: `docs/configuration/`
- **Migration Guides**: `docs/migration/`

---

## 🎓 Lessons Learned

### What Worked Well
1. **TDD Approach**: Writing tests first ensured high coverage (86.20%) and caught bugs early
2. **CLI-First**: Command-line tools provided immediate value before UI work
3. **Pragmatic Decisions**: Enhancing existing systems faster than rebuilding
4. **Incremental Delivery**: Small, focused sprints maintained momentum
5. **Backward Compatibility**: Optional config flags prevented breaking changes
6. **Bash Best Practices**: Using MCP tools for documentation improved script quality
7. **Feature Toggles**: Runtime control without code changes improved flexibility
8. **Unified CLI**: Single entry point (`mcp`) simplified user experience
9. **Comprehensive Testing**: 74 new tests added in Sprint 7 solidified quality
10. **JSON Configuration**: Structured config with schema validation improved reliability

### What to Improve
1. **Documentation Timing**: Update docs during development, not after
2. **Integration Testing**: Add more end-to-end tests for complex flows
3. **Performance Monitoring**: Implement metrics collection earlier
4. **User Feedback**: Gather feedback from real users sooner

### Technical Debt
1. **Legacy Server Module**: Old `server.py` still exists alongside new `core/server.py`
2. **Dual Gateway Clients**: Both `gateway_client.py` and `gateway/client.py` exist
3. **Config Complexity**: Multiple config sources (env vars, YAML, defaults)
4. **Type Hints**: Not all functions have complete type annotations
5. **Admin UI**: Planned but not yet implemented (Phase 7)

---

## 🔐 Security Considerations

### Current Measures
- ✅ JWT authentication for remote connections
- ✅ Environment variables for secrets
- ✅ Pre-commit secrets scanning
- ✅ Input validation on all APIs
- ✅ No hardcoded credentials

### Planned Improvements
- [ ] Rate limiting on API endpoints
- [ ] Audit logging for all operations
- [ ] RBAC for multi-user scenarios
- [ ] Encrypted configuration storage
- [ ] Security scanning in CI/CD

---

## 📞 Support & Contact

### Getting Help
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Documentation**: Check `docs/` directory first

### Contributing
- Follow Angular commit conventions
- Maintain ≥85% test coverage
- Update documentation with changes
- Run `make lint test` before committing

---

## 📝 Appendix

### Environment Variables Reference
```bash
# AI Router Configuration
ROUTER_AI_ENABLED=true
ROUTER_AI_MODEL=llama3.2:3b
ROUTER_AI_ENDPOINT=http://ollama:11434
ROUTER_AI_TIMEOUT_MS=5000
ROUTER_AI_MIN_CONFIDENCE=0.3
ROUTER_AI_WEIGHT=0.7

# Ollama Configuration
OLLAMA_KEEP_ALIVE=24h

# Gateway Configuration
GATEWAY_URL=http://localhost:4444
JWT_TOKEN=<optional-for-remote>
```

### Makefile Commands Reference
```bash
# Development
make start              # Start all services
make stop               # Stop all services
make register           # Register virtual servers
make lint               # Run linting
make test               # Run tests
make format             # Format code

# IDE Configuration
make ide-config IDE=windsurf SERVER=my-server
make ide-windsurf SERVER=cursor-router
make ide-cursor SERVER=test TOKEN=jwt-token

# Server Lifecycle
make enable-server SERVER=cursor-default
make disable-server SERVER=cursor-git
make list-enabled
```

### File Structure
```
mcp-gateway/
├── tool_router/              # Python tool router (FastMCP)
│   ├── ai/                   # AI selector module (Ollama integration)
│   │   ├── tests/            # AI selector tests
│   │   ├── prompts.py        # AI prompts for tool selection
│   │   └── selector.py       # AIToolSelector class
│   ├── api/                  # API endpoints
│   │   ├── tests/            # API tests
│   │   ├── features.py       # Feature toggle API
│   │   ├── health.py         # Health check API
│   │   ├── ide_config.py     # IDE config generator API
│   │   ├── lifecycle.py      # Server lifecycle API
│   │   ├── metrics.py        # Metrics API
│   │   └── rest.py           # REST API handlers
│   ├── core/                 # Core logic
│   │   ├── tests/            # Core tests
│   │   ├── config.py         # Configuration management
│   │   ├── features.py       # Feature toggle system
│   │   └── server.py         # Main MCP server (new)
│   ├── gateway/              # Gateway client (new)
│   │   └── client.py         # HTTPGatewayClient class
│   ├── scoring/              # Scoring algorithms
│   │   └── matcher.py        # Keyword and hybrid scoring
│   ├── observability/        # Observability module
│   │   ├── logger.py         # Logging setup
│   │   └── metrics.py        # Metrics collection
│   ├── args/                 # Argument builder
│   │   └── builder.py        # Tool argument construction
│   ├── __main__.py           # Entry point
│   ├── server.py             # Legacy server (to be removed)
│   └── gateway_client.py     # Legacy client (to be removed)
├── scripts/                  # Automation scripts
│   ├── completions/          # Shell completions
│   │   ├── mcp.bash          # Bash completion
│   │   ├── mcp.fish          # Fish completion
│   │   └── mcp.zsh           # Zsh completion
│   ├── cursor/               # Cursor-specific scripts
│   ├── gateway/              # Gateway management
│   ├── ide/                  # IDE configuration tools
│   ├── utils/                # Utility scripts
│   │   └── ensure-jwt.sh     # JWT generation helper
│   └── mcp                   # Unified CLI tool
├── config/                   # Configuration files
│   ├── features.yaml         # Feature toggle configuration
│   ├── gateways.txt          # Gateway definitions
│   ├── prompts.txt           # Prompt definitions
│   ├── resources.txt         # Resource definitions
│   ├── virtual-servers.json  # Virtual server configs
│   └── virtual-servers.schema.json  # JSON schema
├── docs/                     # Documentation
│   ├── architecture/         # Architecture docs
│   ├── cli/                  # CLI documentation
│   ├── configuration/        # Configuration guides
│   └── operations/           # Operational guides
├── web-admin/                # Next.js admin UI (planned)
├── Makefile                  # Automation commands
├── docker-compose.yml        # Service orchestration
├── pyproject.toml            # Python project config
├── CHANGELOG.md              # Version history
├── README.md                 # Quick start guide
└── PROJECT_CONTEXT.md        # This file
```

---

**Document Maintenance**: This file should be updated with every major feature, architectural change, or strategic decision. Keep it as the single source of truth for project context.
