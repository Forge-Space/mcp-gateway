# Operational Procedures Guide

This guide provides comprehensive operational procedures for managing the Forge MCP Gateway in production environments.

## 🚨 Incident Response Procedures

### Critical Incident Response

#### Severity Levels
- **CRITICAL**: Service down, data loss, security breach
- **WARNING**: High resource usage, performance degradation
- **INFO**: Routine maintenance, informational events

#### Response Timeline
- **0-5 minutes**: Initial detection and alerting
- **5-15 minutes**: Automated response attempts
- **15-30 minutes**: Manual intervention if needed
- **30+ minutes**: Escalation to senior team

### Service-Specific Procedures

#### Gateway Service Issues
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps gateway

# Restart service
./scripts/incident-response.sh -r gateway

# Collect logs
./scripts/incident-response.sh -l gateway 200

# Scale if needed
./scripts/incident-response.sh -s gateway 2
```

#### Database Issues
```bash
# Check database connectivity
docker-compose -f docker-compose.production.yml exec postgres pg_isready

# Restart database
./scripts/incident-response.sh -r postgres

# Check disk space
df -h

# Collect database logs
./scripts/incident-response.sh -l postgres 300
```

#### Service Manager Issues
```bash
# Check service manager health
curl http://localhost:9000/health

# Restart service manager
./scripts/incident-response.sh -r service-manager

# Check Docker daemon status
docker info
```

## 📊 Monitoring Procedures

### Continuous Monitoring

#### Start Advanced Monitoring
```bash
# Continuous monitoring with 60-second intervals
./scripts/advanced-monitoring.sh -m 60

# Single monitoring check
./scripts/advanced-monitoring.sh -c

# Generate metrics report
./scripts/advanced-monitoring.sh -r
```

#### Key Metrics to Monitor
- **CPU Usage**: Alert at 80%, Critical at 90%
- **Memory Usage**: Alert at 85%, Critical at 90%
- **Disk Usage**: Alert at 80%, Critical at 90%
- **Response Time**: Alert at 2s, Critical at 5s
- **Error Rate**: Alert at 5%, Critical at 10%

### Health Checks

#### Service Health Endpoints
- **Gateway**: `http://localhost:8000/health`
- **Service Manager**: `http://localhost:9000/health`
- **Admin UI**: `http://localhost:3000`

#### Automated Health Checks
```bash
# Run all health checks
./scripts/health-check.sh

# Check specific service
curl -f http://localhost:8000/health || echo "Gateway unhealthy"
```

## 🔧 Maintenance Procedures

### Daily Maintenance

#### Log Rotation
```bash
# Rotate application logs
find ./logs -name "*.log" -mtime +7 -delete

# Rotate Docker logs
docker system prune -f
```

#### Health Monitoring
```bash
# Check service status
./scripts/advanced-monitoring.sh -c

# Review alerts
./scripts/advanced-monitoring.sh -a
```

#### Backup Verification
```bash
# Verify recent backups
ls -la ./backups/ | head -10

# Test backup restoration
./scripts/test-backup.sh
```

### Weekly Maintenance

#### Performance Analysis
```bash
# Generate performance report
./scripts/performance-report.sh

# Analyze resource trends
./scripts/resource-trends.sh

# Review scaling decisions
./scripts/scaling-analysis.sh
```

#### Security Updates
```bash
# Check for security updates
docker images | grep -v "latest"

# Update images if needed
docker-compose -f docker-compose.production.yml pull

# Restart services with new images
docker-compose -f docker-compose.production.yml up -d
```

#### Database Maintenance
```bash
# Database health check
docker-compose -f docker-compose.production.yml exec postgres pg_isready

# Database statistics
docker-compose -f docker-compose.production.yml exec postgres psql -c "SELECT pg_stat_database();"

# Vacuum and analyze (if needed)
docker-compose -f docker-compose.production.yml exec postgres psql -c "VACUUM ANALYZE;"
```

### Monthly Maintenance

#### Capacity Planning
```bash
# Generate capacity report
./scripts/capacity-report.sh

# Analyze growth trends
./scripts/growth-analysis.sh

# Plan resource allocation
./scripts/resource-planning.sh
```

#### Security Audit
```bash
# Run security scan
./scripts/security-audit.sh

# Check for vulnerabilities
docker scan $(docker images -q)

# Review access logs
./scripts/access-audit.sh
```

