# Enhanced Production Deployment Guide

This comprehensive guide covers the complete production deployment process for the Forge MCP Gateway, including security hardening, monitoring setup, and operational procedures.

## 🎯 Overview

The Forge MCP Gateway is a self-hosted aggregation gateway that consolidates multiple Model Context Protocol (MCP) servers into a single connection point. This guide ensures secure, scalable, and maintainable production deployments.

## 🚀 Quick Start

### Prerequisites

**System Requirements:**
- Docker 20.10+ and Docker Compose 2.0+
- At least 4GB RAM and 2 CPU cores (recommended: 8GB+ RAM, 4+ cores)
- 20GB+ available disk space
- Linux host (Ubuntu 20.04+, CentOS 8+, or similar)
- Domain name (optional, for SSL certificates)

**Software Requirements:**
- Git for version control
- OpenSSL for certificate generation
- curl for health checks
- Text editor (nano, vim, or VS Code)

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/LucasSantana-Dev/forge-mcp-gateway.git
cd forge-mcp-gateway

# Create production environment file
cp .env.example .env.production

# Set proper permissions
chmod 600 .env.production
```

### 2. Generate Secure Secrets

```bash
# Generate secure secrets (run this script)
make generate-secrets

# Or generate manually (minimum 32 characters each)
JWT_SECRET=$(openssl rand -base64 32 | tr -d '/+=' | tr -d '\n')
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | tr -d '\n')
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | tr -d '\n')
GRAFANA_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | tr -d '\n')

# Add to .env.production
echo "JWT_SECRET=$JWT_SECRET" >> .env.production
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env.production
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env.production
echo "GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> .env.production
```

### 3. Configure Production Environment

Edit `.env.production` with your production values:

```bash
# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
# Generate secure values using: make generate-secrets
JWT_SECRET={{JWT_SECRET}}
POSTGRES_PASSWORD={{POSTGRES_PASSWORD}}
REDIS_PASSWORD={{REDIS_PASSWORD}}
GRAFANA_PASSWORD={{GRAFANA_PASSWORD}}

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
POSTGRES_DB=forge_mcp_prod
POSTGRES_USER=forge_user
DATABASE_URL=sqlite:////data/mcp.db

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=4444
FORGE_ENABLE_DYNAMIC_SERVICES=true
FORGE_SERVICE_MANAGER_URL=http://service-manager:9000
SKIP_MIGRATIONS=true

# =============================================================================
# PRODUCTION SETTINGS
# =============================================================================
NODE_ENV=production
LOG_LEVEL=warn
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# =============================================================================
# MONITORING CONFIGURATION
# =============================================================================
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
ALERTING_ENABLED=true
METRICS_RETENTION=30d
LOG_RETENTION=7d

# =============================================================================
# PERFORMANCE CONFIGURATION
# =============================================================================
MAX_WORKERS=4
WORKER_TIMEOUT=30000
CONNECTION_TIMEOUT=10000
RATE_LIMIT_PER_MINUTE=100
```

## 📋 Detailed Deployment Process

### Phase 1: Pre-deployment Preparation

#### 1.1 System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application user (security best practice)
sudo useradd -m -s /bin/bash forge-user
sudo usermod -aG docker forge-user
```

#### 1.2 Directory Structure Setup

```bash
# Create production directories
sudo mkdir -p /opt/forge-mcp-gateway
sudo chown forge-user:forge-user /opt/forge-mcp-gateway
sudo chmod 755 /opt/forge-mcp-gateway

# Copy application files
sudo -u forge-user cp -r /path/to/forge-mcp-gateway/* /opt/forge-mcp-gateway/
cd /opt/forge-mcp-gateway

# Set proper permissions
sudo chmod 600 .env.production
sudo chmod +x scripts/*.sh
sudo chmod +x docker-compose*.yml
```

#### 1.3 SSL Certificate Setup (Optional but Recommended)

