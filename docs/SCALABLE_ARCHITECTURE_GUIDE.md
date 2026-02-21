# Scalable Architecture Guide

**Version:** 1.0.0
**Updated:** 2025-02-17
**Purpose**: Complete guide for the scalable MCP Gateway architecture with deployment instructions

## 🎯 Overview

The Forge MCP Gateway has been transformed from a monolithic Docker Compose setup with 20+ manually managed services to a dynamic, scalable architecture with only 5 core services. This new approach provides better resource utilization, simplified maintenance, and serverless-like behavior.

This guide provides both the architectural overview and step-by-step deployment instructions for the scalable MCP Gateway architecture with dynamic service management, serverless-like efficiency, and comprehensive monitoring capabilities.

## Architecture Components

### Core Services (5 total)

1. **Gateway** (`forge-mcpgateway`)
   - Main Context Forge instance
   - Handles MCP protocol routing
   - Port: 4444
   - Resources: 0.5 CPU, 512MB memory

2. **Service Manager** (`forge-service-manager`)
   - Dynamic service lifecycle management
   - On-demand service start/stop
   - Auto-sleep/wake capabilities
   - Port: 9000
   - Resources: 0.5 CPU, 512MB memory

3. **Tool Router** (`forge-mcp-gateway-tool-router`)
   - Intelligent routing and AI-powered tool selection
   - Ollama integration for smart routing
   - Port: 8030
   - Resources: 0.5 CPU, 512MB memory

4. **Admin UI** (`forge-mcp-gateway-ui`)
   - Web interface for service management
   - Real-time monitoring and control
   - Port: 8026
   - Resources: 0.5 CPU, 512MB memory

5. **Translate Service** (`forge-translate`)
   - Core translate service for dynamic containers
   - Supports SSE and HTTP protocols
   - Port: 8000
   - Resources: 0.25 CPU, 128MB memory

### Dynamic Services (20+ available)

All other MCP services are now managed dynamically by the service manager:

- **AI Services**: sequential-thinking
- **Browser Automation**: chrome-devtools, playwright, puppeteer, browser-tools
- **File System**: filesystem (auto-started)
- **Development Tools**: github, snyk, git-mcp, fetch
- **Database**: postgres, mongodb, sqlite
- **Memory**: memory (auto-started)
- **Search**: tavily
- **UI Tools**: magicuidesign-mcp, reactbits
- **Desktop**: desktop-commander

## Configuration Files

### `config/services.yml`
Defines all available MCP services with their configurations:

```yaml
services:
  sequential-thinking:
    image: forge-mcp-gateway-translate:latest
    command: ["python3", "-m", "forge.translate", "--stdio", "npx -y @modelcontextprotocol/server-sequential-thinking", "--expose-sse", "--port", "8013", "--host", "0.0.0.0"]
    port: 8013
    resources:
      memory: "256MB"
      cpu: "0.25"
    auto_start: false
    sleep_policy:
      enabled: true
      idle_timeout: 300
```

### `config/scaling-policies.yml`
Defines how services should be scaled based on demand:

```yaml
policies:
  default:
    min_instances: 0
    max_instances: 1
    idle_timeout: 300
    target_cpu_utilization: 0.7

service_policies:
  filesystem: high-demand  # Always available
  memory: high-demand     # Always available
  chrome-devtools: browser-automation  # Conservative scaling
```

### `config/gateways.txt`
Gateway registration configuration (unchanged):

```
sequential-thinking|http://sequential-thinking:8013/sse|SSE
filesystem|http://filesystem:8021/sse|SSE
github|http://github:8025/sse|SSE
```

## 🚀 Deployment Guide

### 📋 Prerequisites

#### System Requirements
- **Docker**: 20.10+ with Docker Compose v2.0+
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: Minimum 20GB free disk space
- **Network**: Internet access for container image downloads
- **OS**: Linux, macOS, or Windows with WSL2

#### Software Dependencies
```bash
# Required tools
docker --version
docker-compose --version
curl --version
jq --version  # For JSON parsing in scripts
```

#### Environment Setup
```bash
# Clone repository
git clone https://github.com/LucasSantana-Desenvolvimento/mcp-gateway.git
cd mcp-gateway

# Create necessary directories
mkdir -p data config logs test-results
```

### Quick Start Deployment

#### 1. Environment Configuration
```bash
# Copy environment template
cp .env.example .env.development

# Edit environment variables
nano .env.development
```

**Key Environment Variables:**
```bash
# Core Configuration
GATEWAY_PORT=4444
FORGE_SERVICE_MANAGER_PORT=9000
FORGE_TOOL_ROUTER_PORT=8030
FORGE_UI_PORT=3000

# Database Configuration
DATABASE_URL=sqlite:////data/mcp.db

# Logging Configuration
FORGE_LOG_LEVEL=info

# Scalable Architecture
FORGE_ENABLE_DYNAMIC_SERVICES=true
FORGE_ENABLE_SERVICE_DISCOVERY=true
FORGE_ENABLE_AUTO_SCALING=true
FORGE_ENABLE_SLEEP_POLICIES=true
FORGE_ENABLE_SERVERLESS_MODE=true
```