#### Disaster Recovery Testing
```bash
# Test backup restoration
./scripts/disaster-recovery-test.sh

# Validate failover procedures
./scripts/failover-test.sh

# Update recovery documentation
./scripts/update-recovery-docs.sh
```

## 🚀 Deployment Procedures

### Production Deployment

#### Pre-deployment Checklist
```bash
# Run pre-deployment checks
./scripts/deploy-production.sh -c -v -p

# Backup current deployment
./scripts/deploy-production.sh -b

# Validate configuration
./scripts/deploy-production.sh -v
```

#### Deployment Process
```bash
# Full deployment
./scripts/deploy-production.sh

# Deploy specific services only
./scripts/deploy-production.sh -d

# Verify deployment
./scripts/deploy-production.sh --verify
```

#### Post-deployment Verification
```bash
# Check service health
./scripts/health-check.sh

# Verify functionality
./scripts/smoke-test.sh

# Monitor performance
./scripts/advanced-monitoring.sh -c
```

### Rolling Updates

#### Zero-downtime Updates
```bash
# Pull new images
docker-compose -f docker-compose.production.yml pull

# Update service by service
docker-compose -f docker-compose.production.yml up -d --no-deps gateway
docker-compose -f docker-compose.production.yml up -d --no-deps service-manager

# Verify each service
./scripts/verify-service.sh gateway
./scripts/verify-service.sh service-manager
```

#### Blue-Green Deployment
```bash
# Deploy to green environment
./scripts/deploy-green.sh

# Test green environment
./scripts/test-green.sh

# Switch traffic
./scripts/switch-traffic.sh

# Decommission blue environment
./scripts/decommission-blue.sh
```

## 🔒 Security Procedures

### Security Monitoring

#### Daily Security Checks
```bash
# Check for failed login attempts
./scripts/security-monitor.sh --auth-failures

# Monitor for unusual activity
./scripts/security-monitor.sh --anomaly-detection

# Review access logs
./scripts/security-monitor.sh --access-logs
```

#### Incident Response
```bash
# Security incident response
./scripts/security-incident.sh --respond

# Isolate affected systems
./scripts/security-isolate.sh

# Collect forensic data
./scripts/security-forensics.sh
```

### Access Management

#### User Access Control
```bash
# Review user permissions
./scripts/access-review.sh

# Update user roles
./scripts/update-roles.sh

# Audit access changes
./scripts/access-audit.sh
```

#### Certificate Management
```bash
# Check certificate expiration
./scripts/cert-check.sh

# Renew certificates
./scripts/cert-renew.sh

# Update certificate stores
./scripts/cert-update.sh
```

## 📈 Performance Optimization

### Performance Monitoring

#### Real-time Monitoring
```bash
# Start performance monitoring
./scripts/performance-monitor.sh

# Generate performance report
./scripts/performance-report.sh

# Analyze performance trends
./scripts/performance-trends.sh
```

#### Bottleneck Analysis
```bash
# Identify performance bottlenecks
./scripts/bottleneck-analysis.sh

# Optimize slow queries
./scripts/query-optimization.sh

# Tune resource allocation
./scripts/resource-tuning.sh
```

### Scaling Procedures

#### Auto-scaling
```bash
# Enable auto-scaling
./scripts/auto-scale.sh --enable

# Configure scaling policies
./scripts/scale-policy.sh --configure

# Monitor scaling events
./scripts/scale-monitor.sh
```

#### Manual Scaling
```bash
# Scale up service
./scripts/incident-response.sh -s gateway 3

# Scale down service
./scripts/incident-response.sh -s gateway 1

# Check scaling status
./scripts/scale-status.sh
```

## 🔄 Backup and Recovery

### Backup Procedures

#### Automated Backups
```bash
# Configure automated backups
./scripts/backup-setup.sh

# Run manual backup
./scripts/backup-create.sh

# Verify backup integrity
./scripts/backup-verify.sh
```

#### Backup Restoration
```bash
# List available backups
./scripts/backup-list.sh

# Restore from backup
./scripts/backup-restore.sh --backup-id <id>

# Verify restoration
./scripts/backup-verify-restore.sh
```

### Disaster Recovery

#### Recovery Procedures
```bash
# Initiate disaster recovery
./scripts/disaster-recovery.sh

# Restore services
./scripts/restore-services.sh

# Verify recovery
./scripts/verify-recovery.sh
```