```bash
# Create SSL directory
sudo mkdir -p /opt/forge-mcp-gateway/ssl
sudo chown forge-user:forge-user /opt/forge-mcp-gateway/ssl

# Generate self-signed certificate (for testing)
sudo -u forge-user openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout /opt/forge-mcp-gateway/ssl/server.key \
    -out /opt/forge-mcp-gateway/ssl/server.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# For production, use Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

### Phase 2: Security Hardening

#### 2.1 Docker Security Configuration

```bash
# Create production Docker Compose file
cat > docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  gateway:
    image: ghcr.io/ibm/mcp-context-forge:1.0.0-BETA-2
    container_name: forge-mcpgateway
    restart: unless-stopped
    entrypoint: ["/app/docker/entrypoint.sh"]
    ports:
      - "${GATEWAY_PORT:-4444}:4444"
    env_file:
      - .env.production
    environment:
      HOST: ${GATEWAY_HOST:-0.0.0.0}
      PORT: ${GATEWAY_PORT:-4444}
      DATABASE_URL: ${DATABASE_URL:-sqlite:////data/mcp.db}
      FORGE_ENABLE_DYNAMIC_SERVICES: true
      FORGE_SERVICE_MANAGER_URL: http://service-manager:9000
      SKIP_MIGRATIONS: true
    volumes:
      - ./data:/data
      - ./docker/entrypoint.sh:/app/docker/entrypoint.sh:ro
      - ./docker/minimal_gateway.py:/app/docker/minimal_gateway.py:ro
      - ./ssl:/ssl:ro
    depends_on:
      - service-manager
      - tool-router
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
          pids: 50
        reservations:
          cpus: "0.1"
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4444/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    security_opt:
      - no-new-privileges:true
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m

  service-manager:
    build:
      context: ./service-manager
      dockerfile: Dockerfile
    container_name: forge-service-manager
    restart: unless-stopped
    ports:
      - "${FORGE_SERVICE_MANAGER_PORT:-9000}:9000"
    volumes:
      - ./config:/config:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/data
    environment:
      - CONFIG_PATH=/config
      - LOG_LEVEL=${FORGE_SERVICE_MANAGER_LOG_LEVEL:-info}
      - DATA_PATH=/data
      - DOCKER_HOST=unix:///var/run/docker.sock
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "0.25"
          memory: 256M
          pids: 30
        reservations:
          cpus: "0.05"
          memory: 64M
    security_opt:
      - no-new-privileges:true
    user: "1001:1001"
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=50m

  tool-router:
    build:
      context: ./tool-router
      dockerfile: Dockerfile.tool-router
    container_name: forge-tool-router
    restart: unless-stopped
    ports:
      - "${TOOL_ROUTER_PORT:-8001}:8001"
    volumes:
      - ./config:/config:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/data
    environment:
      - CONFIG_PATH=/config
      - LOG_LEVEL=${TOOL_ROUTER_LOG_LEVEL:-info}
      - DATA_PATH=/data
      - DOCKER_HOST=unix:///var/run/docker.sock
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "0.25"
          memory: 256M
          pids: 30
        reservations:
          cpus: "0.05"
          memory: 64M
    security_opt:
      - no-new-privileges:true
    user: "1002:1002"
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=50m

networks:
  forge-mcp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.host_binding_ipv4: "172.20.0.1"

volumes:
  forge-mcp-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/forge-mcp-gateway/data

  forge-mcp-config:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/forge-mcp-gateway/config

  forge-mcp-logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/forge-mcp-gateway/logs
EOF
```

#### 2.2 Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 4444/tcp
sudo ufw allow 9000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 3001/tcp

# Allow Docker communication
sudo ufw allow from 172.20.0.0/16
```

### Phase 3: Deployment Execution

#### 3.1 Automated Deployment

```bash
# Make deployment script executable
chmod +x scripts/deploy-production.sh

# Run full deployment with validation
./scripts/deploy-production.sh full
```

#### 3.2 Manual Deployment Steps

```bash
# Step 1: Pull latest images
docker-compose -f docker-compose.production.yml pull

# Step 2: Build custom images
docker-compose -f docker-compose.production.yml build

# Step 3: Start services
docker-compose -f docker-compose.production.yml up -d

# Step 4: Wait for health checks
sleep 60

# Step 5: Verify deployment
curl -f http://localhost:4444/health
curl -f http://localhost:9000/health
curl -f http://localhost:8001/health
```

### Phase 4: Post-deployment Verification

#### 4.1 Health Checks

```bash
# Comprehensive health verification
./scripts/deploy-production.sh health

# Individual service checks
curl -s http://localhost:4444/health | jq .
curl -s http://localhost:9000/health | jq .
curl -s http://localhost:8001/health | jq .
```

#### 4.2 Service Validation

```bash
# Test gateway functionality
curl -X POST http://localhost:4444/tools \
  -H "Content-Type: application/json" \
  -d '{"task": "test query", "context": "testing"}'

# Verify service manager
curl -s http://localhost:9000/services | jq .

# Check tool router
curl -s http://localhost:8001/status | jq .
```

#### 4.3 Load Testing

```bash
# Basic load test
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://localhost:4444/health &
  sleep 0.1
done

# Wait for completion
wait
```

## 🔧 Service Management

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Start specific service
docker-compose -f docker-compose.production.yml up -d gateway

# Scale services
docker-compose -f docker-compose.production.yml up -d --scale gateway=2
```

### Stopping Services

```bash
# Graceful shutdown
docker-compose -f docker-compose.production.yml down

# Force stop (emergency)
docker-compose -f docker-compose.production.yml down --remove-orphans
```

### Log Management

```bash
# View all logs
docker-compose -f docker-compose.production.yml logs -f

# Service-specific logs
docker-compose -f docker-compose.production.yml logs -f gateway
docker-compose -f docker-compose.production.yml logs -f service-manager

# Log rotation (setup in docker-compose.yml)
docker-compose -f docker-compose.production.yml logs --tail=100 gateway
```

### Backup Procedures

```bash
# Create backup script
cat > scripts/backup-production.sh << 'EOF'
#!/bin/bash

set -euo pipefail

BACKUP_DIR="/opt/forge-mcp-gateway/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/forge-mcp-gateway-backup-$TIMESTAMP.tar.gz"

echo "Creating backup: $BACKUP_FILE"

# Create backup
docker run --rm \
  -v /opt/forge-mcp-gateway:/source:ro \
  -v $BACKUP_DIR:/backup \
  alpine:latest \
  tar czf /backup/forge-mcp-gateway-backup-$TIMESTAMP.tar.gz \
  -C /source data config .env.production

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x scripts/backup-production.sh
```

## 📊 Monitoring and Observability

### Health Check Endpoints

All services expose health check endpoints:

| Service | Endpoint | Description |
|---------|----------|-------------|
| Gateway | `GET /health` | Overall system health |
| Service Manager | `GET /health` | Service management health |
| Tool Router | `GET /health` | Tool routing health |

### Monitoring Stack

#### Prometheus Metrics

```yaml
# prometheus.yml configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'forge-mcp-gateway'
    static_configs:
      - targets:
        - 'localhost:4444'
        - 'localhost:9000'
        - 'localhost:8001'
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: job
        replacement: forge-mcp-gateway
```

#### Grafana Dashboard

```bash
# Import dashboard configuration
curl -X POST http://{{GRAFANA_ADMIN_USER}}:{{GRAFANA_ADMIN_PASSWORD}}@localhost:3001/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana-dashboard.json
```

### Alerting Rules

```yaml
# alerting.yml configuration
groups:
  - name: forge-mcp-gateway
    rules:
      - alert: GatewayDown
        expr: up{job="forge-mcp-gateway"} == 0
        for: 1m
        labels:
          severity: critical
          service: gateway
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          service: gateway
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[5m]) / (5 * 60) > 0.8
        for: 5m
        labels:
          severity: warning
          service: gateway
