# Docker Operations Runbook - MCP Gateway

## 📋 **Overview**
This runbook provides operational procedures for managing, monitoring, and troubleshooting the Docker-optimized MCP Gateway deployment.

## 🚀 **Quick Start**

### **Starting Services**
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### **Monitoring Services**
```bash
# Real-time monitoring dashboard
./scripts/docker-monitoring-dashboard.sh

# Single check
./scripts/docker-monitoring-dashboard.sh -s

# Continuous monitoring (5 minutes)
./scripts/docker-monitoring-dashboard.sh -d 300
```

### **Performance Testing**
```bash
# Full performance test suite
./scripts/docker-performance-test.sh

# Startup performance only
./scripts/docker-performance-test.sh -s

# Response time test only
./scripts/docker-performance-test.sh -r

# Custom test duration (10 minutes)
./scripts/docker-performance-test.sh -d 600
```

### **Security Scanning**
```bash
# Full security scan
./scripts/docker-security-scan.sh

# Image scanning only
./scripts/docker-security-scan.sh -i

# Basic security checks only
./scripts/docker-security-scan.sh -i --basic-only
```

## 📊 **Daily Operations**

### **Morning Health Check**
```bash
# 1. Check service status
docker-compose ps

# 2. Check resource usage
docker stats --no-stream

# 3. Run quick monitoring
./scripts/docker-monitoring-dashboard.sh -s

# 4. Check for alerts
tail -n 20 /tmp/mcp-gateway-monitoring/alerts.log
```

### **Performance Monitoring**
```bash
# Run daily performance test
./scripts/docker-performance-test.sh -d 300 --set-baseline

# Compare with previous baseline
./scripts/docker-performance-test.sh -c
```

### **Security Check**
```bash
# Daily security scan
./scripts/docker-security-scan.sh -i --basic-only

# Weekly comprehensive scan
./scripts/docker-security-scan.sh
```

## 🔧 **Troubleshooting**

### **Service Not Starting**

**Symptoms**: Container in restart loop or not starting

**Steps**:
1. Check container logs:
   ```bash
   docker-compose logs <service-name>
   ```

2. Check resource limits:
   ```bash
   docker inspect <container-name> | grep -A 10 "Resources"
   ```

3. Check system resources:
   ```bash
   docker system df
   df -h
   free -h
   ```

4. Common fixes:
   ```bash
   # Increase memory limit
   # Edit docker-compose.yml and increase memory limit

   # Clear Docker cache
   docker system prune -f

   # Restart service
   docker-compose restart <service-name>
   ```

### **High Resource Usage**

**Symptoms**: CPU or memory usage consistently high

**Steps**:
1. Identify problematic container:
   ```bash
   docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
   ```

2. Check container processes:
   ```bash
   docker exec <container-name> ps aux
   ```

3. Review resource limits:
   ```bash
   docker inspect <container-name> | grep -A 20 "Resources"
   ```

4. Solutions:
   - Increase resource limits in docker-compose.yml
   - Check for memory leaks in application logs
   - Restart the service
   - Scale horizontally if needed

### **Health Check Failures**

**Symptoms**: Health checks showing unhealthy status

**Steps**:
1. Check health check configuration:
   ```bash
   docker inspect <container-name> | grep -A 10 "Health"
   ```

2. Test health endpoint manually:
   ```bash
   curl -f http://localhost:<port>/health
   ```

3. Check application logs:
   ```bash
   docker-compose logs <service-name> | tail -50
   ```

4. Common fixes:
   - Fix application errors
   - Adjust health check timeout/intervals
   - Verify health endpoint is accessible

### **Performance Issues**

**Symptoms**: Slow response times or degraded performance

**Steps**:
1. Run performance test:
   ```bash
   ./scripts/docker-performance-test.sh -r
   ```

2. Check resource usage trends:
   ```bash
   ./scripts/docker-monitoring-dashboard.sh -s
   ```

3. Review system metrics:
   ```bash
   docker system df
   docker stats --no-stream
   ```

4. Optimization steps:
   - Increase resource limits
   - Check for resource bottlenecks
   - Review application performance
   - Consider scaling options