#### Recovery Testing
```bash
# Test recovery procedures
./scripts/recovery-test.sh

# Validate recovery time
./scripts/recovery-time-test.sh

# Update recovery documentation
./scripts/update-recovery-docs.sh
```

## 📋 Troubleshooting Guide

### Common Issues

#### Service Won't Start
```bash
# Check container logs
docker-compose -f docker-compose.production.yml logs service-name

# Check resource constraints
docker stats

# Check port conflicts
netstat -tulpn | grep :port

# Restart service
./scripts/incident-response.sh -r service-name
```

#### High Resource Usage
```bash
# Identify resource usage
docker stats

# Check for memory leaks
./scripts/memory-leak-check.sh

# Optimize resource allocation
./scripts/resource-optimize.sh

# Scale if needed
./scripts/incident-response.sh -s service-name 2
```

#### Network Issues
```bash
# Check network connectivity
ping gateway-host

# Check port availability
telnet gateway-host 8000

# Check DNS resolution
nslookup gateway-host

# Restart networking
./scripts/network-restart.sh
```

#### Database Issues
```bash
# Check database connectivity
docker-compose -f docker-compose.production.yml exec postgres pg_isready

# Check database logs
docker-compose -f docker-compose.production.yml logs postgres

# Check disk space
df -h

# Restart database
./scripts/incident-response.sh -r postgres
```

### Debugging Procedures

#### Enable Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug

# Restart services with debug
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Monitor debug logs
docker-compose -f docker-compose.production.yml logs -f
```

#### Collect Debug Information
```bash
# Collect system information
./scripts/debug-info.sh

# Collect service diagnostics
./scripts/service-diagnostics.sh

# Generate debug report
./scripts/debug-report.sh
```

## 📞 Escalation Procedures

### When to Escalate

#### Immediate Escalation Required
- Data loss or corruption
- Security breach detected
- Multiple services down
- Critical performance degradation
- User impact > 50%

#### Escalation Contacts
- **Level 1**: On-call engineer
- **Level 2**: Senior engineer
- **Level 3**: Engineering manager
- **Level 4**: CTO/VP Engineering

### Escalation Process

#### Step 1: Initial Assessment
```bash
# Assess incident severity
./scripts/assess-incident.sh

# Collect initial diagnostics
./scripts/collect-diagnostics.sh

# Document incident
./scripts/document-incident.sh
```

#### Step 2: Attempt Resolution
```bash
# Try automated recovery
./scripts/automated-recovery.sh

# Monitor recovery progress
./scripts/monitor-recovery.sh

# Document attempts
./scripts/document-attempts.sh
```

#### Step 3: Escalate if Needed
```bash
# Escalate incident
./scripts/escalate-incident.sh

# Notify stakeholders
./scripts/notify-stakeholders.sh

# Handoff documentation
./scripts/handoff-documentation.sh
```

## 📚 Documentation Procedures

### Documentation Updates

#### Update Operational Procedures
```bash
# Update procedures after incident
./scripts/update-procedures.sh

# Review documentation accuracy
./scripts/review-documentation.sh

# Publish updated documentation
./scripts/publish-documentation.sh
```

#### Knowledge Base Management
```bash
# Document new procedures
./scripts/document-procedure.sh

# Update knowledge base
./scripts/update-knowledge-base.sh

# Review knowledge base
./scripts/review-knowledge-base.sh
```

### Training Procedures

#### New Team Member Onboarding
```bash
# Generate onboarding checklist
./scripts/onboarding-checklist.sh

# Provide training materials
./scripts/training-materials.sh

# Schedule training sessions
./scripts/schedule-training.sh
```

#### Ongoing Training
```bash
# Schedule regular training
./scripts/schedule-regular-training.sh

# Update training materials
./scripts/update-training.sh

# Assess training effectiveness
./scripts/assess-training.sh
```

---

## 📞 Support Contacts

### Emergency Contacts
- **On-call Engineer**: [Phone Number]
- **Engineering Manager**: [Phone Number]
- **CTO**: [Phone Number]

### Service Providers
- **Cloud Provider**: [Contact Information]
- **Database Support**: [Contact Information]
- **Security Team**: [Contact Information]

### Documentation
- **Internal Wiki**: [URL]
- **Runbooks**: [URL]
- **Knowledge Base**: [URL]

---

**Note**: This guide should be regularly updated based on operational experience and changing requirements. All procedures should be tested regularly to ensure effectiveness.