```

## 🔒 Security Hardening

### Container Security

- **Non-root Users**: All containers run as dedicated non-root users
- **Minimal Base Images**: Alpine Linux variants with essential packages only
- **Read-only Filesystems**: Critical directories mounted read-only where possible
- **Tmpfs for Temp**: Temporary directories mounted with noexec and nosuid
- **Resource Limits**: CPU, memory, and PID limits enforced

### Network Security

- **Isolated Network**: Services communicate via internal Docker network
- **Firewall Rules**: Only necessary ports exposed to host
- **SSL/TLS**: HTTPS termination at load balancer level
- **Authentication**: JWT-based authentication for all API endpoints

### Application Security

- **Environment Variables**: Sensitive data stored in environment files with restricted permissions
- **Input Validation**: All inputs validated and sanitized
- **Rate Limiting**: API endpoints protected with rate limiting
- **Audit Logging**: Security events logged with structured format

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs gateway

# Check configuration
docker-compose -f docker-compose.production.yml config

# Validate environment file
docker-compose -f docker-compose.production.yml config --quiet
```

#### Health Check Failures

```bash
# Test individual endpoints
curl -v http://localhost:4444/health
curl -v http://localhost:9000/health
curl -v http://localhost:8001/health

# Check container status
docker ps -a
docker inspect forge-mcpgateway
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check system resources
htop
free -h
df -h

# Analyze logs for errors
docker-compose logs gateway | grep ERROR
```

