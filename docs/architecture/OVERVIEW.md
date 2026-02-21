# Architecture Overview

High-level architecture of the MCP Gateway (Context Forge) system.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         IDE/Client                          │
│                    (Cursor, VS Code, etc.)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol (HTTP/SSE)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      MCP Gateway                            │
│                   (Context Forge)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Virtual Servers (Tool Collections)                  │  │
│  │  - cursor-default (all tools)                        │  │
│  │  - cursor-router (tool-router only)                  │  │
│  │  - custom servers (filtered tool sets)              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Gateway Registry                                     │  │
│  │  - Upstream MCP servers                              │  │
│  │  - Authentication & routing                          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌────▼────────┐
│   Remote     │  │   Local     │  │ Tool Router │
│   Gateways   │  │  Translate  │  │  (Dynamic)  │
│              │  │  Services   │  │             │
│ - Context7   │  │ - sequential│  │ Queries     │
│ - Prisma     │  │ - playwright│  │ gateway API │
│ - v0         │  │ - snyk      │  │ for tools   │
└──────────────┘  └─────────────┘  └─────────────┘
```

## Core Components

### 1. MCP Gateway (Context Forge)

**Purpose:** Central hub that aggregates multiple MCP servers into a single connection point.

**Key Features:**
- Single connection from IDE to gateway
- Multiple upstream MCP server connections
- Virtual server management (tool collections)
- Authentication & authorization (JWT-based)
- Admin UI for configuration
- SQLite database for persistence

**Technology:**
- IBM Context Forge (upstream)
- Docker containerized
- FastAPI backend
- SQLite database

### 2. Virtual Servers

**Purpose:** Organize tools into logical collections to stay under IDE tool limits (~60 tools).

**Types:**
- **cursor-default** - All available tools from all gateways
- **cursor-router** - Single entry point using tool-router
- **Custom servers** - User-defined tool subsets

**Benefits:**
- Avoid tool limit warnings
- Organize tools by use case
- Multiple connection points for different workflows

See [VIRTUAL_SERVERS.md](VIRTUAL_SERVERS.md) for details.

### 3. Tool Router

**Purpose:** Single entry point that dynamically queries the gateway API to find and execute the best tool for a task.

**How it works:**
1. Receives task description from IDE
2. Queries gateway API for all available tools
3. Scores tools based on task relevance
4. Executes the best matching tool
5. Returns results to IDE

**Benefits:**
- Only 1-2 tools exposed to IDE (no tool limit issues)
- Access to all gateway tools dynamically
- Intelligent tool selection
- Automatic argument building

See [TOOL_ROUTER_GUIDE.md](TOOL_ROUTER_GUIDE.md) for details.

### 4. Translate Services

**Purpose:** Convert stdio-based MCP servers to HTTP/SSE for gateway consumption.

**Architecture:**
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ MCP Server   │      │  Translate   │      │   Gateway    │
│  (stdio)     │─────▶│   Service    │─────▶│              │
│              │ stdio │  (Docker)    │ SSE  │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

**Examples:**
- sequential-thinking → http://sequential-thinking:8013/sse
- playwright → http://playwright:8015/sse
- snyk → http://snyk:8023/sse

### 5. TypeScript Client

**Purpose:** NPX-compatible MCP client for connecting IDEs to the gateway.

**Features:**
- Standard MCP server pattern (`npx @forge-mcp-gateway/client`)
- JWT authentication support
- Configurable timeouts and retries
- Works with any MCP-compatible IDE

**Usage:**
```json
{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx",
      "args": ["-y", "@forge-mcp-gateway/client", "--url=http://localhost:4444/servers/<UUID>/mcp"]
    }
  }
}
```

## Data Flow

### Tool Execution Flow

```
1. IDE sends tool call
   ↓
2. Gateway receives request
   ↓
3. Gateway authenticates JWT
   ↓
4. Gateway routes to virtual server
   ↓
5. Virtual server finds tool in registry
   ↓
6. Gateway forwards to upstream MCP server
   ↓
7. Upstream server executes tool
   ↓
8. Results flow back through gateway
   ↓
9. IDE receives response
```

### Tool Router Flow

```
1. IDE calls execute_task("search for React docs")
   ↓
2. Tool router queries gateway API for all tools
   ↓
3. Tool router scores tools by relevance
   ↓
4. Tool router picks best tool (e.g., tavily_search)
   ↓
5. Tool router builds arguments from task description
   ↓
6. Tool router calls gateway API to execute tool
   ↓
7. Gateway executes tavily_search
   ↓
8. Results return to IDE
```

## Authentication & Security

### JWT-Based Authentication

**Token Generation:**
```bash
make jwt  # Generates 7-day token
```

**Token Structure:**
```json
{
  "username": "admin@example.com",
  "sub": "admin@example.com",
  "iat": 1234567890,
  "exp": 1234567890,
  "iss": "mcpgateway",
  "aud": "mcpgateway-api"
}
```

**Security Features:**
- JWT secret key (32+ characters)
- Encryption secret for sensitive data
- Per-request authentication
- Token expiration (7 days default)
- HTTPS support for production

### Environment-Based Configuration

**Development:**
- `AUTH_REQUIRED=false` - Skip JWT for local testing
- `SECURE_COOKIES=false` - HTTP cookies allowed

**Production:**
- `AUTH_REQUIRED=true` - JWT required
- `SECURE_COOKIES=true` - HTTPS-only cookies
- Strong secrets (32+ characters)

## Deployment Patterns

### Local Development

```bash
make start        # Full stack
make gateway-only # Gateway only
make register     # Register gateways
```

### Docker Compose

```yaml
services:
  gateway:
    image: contextforge/gateway
    ports:
      - "4444:4444"
    environment:
      - JWT_SECRET_KEY
      - DATABASE_URL
```

### Production Considerations

- Use PostgreSQL instead of SQLite
- Enable HTTPS (reverse proxy)
- Set strong secrets
- Enable authentication
- Monitor with health checks
- Use Docker secrets for sensitive data

## Monorepo Structure

```
forge-mcp-gateway/
├── src/                    # TypeScript client source
├── build/                  # TypeScript client build
├── tool_router/           # Python tool router
│   ├── core/              # Configuration & server
│   ├── gateway/           # Gateway client
│   ├── tools/             # Tool execution
│   ├── scoring/           # Tool matching
│   └── tests/             # Unit & integration tests
├── scripts/               # Automation scripts
├── config/                # Gateway configurations
├── docs/                  # Documentation
└── docker-compose.yml     # Service orchestration
```

## Next Steps

- **[Virtual Servers](VIRTUAL_SERVERS.md)** - Organize tools
- **[Tool Router Guide](TOOL_ROUTER_GUIDE.md)** - Single entry point
- **[Development Guide](../development/DEVELOPMENT.md)** - Contributing
- **[Configuration](../configuration/MCP_STACK_CONFIGURATIONS.md)** - Stack setups