## 🚨 **Incident Response**

### **Critical Service Down**

**Response Time**: Immediate

**Steps**:
1. Assess impact:
   ```bash
   docker-compose ps
   ./scripts/docker-monitoring-dashboard.sh -s
   ```

2. Check logs for errors:
   ```bash
   docker-compose logs --tail=100 <affected-service>
   ```

3. Attempt recovery:
   ```bash
   docker-compose restart <affected-service>
   ```

4. If restart fails:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

5. Monitor recovery:
   ```bash
   watch -n 5 'docker-compose ps'
   ```

### **Security Vulnerability Detected**

**Response Time**: Within 24 hours

**Steps**:
1. Run security scan:
   ```bash
   ./scripts/docker-security-scan.sh -i
   ```

2. Review findings:
   ```bash
   cat /tmp/mcp-gateway-security-results/security_report_*.json
   ```

3. Prioritize fixes:
   - Critical: Immediate action required
   - High: Fix within 24 hours
   - Medium: Fix within 7 days
   - Low: Fix in next maintenance window

4. Apply fixes:
   - Update base images
   - Rebuild containers
   - Test and deploy

### **Resource Exhaustion**

**Response Time**: Within 1 hour

**Steps**:
1. Identify resource issue:
   ```bash
   docker stats --no-stream
   df -h
   free -h
   ```

2. Free up resources:
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

3. Adjust limits if needed:
   ```bash
   # Edit docker-compose.yml to adjust resource limits
   ```

4. Monitor after adjustments:
   ```bash
   ./scripts/docker-monitoring-dashboard.sh -d 300
   ```

## 📈 **Performance Tuning**

### **Resource Optimization**

**Memory Tuning**:
1. Monitor memory usage patterns:
   ```bash
   ./scripts/docker-performance-test.sh -d 3600
   ```

2. Adjust memory limits based on usage:
   ```yaml
   # In docker-compose.yml
   services:
     service-name:
       deploy:
         resources:
           limits:
             memory: 512M
           reservations:
             memory: 256M
   ```

3. Test changes:
   ```bash
   docker-compose up -d
   ./scripts/docker-monitoring-dashboard.sh -s
   ```

**CPU Tuning**:
1. Monitor CPU usage:
   ```bash
   docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}"
   ```

2. Adjust CPU limits:
   ```yaml
   services:
     service-name:
       deploy:
         resources:
           limits:
             cpus: '0.5'
           reservations:
             cpus: '0.1'
   ```

### **Health Check Optimization**

**Optimize Health Checks**:
1. Review current health checks:
   ```bash
   docker inspect <container-name> | grep -A 10 "Health"
   ```

2. Optimize intervals and timeouts:
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 40s
   ```

3. Test health check performance:
   ```bash
   ./scripts/docker-performance-test.sh -r
   ```

## 🔒 **Security Operations**

### **Regular Security Tasks**

**Daily**:
- Basic security scan: `./scripts/docker-security-scan.sh -i --basic-only`
- Review access logs
- Check for unusual activity

**Weekly**:
- Full security scan: `./scripts/docker-security-scan.sh`
- Review security recommendations
- Update base images if needed

**Monthly**:
- Comprehensive security audit
- Review and update security policies
- Security training refresh

### **Security Incident Response**

**Vulnerability Found**:
1. Assess severity:
   ```bash
   ./scripts/docker-security-scan.sh -i | grep -E "(Critical|High)"
   ```

2. Plan remediation:
   - Critical: Immediate patch and redeploy
   - High: Patch within 24 hours
   - Medium: Patch within 7 days

3. Implement fix:
   ```bash
   # Update Dockerfile with patched base image
   docker-compose build <service>
   docker-compose up -d <service>
   ```

4. Verify fix:
   ```bash
   ./scripts/docker-security-scan.sh -i
   ```

## 📝 **Maintenance Procedures**

### **Weekly Maintenance**

**System Cleanup**:
```bash
# Clean up unused Docker resources
docker system prune -f
docker volume prune -f
docker network prune -f

# Check disk space
df -h