#### 2. Deploy Scalable Architecture
```bash
# Deploy using the start script
./start.sh

# Or manually with Docker Compose
docker-compose up -d
```

#### 3. Verify Deployment
```bash
# Check service status
docker-compose ps

# Check service manager API
curl http://localhost:9000/services

# View logs
docker-compose logs -f
```

### 🔧 Advanced Configuration

#### Service Configuration

**Dynamic Services (config/services.yml)**
```yaml
services:
  filesystem:
    image: forge-mcp-gateway-translate:latest
    port: 8021
    resources:
      memory: "256MB"
      cpu: "0.25"
    auto_start: true
    sleep_policy:
      enabled: true
      idle_timeout: 600  # 10 minutes
      min_sleep_time: 120  # 2 minutes
      memory_reservation: "128MB"
      priority: "high"
    health_check:
      path: "/health"
      interval: 30
      timeout: 10

  chrome-devtools:
    image: forge-mcp-gateway-translate:latest
    port: 8014
    resources:
      memory: "512MB"
      cpu: "0.5"
    auto_start: false
    sleep_policy:
      enabled: true
      idle_timeout: 180  # 3 minutes
      min_sleep_time: 60   # 1 minute
      memory_reservation: "256MB"
      priority: "normal"
```

#### Sleep Policy Configuration
```yaml
# Sleep policy priorities
priority_levels:
  high:    # Never sleep (core services)
    - gateway
    - service-manager
    - tool-router

  normal:  # Sleep after 10 minutes
    - filesystem
    - memory
    - database

  low:     # Sleep after 3 minutes
    - chrome-devtools
    - browser-automation
    - ai-services
```

### 📊 Monitoring and Management

#### Service Management API
```bash
# List all services
curl http://localhost:9000/services

# Get service status
curl http://localhost:9000/services/sequential-thinking

# Start a service
curl -X POST http://localhost:9000/services/sequential-thinking/start

# Stop a service
curl -X POST http://localhost:9000/services/sequential-thinking/stop

# Put service to sleep
curl -X POST http://localhost:9000/services/sequential-thinking/sleep

# Wake service from sleep
curl -X POST http://localhost:9000/services/sequential-thinking/wake

# Health check
curl http://localhost:9000/health
```

#### Real-time Monitoring
```bash
# Start monitoring dashboard
./scripts/monitoring-dashboard.sh

# Monitor resource usage
docker stats --no-stream

# Check service logs
docker-compose logs -f service-manager
```

## Key Features

### 1. On-Demand Scaling
Services start only when needed:
- Manual start via API: `POST /services/{name}/start`
- Automatic start based on demand
- Configurable auto-start for critical services

### 2. Serverless-Like Behavior
- **Auto-Sleep**: Services pause after inactivity
- **Fast Wake**: Sub-200ms wake times for sleeping services
- **Resource Optimization**: Reduced memory usage during sleep

### 3. Configuration-Driven Management
- Add/remove services via `config/services.yml`
- Adjust scaling via `config/scaling-policies.yml`
- No Docker Compose changes required

### 4. Intelligent Routing
- AI-powered tool selection with Ollama
- Load balancing across service instances
- Health check integration

## API Endpoints

### Service Manager API

#### List All Services
```bash
curl http://localhost:9000/services
```

#### Get Service Status
```bash
curl http://localhost:9000/services/sequential-thinking
```

#### Start a Service
```bash
curl -X POST http://localhost:9000/services/sequential-thinking/start
```

#### Stop a Service
```bash
curl -X POST http://localhost:9000/services/sequential-thinking/stop
```

#### Put Service to Sleep
```bash
curl -X POST http://localhost:9000/services/sequential-thinking/sleep
```

#### Wake Service from Sleep
```bash
curl -X POST http://localhost:9000/services/sequential-thinking/wake
```

#### Health Check
```bash
curl http://localhost:9000/health
```

### Gateway API

#### Health Check
```bash
curl http://localhost:4444/health
```

#### Service Discovery
```bash
curl http://localhost:4444/services
```

## Migration Guide

### Prerequisites
- Docker and Docker Compose installed
- Existing forge-mcp-gateway setup

### Migration Steps

1. **Backup Current Setup**
   ```bash
   cp docker-compose.yml docker-compose.yml.backup
   ```

2. **Run Migration Script**
   ```bash
   ./scripts/migration/migrate-to-scalable-architecture.sh
   ```

3. **Verify Services**
   ```bash
   docker-compose ps
   curl http://localhost:9000/services
   ```

4. **Test Dynamic Services**
   ```bash
   # Start sequential-thinking service
   curl -X POST http://localhost:9000/services/sequential-thinking/start

   # Check status
   curl http://localhost:9000/services/sequential-thinking
   ```

### Manual Migration (Alternative)

If the migration script fails, you can migrate manually:

1. **Stop Current Services**
   ```bash
   docker-compose down
   ```

2. **Update docker-compose.yml**
   - Replace with the new streamlined version
   - Only 5 core services should remain

3. **Build New Images**
   ```bash
   docker-compose build
   ```

