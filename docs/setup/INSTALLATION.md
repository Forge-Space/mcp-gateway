# Installation & Setup

Complete installation guide for the MCP Gateway (Context Forge).

## Prerequisites

- **Docker** - Container runtime
- **Docker Compose V2** (`docker compose`) or V1 (`docker-compose`)
- **Git** - For cloning the repository

**Optional:**
- [Dev Container](https://code.visualstudio.com/docs/devcontainers/containers) for one-click lint/test
- Node.js 20+ (for local TypeScript client development)
- Python 3.11+ (for local tool-router development)

## Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/forge-mcp-gateway.git
cd forge-mcp-gateway
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set the required values:

```bash
# Required - Generate strong secrets (min 32 characters each)
JWT_SECRET_KEY=your-secret-key-here
AUTH_ENCRYPTION_SECRET=your-encryption-secret-here
PLATFORM_ADMIN_EMAIL=admin@example.com
PLATFORM_ADMIN_PASSWORD=your-secure-password
```

**Quick secret generation:**
```bash
make generate-secrets
```

### 3. Start the Gateway

```bash
make start
```

This will:
- Pull Docker images
- Start the gateway and all translate services
- Initialize the database
- Expose the Admin UI at http://localhost:4444/admin

### 4. Register Gateways

```bash
make register
```

This will:
- Register all configured MCP servers
- Create virtual servers
- Print connection URLs for your IDE

## Detailed Installation

### Environment Configuration

See [ENVIRONMENT_CONFIGURATION.md](ENVIRONMENT_CONFIGURATION.md) for detailed environment variable documentation.

**Minimal configuration:**
```env
HOST=0.0.0.0
PORT=4444
DATABASE_URL=sqlite:///./mcp.db
JWT_SECRET_KEY=<32+ character secret>
AUTH_ENCRYPTION_SECRET=<32+ character secret>
PLATFORM_ADMIN_EMAIL=admin@example.com
PLATFORM_ADMIN_PASSWORD=<secure password>
```

**Optional services:**
```env
# API Keys for specific services
TAVILY_API_KEY=your-tavily-key
SNYK_TOKEN=your-snyk-token
GITHUB_PERSONAL_ACCESS_TOKEN=your-github-token
```

### Docker Compose Profiles

Start specific services:

```bash
# Gateway only (no translate services)
make gateway-only

# Full stack (default)
make start

# With specific services
docker compose --profile gateway --profile sequential-thinking up -d
```

### Verify Installation

Check service status:
```bash
docker compose ps
```

Check gateway health:
```bash
curl http://localhost:4444/health
```

View logs:
```bash
docker compose logs gateway
docker compose logs -f  # Follow all logs
```

## IDE Setup

After installation, configure your IDE to connect to the gateway:

- **[Cursor/VS Code/Windsurf Setup](IDE_SETUP_GUIDE.md)**
- **[NPX Client Configuration](../../NPM_PACKAGE_README.md)**

## Troubleshooting

### Gateway won't start

1. Check Docker is running:
   ```bash
   docker ps
   ```

2. Check port 4444 is available:
   ```bash
   lsof -i :4444  # macOS/Linux
   netstat -ano | findstr :4444  # Windows
   ```

3. Check logs:
   ```bash
   docker compose logs gateway
   ```

### Database initialization fails

Remove the database and restart:
```bash
rm mcp.db
make start
```

### Services fail to connect

Wait for services to initialize (first run takes longer):
```bash
make register-wait  # Waits 30s before registering
```

## Next Steps

- **[Configure your IDE](IDE_SETUP_GUIDE.md)**
- **[Add MCP servers](../configuration/ADMIN_UI_MANUAL_REGISTRATION.md)**
- **[Learn about virtual servers](../architecture/VIRTUAL_SERVERS.md)**
- **[Explore the tool router](../architecture/TOOL_ROUTER_GUIDE.md)**

## Uninstallation

Stop and remove all containers:
```bash
make stop
docker compose down -v  # Remove volumes too
```

Remove data:
```bash
rm -rf data/ mcp.db
```