#### Database Issues

```bash
# Check database file
ls -la /opt/forge-mcp-gateway/data/

# Verify database permissions
ls -la /opt/forge-mcp-gateway/data/mcp.db

# Test database connectivity
sqlite3 /opt/forge-mcp-gateway/data/mcp.db ".tables"
```

### Recovery Procedures

#### Service Recovery

```bash
# Restart all services
docker-compose -f docker-compose.production.yml restart

# Force recreation
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --force-recreate

# Restore from backup
tar xzf /opt/forge-mcp-gateway/backups/forge-mcp-gateway-backup-*.tar.gz -C /opt/forge-mcp-gateway/
```

#### Configuration Recovery

```bash
# Reset configuration from template
cp .env.example .env.production
chmod 600 .env.production

# Regenerate secrets
make generate-secrets

# Redeploy
./scripts/deploy-production.sh deploy
```

## 📈 Scaling and Performance

### Horizontal Scaling

```bash
# Scale gateway service
docker-compose -f docker-compose.production.yml up -d --scale gateway=3

# Scale all services
docker-compose -f docker-compose.production.yml up -d \
  --scale gateway=2 \
  --scale service-manager=2 \
  --scale tool-router=2
```

### Resource Optimization

#### Memory Optimization

```yaml
# In docker-compose.production.yml
services:
  gateway:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
      restart_policy: unless-stopped
```

#### CPU Optimization

```yaml
# In docker-compose.production.yml
services:
  gateway:
    deploy:
      resources:
        limits:
          cpus: "0.5"
        reservations:
          cpus: "0.1"
      restart_policy: unless-stopped
```

### Performance Monitoring

```bash
# Monitor response times
curl -w "time_total=%{time_total}\n" http://localhost:4444/health

# Monitor resource usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Monitor database performance
sqlite3 /opt/forge-mcp-gateway/data/mcp.db ".schema" | head -10
```

## 🔄 Maintenance Procedures

### Regular Maintenance Tasks

#### Daily

- Check service health status
- Review logs for errors
- Monitor resource usage
- Verify backup completion

#### Weekly

- Update container images
- Review security patches
- Clean up old logs
- Test backup restoration

#### Monthly

- Update application code
- Review and rotate secrets
- Performance tuning
- Capacity planning

### Automated Maintenance

