# Production Deployment Guide

This guide covers the complete production deployment process for the Forge MCP Gateway.

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- At least 4GB RAM and 2 CPU cores
- 20GB+ disk space
- Domain name (optional, for SSL)

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/LucasSantana-Dev/forge-mcp-gateway.git
cd forge-mcp-gateway

# Copy production environment template
cp .env.production.example .env.production

# Edit production configuration
nano .env.production
```

### 2. Configure Environment Variables

Edit `.env.production` with your production values:

```bash
# Security (generate secure values)
JWT_SECRET=your-super-secure-jwt-secret-key-here-at-least-32-chars
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-secure-redis-password
GRAFANA_PASSWORD=your-secure-grafana-password

# Database
POSTGRES_DB=forge_mcp_prod
POSTGRES_USER=forge_user
DATABASE_URL=postgresql://forge_user:your-secure-postgres-password@postgres:5432/forge_mcp_prod

# Service URLs
GATEWAY_URL=https://your-domain.com
EXTERNAL_API_BASE_URL=https://api.your-domain.com
```

### 3. Deploy Services

```bash
# Make deployment script executable
chmod +x scripts/deploy-production.sh

# Run full deployment
./scripts/deploy-production.sh full
```

## 📋 Deployment Steps

### Step 1: Pre-deployment Checks

The deployment script automatically runs these checks:

- ✅ Docker and Docker Compose installation
- ✅ Environment file configuration
- ✅ Docker build validation
- ✅ Configuration file validation

### Step 2: Backup Current Deployment

```bash
# Manual backup (optional)
./scripts/deploy-production.sh backup
```

### Step 3: Build and Test

```bash
# Run tests only
./scripts/deploy-production.sh test
```

### Step 4: Deploy Services

```bash
# Deploy all services
./scripts/deploy-production.sh deploy
```

### Step 5: Health Verification

```bash
# Wait for services to be healthy
./scripts/deploy-production.sh health

# Verify deployment
./scripts/deploy-production.sh verify
```

## 🌐 Access Points

After successful deployment, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Gateway API** | http://localhost:8000 | Main MCP Gateway |
| **Admin UI** | http://localhost:3000 | Management Dashboard |
| **Grafana** | http://localhost:3001 | Monitoring Dashboard |
| **Prometheus** | http://localhost:9090 | Metrics Collection |
| **Service Manager** | http://localhost:9000 | Service Health |

## 🔧 Service Management

### Start Services

```bash
docker-compose -f docker-compose.production.yml up -d
```

### Stop Services

```bash
docker-compose -f docker-compose.production.yml down
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f gateway
```

### Scale Services

```bash
# Scale gateway service
docker-compose -f docker-compose.production.yml up -d --scale gateway=2
```

## 📊 Monitoring and Observability

### Health Checks

All services include health checks:

```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:9000/health
```

### Metrics Collection

- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics with pre-configured dashboards
- **Service Manager**: Monitors service lifecycle

### Log Management

Logs are automatically rotated and stored in `./logs/`:

```bash
# View recent logs
tail -f ./logs/deploy-*.log

# Clean old logs (older than 7 days)
find ./logs -name "*.log" -mtime +7 -delete
```

## 🔒 Security Configuration

### SSL/TLS Setup

1. **Obtain SSL Certificate** (Let's Encrypt recommended)
2. **Place certificates** in `/etc/nginx/ssl/`
3. **Update environment variables**:
   ```bash
   SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
   SSL_KEY_PATH=/etc/ssl/key.pem
   ```

### Network Security

- All services run on isolated Docker network
- Only necessary ports exposed
- Environment variables for sensitive data
- Regular security updates via Docker

### Access Control

```bash
# Update JWT secret (rotate regularly)
JWT_SECRET=$(openssl rand -hex 32)
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs service-name

# Check resource usage
docker stats

# Check disk space
df -h
```

#### Health Check Failures

```bash
# Manual health check
curl -f http://localhost:8000/health

# Check service dependencies
docker-compose -f docker-compose.production.yml ps
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats --no-stream

# Check service limits
docker-compose -f docker-compose.production.yml config
```

### Recovery Procedures

#### Database Recovery

```bash
# Restore from backup
docker-compose -f docker-compose.production.yml down
# Restore data volume from backup
docker-compose -f docker-compose.production.yml up -d
```

#### Service Reset

```bash
# Reset specific service
docker-compose -f docker-compose.production.yml stop service-name
docker-compose -f docker-compose.production.yml rm -f service-name
docker-compose -f docker-compose.production.yml up -d service-name
```

## 📈 Performance Optimization

### Resource Allocation

Default production resource limits:

| Service | CPU Limit | Memory Limit |
|---------|-----------|------------|
| Gateway | 1.0 | 1GB |
| Service Manager | 0.5 | 512MB |
| Tool Router | 0.5 | 512MB |
| PostgreSQL | 1.0 | 2GB |
| Redis | 0.5 | 512MB |
| Ollama | 2.0 | 4GB |

### Scaling Recommendations

- **Gateway**: Scale based on concurrent requests
- **Database**: Consider read replicas for high load
- **Cache**: Increase Redis memory for better performance
- **AI Services**: Scale Ollama based on model usage

### Monitoring Alerts

Configure alerts in Grafana for:

- High error rates (>5%)
- High response times (>2s)
- Resource utilization (>80%)
- Service health failures

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update without downtime
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d --no-deps gateway
```

### Backup Strategy

```bash
# Automated backup (configured in .env.production)
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

### Maintenance Windows

- **Weekly**: Security updates
- **Monthly**: Performance optimization
- **Quarterly**: Capacity planning

## 📚 Additional Resources

- [Architecture Guide](./architecture/OVERVIEW.md)
- [API Documentation](./docs/API_REFERENCE.md)
- [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)
- [Security Best Practices](./docs/SECURITY.md)

## 🆘 Support

For production deployment issues:

1. Check this documentation first
2. Review logs in `./logs/`
3. Check GitHub Issues
4. Contact support with deployment logs

---

**Note**: This deployment configuration is optimized for production use with security, monitoring, and scalability considerations. For development or testing, use the standard `docker-compose.yml` file.