# Review logs
find /var/lib/docker/containers/ -name "*.log" -size +100M
```

**Performance Check**:
```bash
# Run performance test
./scripts/docker-performance-test.sh -d 300

# Check resource usage
docker stats --no-stream

# Review alerts
tail -n 50 /tmp/mcp-gateway-monitoring/alerts.log
```

### **Monthly Maintenance**

**Image Updates**:
```bash
# Check for image updates
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"

# Rebuild images with updated base images
docker-compose build --no-cache

# Test after rebuild
./scripts/docker-performance-test.sh -s
```

**Configuration Review**:
```bash
# Review resource limits
grep -A 10 "resources:" docker-compose.yml

# Review health checks
grep -A 5 "healthcheck:" docker-compose.yml

# Review security settings
./scripts/docker-security-scan.sh -d
```

## 📊 **Monitoring and Alerting**

### **Key Metrics to Monitor**

**Resource Metrics**:
- CPU usage per container
- Memory usage per container
- Disk usage
- Network I/O

**Health Metrics**:
- Container uptime
- Health check status
- Response times
- Error rates

**Security Metrics**:
- Vulnerability count
- Failed login attempts
- Unusual network activity

### **Alert Thresholds**

**Critical Alerts**:
- Container down > 5 minutes
- CPU usage > 90% for > 5 minutes
- Memory usage > 95% for > 5 minutes
- Critical security vulnerabilities

**Warning Alerts**:
- CPU usage > 80% for > 10 minutes
- Memory usage > 85% for > 10 minutes
- Health check failures > 3 consecutive
- Medium security vulnerabilities

### **Alert Response**

**Critical Alert Response**:
1. Immediate assessment (within 5 minutes)
2. Implement fix or workaround
3. Monitor recovery
4. Document incident

**Warning Alert Response**:
1. Assess within 1 hour
2. Plan fix for next maintenance window
3. Monitor trend
4. Document for future reference

## 🚀 **Scaling and Growth**

### **Horizontal Scaling**

**When to Scale**:
- Consistent high CPU (>80%)
- Consistent high memory (>85%)
- Increased request volume
- Performance degradation

**How to Scale**:
```bash
# Scale service
docker-compose up -d --scale <service-name>=<replicas>

# Monitor scaled service
docker-compose ps
./scripts/docker-monitoring-dashboard.sh -s
```

### **Vertical Scaling**

**When to Scale Up**:
- Resource limits consistently hit
- Memory-intensive workloads
- CPU-intensive operations

**How to Scale Up**:
```yaml
# Increase resource limits in docker-compose.yml
services:
  service-name:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

## 📚 **Reference Materials**

### **Useful Commands**

**Container Management**:
```bash
# List all containers
docker ps -a

# Inspect container
docker inspect <container-name>

# Execute command in container
docker exec -it <container-name> /bin/sh

# View logs
docker logs -f <container-name>
```

**Image Management**:
```bash
# List images
docker images

# Remove unused images
docker image prune -f

# Build image
docker build -t <image-name> .
```

**System Information**:
```bash
# Docker system info
docker system info

# Docker disk usage
docker system df

# Container resource usage
docker stats --no-stream
```

### **Configuration Files**

**docker-compose.yml**: Main service configuration
**Dockerfile.*: Service-specific build configurations
**.dockerignore**: Build context exclusions
**scripts/**: Monitoring and management tools

### **Log Locations**

**Docker Logs**: `/var/lib/docker/containers/*/`
**Application Logs**: Container-specific via `docker-compose logs`
**Monitoring Logs**: `/tmp/mcp-gateway-monitoring/`
**Security Logs**: `/tmp/mcp-gateway-security-results/`

---

## 📞 **Emergency Contacts**

**System Administrator**: [Contact Information]
**DevOps Team**: [Contact Information]
**Security Team**: [Contact Information]

## 🔄 **Version History**

- **v1.0.0**: Initial runbook creation
- **v1.1.0**: Added performance testing procedures
- **v1.2.0**: Enhanced security scanning procedures
- **v1.3.0**: Added scaling procedures

---

**Last Updated**: $(date '+%Y-%m-%d')
**Next Review**: $(date -d '+1 month' '+%Y-%m-%d')