```bash
# Create maintenance script
cat > scripts/maintenance.sh << 'EOF'
#!/bin/bash

set -euo pipefail

echo "Starting maintenance procedures..."

# Clean old logs
find /opt/forge-mcp-gateway/logs -name "*.log" -mtime +7 -delete

# Clean old backups
find /opt/forge-mcp-gateway/backups -name "*.tar.gz" -mtime +30 -delete

# Update containers
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml build --no-cache

# Restart services
docker-compose -f docker-compose.production.yml restart

echo "Maintenance completed"
EOF

chmod +x scripts/maintenance.sh

# Add to crontab
echo "0 2 * * * /opt/forge-mcp-gateway/scripts/maintenance.sh" | crontab -
```

## 📚 Documentation and Training

### Required Documentation

#### Technical Documentation
- [x] Production deployment guide ✅ **(THIS DOCUMENT)**
- [ ] Performance optimization procedures
- [ ] Security hardening checklist
- [ ] Troubleshooting guide
- [ ] API reference documentation
- [ ] Configuration reference

#### Operational Documentation
- [ ] Service management procedures
- [ ] Monitoring and alerting guide
- [ ] Backup and recovery procedures
- [ ] Incident response procedures
- [ ] Change management procedures

#### Training Documentation
- [ ] Architecture overview and concepts
- [ ] Service management training
- [ ] Monitoring and alerting training
- [ ] Troubleshooting and debugging training
- [ ] Security best practices

### Training Materials

#### Onboarding Guide
```bash
# Create onboarding checklist
cat > docs/ONBOARDING.md << 'EOF'
# MCP Gateway Production Onboarding Checklist

## Pre-Onboarding
- [ ] Review architecture documentation
- [ ] Understand security policies
- [ ] Complete security training
- [ ] Review monitoring procedures

## System Access
- [ ] SSH access configured
- [ ] Docker permissions verified
- [ ] Environment variables understood
- [ ] Backup procedures tested

## Service Management
- [ ] Start/stop procedures learned
- [ ] Log analysis skills developed
- [ ] Health check interpretation
- [ ] Scaling procedures understood

## Troubleshooting
- [ ] Common issues identification
- [ ] Log analysis techniques
- [ ] Recovery procedures tested
- [ ] Escalation procedures known

## Security
- [ ] Security policies reviewed
- [ ] Incident response procedures
- [ ] Access management understood
- [ ] Audit procedures followed
EOF
```

#### Operational Runbooks
```bash
# Create operational runbooks
mkdir -p docs/runbooks

# Service Management Runbook
cat > docs/runbooks/SERVICE_MANAGEMENT.md << 'EOF'
# Service Management Runbook

## Service Status
- Gateway: http://localhost:4444/health
- Service Manager: http://localhost:9000/health
- Tool Router: http://localhost:8001/health

## Common Operations

### Starting Services
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Start specific service
docker-compose -f docker-compose.production.yml up -d gateway
```

### Stopping Services
```bash
# Graceful shutdown
docker-compose -f docker-compose.production.yml down

# Force stop
docker-compose -f docker-compose.production.yml down --remove-orphans
```

### Scaling Services
```bash
# Scale gateway
docker-compose -f docker-compose.production.yml up -d --scale gateway=2
```

## Emergency Procedures

### Service Recovery
```bash
# Full system restart
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --force-recreate
```

### Data Recovery
```bash
# Restore from latest backup
./scripts/backup-production.sh restore
```
EOF
```

## 🎯 Success Criteria

### Technical Success
- All services deployed and healthy
- Health checks passing consistently
- Resource utilization within limits
- Security hardening implemented
- Monitoring and alerting functional

### Operational Success
- Team trained on procedures
- Documentation complete and current
- Backup procedures tested
- Incident response procedures validated

### Business Success
- Service availability targets met
- Performance SLAs achieved
- Security compliance maintained
- Cost optimization realized

---

## 📞 Support

For technical support or questions:
- Review existing documentation
- Check troubleshooting guides
- Review monitoring dashboards
- Contact system administrator

For security incidents:
- Follow incident response procedures
- Contact security team immediately
- Preserve evidence for investigation
- Document lessons learned
```

This enhanced production deployment guide provides comprehensive coverage for secure, scalable, and maintainable MCP Gateway deployments with proper security hardening, monitoring, and operational procedures.