4. **Start Services**
   ```bash
   docker-compose up -d
   ```

## Benefits

### Resource Optimization
- **Memory Usage**: Reduced from ~8GB to ~2GB at idle
- **CPU Usage**: Only active services consume CPU
- **Startup Time**: Faster initial startup (5 services vs 20+)

### Maintenance Simplification
- **Docker Compose**: 5 services vs 20+ to manage
- **Configuration**: YAML files vs manual service definitions
- **Updates**: Add services via config, not Docker Compose

### Scalability Improvements
- **On-Demand**: Services start only when needed
- **Auto-Sleep**: Automatic resource optimization
- **Flexible Scaling**: Configurable policies per service

### Development Experience
- **Faster Iteration**: Quick service start/stop
- **Better Debugging**: Isolated service management
- **Real-time Monitoring**: Service status API

## Troubleshooting

### Common Issues

#### Services Not Starting
1. Check service manager logs: `docker-compose logs service-manager`
2. Verify configuration files: `python3 -c "import yaml; yaml.safe_load(open('config/services.yml'))"`
3. Check Docker socket permissions

#### Health Check Failures
1. Wait longer for services to start (up to 60 seconds)
2. Check port conflicts: `netstat -tulpn | grep :8000`
3. Verify environment variables in `.env`

#### Memory Issues
1. Check resource limits in `config/services.yml`
2. Monitor with: `docker stats`
3. Adjust scaling policies in `config/scaling-policies.yml`

### Debug Commands

#### Check All Service Status
```bash
curl -s http://localhost:9000/services | python3 -m json.tool
```

#### Monitor Service Manager Logs
```bash
docker-compose logs -f service-manager
```

#### Check Resource Usage
```bash
docker stats --no-stream
```

#### Test Service Lifecycle
```bash
# Start
curl -X POST http://localhost:9000/services/sequential-thinking/start

# Wait a bit, then sleep
curl -X POST http://localhost:9000/services/sequential-thinking/sleep

# Wake
curl -X POST http://localhost:9000/services/sequential-thinking/wake

# Stop
curl -X POST http://localhost:9000/services/sequential-thinking/stop
```

## Performance Tuning

### Service Manager Settings
Edit `config/scaling-policies.yml`:

```yaml
global_settings:
  scaling_interval: 30        # Check every 30 seconds
  max_concurrent_services: 10 # Max 10 services running
  system_limits:
    max_memory_gb: 8         # System memory limit
    max_cpu_cores: 4         # System CPU limit
```

### Individual Service Tuning
Edit `config/services.yml`:

```yaml
services:
  chrome-devtools:
    resources:
      memory: "512MB"        # Increase for heavy services
      cpu: "0.5"
    sleep_policy:
      idle_timeout: 180      # Shorter for browser services
      priority: "high"        # Faster wake for important services
```

### Docker Compose Optimization
Edit resource limits in `docker-compose.yml`:

```yaml
services:
  service-manager:
    deploy:
      resources:
        limits:
          cpus: '1.0'          # Increase for heavy workloads
          memory: 1G
```

## Monitoring

### Built-in Monitoring
- **Service Manager API**: `/health`, `/services`
- **Gateway API**: `/health`, `/services`
- **Docker Stats**: `docker stats`

### External Monitoring
- **Prometheus**: Metrics available on port 9000
- **Grafana**: Service status dashboards
- **Alertmanager**: Service failure alerts

### Log Management
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f service-manager

# Last 100 lines
docker-compose logs --tail=100 service-manager
```

## Security Considerations

### Docker Socket Access
The service manager needs Docker socket access for dynamic container management:
- **Risk**: Container escape possibility
- **Mitigation**: Service manager runs with minimal privileges
- **Recommendation**: Run in isolated environment if needed

### Service Isolation
- Each MCP service runs in isolated container
- Network segmentation via Docker networks
- Resource limits prevent resource exhaustion

### API Security
- Service manager API on localhost only
- No authentication required (internal use)
- Consider adding auth for external access

## Future Enhancements

### Planned Features
1. **Multi-Host Support**: Scale across multiple Docker hosts
2. **Kubernetes Integration**: Native K8s deployment
3. **Advanced Metrics**: Detailed performance analytics
4. **Service Mesh**: Istio/Linkerd integration
5. **Auto-Scaling**: CPU/memory-based scaling

### Extension Points
- Custom service managers
- Alternative service discovery
- Pluggable scaling policies
- Custom health checks

## Support

### Documentation
- **Architecture Overview**: `docs/architecture/OVERVIEW.md`
- **Service Manager Guide**: `docs/architecture/SERVICE_MANAGER_GUIDE.md`
- **Configuration Reference**: `docs/configuration/`

### Community
- **Issues**: Report via GitHub Issues
- **Discussions**: GitHub Discussions for questions
- **Contributions**: Pull Requests welcome

### Getting Help
1. Check this guide first
2. Review troubleshooting section
3. Check GitHub Issues
4. Create new issue with details

---

**Last Updated**: 2025-02-18
**Version**: 1.0.0
**Architecture**: Scalable Docker Compose with Dynamic Service Discovery
