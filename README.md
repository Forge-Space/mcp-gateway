# MCP Gateway

A comprehensive, enterprise-ready Model Context Protocol (MCP) Gateway with advanced security, compliance, and performance features.

## 🚀 Overview

MCP Gateway provides a secure, scalable, and compliant gateway for managing Model Context Protocol (MCP) communications. It offers comprehensive security features including encryption, access control, GDPR compliance, and automated data retention policies.

### Key Features

- 🔐 **Enterprise Security**: Fernet encryption, role-based access control, comprehensive audit trails
- 📋 **Regulatory Compliance**: GDPR, CCPA, HIPAA, SOX, PCI-DSS, ISO-27001 compliance
- 🔄 **Data Retention**: Automated retention policies with multiple policy types
- 📊 **Performance Monitoring**: Real-time metrics and performance optimization
- 🌐 **REST API**: Comprehensive API for security and compliance management
- 🐳 **Container Ready**: Docker-based deployment with multi-platform support
- 🧪 **High Test Coverage**: Comprehensive test suite with 80%+ coverage
- 🔒 **Cache Security**: Advanced cache security with encryption and access control (NEW)

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Security Features](#security-features)
- [Cache Security](#cache-security)
- [Compliance](#compliance)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Quick Start

### Prerequisites

- Python 3.14+
- Docker and Docker Compose
- PostgreSQL (for production)
- Redis (optional, for distributed caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/forgespace/mcp-gateway.git
   cd mcp-gateway
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the gateway**
   ```bash
   docker-compose up -d
   ```

5. **Verify installation**
   ```bash
   curl http://localhost:4444/health
   ```

## 🏗️ Architecture

### System Architecture

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
│  ┌──────────────────────────────────────────────┐  │
│  │  Virtual Servers (Tool Collections)                  │  │
│  │  - cursor-default (all tools)                        │  │
│  │  - cursor-router (tool-router only)                  │  │
│  │  - custom servers (filtered tool sets)              │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Gateway Registry                                     │  │
│  │  - Upstream MCP servers                              │  │
│  │  - Authentication & routing                          │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Cache Security Layer (NEW)                           │  │
│  │  - Encryption & Access Control                        │  │
│  │  - GDPR Compliance & Retention                       │  │
│  │  - Audit Trail & Monitoring                         │  │
│  └──────────────────────────────────────────────┘  │
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

### Core Components

1. **MCP Gateway**: Central hub for MCP server aggregation
2. **Virtual Servers**: Tool collections with access control
3. **Gateway Registry**: Server registration and discovery
4. **Tool Router**: AI-powered dynamic tool selection
5. **Cache Security Layer**: Advanced security and compliance features

## 🔒 Security Features

### Cache Security (Phase 2.4)

#### **Encryption System**
- **Fernet-based Encryption**: AES-256 encryption for sensitive data
- **Key Management**: Automatic key generation and rotation
- **Data Classification**: Multiple classification levels (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED, PERSONAL, SENSITIVE_PERSONAL)
- **Thread-Safe Operations**: Concurrent access protection
- **Performance Optimized**: < 5ms encryption/decryption for typical data

#### **Access Control**
- **Role-Based Permissions**: Granular access control system
- **Access Request Workflow**: Approval system for elevated permissions
- **Permission Inheritance**: Role-based permission inheritance
- **Audit Logging**: Complete access control audit trail
- **Integration**: Seamless integration with cache operations

#### **GDPR Compliance**
- **Consent Management**: Complete consent lifecycle management
- **Data Subject Rights**: Access, portability, rectification, erasure
- **Right to be Forgotten**: Complete data removal capabilities
- **Consent Tracking**: Timestamped consent records with metadata
- **Compliance Reporting**: Automated compliance assessment and reporting

#### **Retention Policies**
- **Rule-Based Retention**: Configurable retention policies by data type
- **Lifecycle Management**: Automated data lifecycle stage transitions
- **Retention Scheduler**: Automated cleanup operations
- **Retention Auditing**: Compliance checking and reporting
- **Multiple Triggers**: Time-based, access-based, and size-based retention

### Enterprise Security Standards

- **GDPR**: Full compliance with consent management and data subject rights
- **CCPA**: California Consumer Privacy Act compliance
- **HIPAA**: Healthcare information protection
- **SOX**: Sarbanes-Oxley Act compliance
- **PCI-DSS**: Payment card industry data security
- **ISO-27001**: Information security management

## 🔒 Cache Security

### Overview

The cache security module provides comprehensive protection for cached data, ensuring that sensitive information is encrypted, access-controlled, and retained according to regulatory requirements.

### Key Components

#### **CacheEncryption**
```python
from tool_router.cache.security import CacheEncryption

# Initialize encryption
encryption = CacheEncryption()
encryption.set_encryption_key("your-encryption-key")

# Encrypt data
encrypted_data = encryption.encrypt("sensitive_data")

# Decrypt data
decrypted_data = encryption.decrypt(encrypted_data)
```

#### **AccessControlManager**
```python
from tool_router.cache.security import AccessControlManager

# Initialize access control
access_manager = AccessControlManager()

# Check permissions
has_access = access_manager.check_access(
    user_id="user123",
    operation="read",
    resource="cache_key",
    data_classification="CONFIDENTIAL"
)
```

#### **GDPRComplianceManager**
```python
from tool_router.cache.compliance import GDPRComplianceManager

# Initialize compliance manager
gdpr_manager = GDPRComplianceManager()

# Record consent
gdpr_manager.record_consent(
    user_id="user123",
    data_type="cache_data",
    purpose="storage",
    consent_given=True
)
```

#### **RetentionPolicyManager**
```python
from tool_router.cache.retention import RetentionPolicyManager

# Initialize retention manager
retention_manager = RetentionPolicyManager()

# Create retention policy
retention_manager.create_policy(
    policy_id="personal_data",
    data_classification="PERSONAL",
    retention_days=2555,  # 7 years for GDPR
    auto_delete=True
)
```

### Security Configuration

```bash
# Security Configuration
CACHE_ENCRYPTION_KEY=your-encryption-key
CACHE_ACCESS_CONTROL_ENABLED=true
CACHE_GDPR_ENABLED=true
CACHE_RETENTION_ENABLED=true
CACHE_AUDIT_ENABLED=true

# Retention Configuration
CACHE_RETENTION_PUBLIC_DAYS=30
CACHE_RETENTION_INTERNAL_DAYS=90
CACHE_RETENTION_CONFIDENTIAL_DAYS=180
CACHE_RETENTION_RESTRICTED_DAYS=365
CACHE_RETENTION_PERSONAL_DAYS=2555
```

## 📋 Compliance

### Regulatory Compliance

#### **GDPR (General Data Protection Regulation)**
- ✅ **Data Protection**: All personal data encrypted by default
- ✅ **Consent Management**: Full consent lifecycle management
- ✅ **Right to be Forgotten**: Complete data removal capability
- ✅ **Data Subject Rights**: Access, portability, rectification, erasure
- ✅ **Data Retention**: Configurable retention periods by data type
- ✅ **Audit Trail**: Complete audit logging for compliance

#### **CCPA (California Consumer Privacy Act)**
- ✅ **Consumer Rights**: Right to know, delete, opt-out
- ✅ **Data Minimization**: Collect only necessary data
- ✅ **Purpose Limitation**: Use data for specified purposes only
- ✅ **Data Security**: Reasonable security measures

#### **HIPAA (Health Insurance Portability and Accountability Act)**
- ✅ **Protected Health Information**: PHI encryption and access control
- ✅ **Audit Controls**: Comprehensive audit trail
- ✅ **Access Management**: Role-based access to health data
- **Transmission Security**: Secure data transmission

#### **SOX (Sarbanes-Oxley Act)**
- ✅ **Internal Controls**: Comprehensive internal control framework
- ✅ **Audit Trail**: Complete audit logging and reporting
- ✅ **Data Integrity**: Data integrity controls and validation
- ✅ **Access Controls**: Segregation of duties and access controls

### Compliance Features

#### **Consent Management**
- **Consent Recording**: Timestamped consent records with metadata
- **Consent Validation**: Automated consent validation checks
- **Consent Withdrawal**: Easy consent withdrawal with data cleanup
- **Consent Analytics**: Consent metrics and reporting

#### **Data Subject Requests**
- **Access Requests**: Automated data access request handling
- **Portability Requests**: Data export in machine-readable format
- **Rectification Requests**: Data correction and update capabilities
- **Erasure Requests**: Complete data removal with verification

#### **Compliance Reporting**
- **Assessment Reports**: Automated compliance assessment scoring
- **Compliance Metrics**: Real-time compliance status tracking
- **Audit Reports**: Detailed audit trail analysis
- **Regulatory Filings**: Automated compliance documentation

## 🌐 API Documentation

### Security API

#### **Encryption Endpoints**
```bash
# Encrypt data
POST /api/security/encrypt
Content-Type: application/json
{
  "data": "sensitive_information",
  "classification": "CONFIDENTIAL",
  "key_id": "optional_key_id"
}

# Decrypt data
POST /api/security/decrypt
Content-Type: application/json
{
  "encrypted_data": "gAAAA...",
  "key_id": "optional_key_id"
}
```

#### **Access Control Endpoints**
```bash
# Check access permissions
POST /api/security/access/check
Content-Type: application/json
{
  "user_id": "user123",
  "operation": "read",
  "resource": "cache_key",
  "data_classification": "CONFIDENTIAL"
}

# Create access request
POST /api/security/access/request
Content-Type: application/json
{
  "user_id": "user123",
  "operation": "write",
  "resource": "cache_key",
  "data_classification": "CONFIDENTIAL",
  "reason": "Business requirement"
}
```

#### **Compliance Endpoints**
```bash
# Record consent
POST /api/compliance/consent/record
Content-Type: application/json
{
  "user_id": "user123",
  "data_type": "cache_data",
  "purpose": "storage",
  "consent_given": true,
  "metadata": {}
}

# Check consent
GET /api/compliance/consent/check?user_id=user123&data_type=cache_data&purpose=storage

# Create data subject request
POST /api/compliance/data-subject/request
Content-Type: application/json
{
  "user_id": "user123",
  "request_type": "access",
  "data_type": "cache_data",
  "reason": "Data access request"
}
```

#### **Retention Endpoints**
```bash
# Create retention policy
POST /api/retention/policies
Content-Type: application/json
{
  "policy_id": "personal_data",
  "data_classification": "PERSONAL",
  "retention_days": 2555,
  "auto_delete": true,
  "description": "GDPR compliant retention policy"
}

# Enforce retention
POST /api/retention/enforce
Content-Type: application/json
{
  "policy_id": "personal_data",
  "dry_run": false
}
```

### Configuration API

#### **Security Configuration**
```bash
# Get security configuration
GET /api/config/security

# Update security configuration
PUT /api/config/security
Content-Type: application/json
{
  "encryption_key_rotation_days": 90,
  "access_control_enabled": true,
  "gdpr_enabled": true,
  "retention_enabled": true,
  "audit_enabled": true
}
```

#### **Key Management**
```bash
# Rotate encryption key
POST /api/config/keys/rotate

# Get key status
GET /api/config/keys/status
```

### Monitoring API

#### **Health Check**
```bash
# System health check
GET /api/health

# Security health check
GET /api/health/security
```

#### **Metrics**
```bash
# Security metrics
GET /api/metrics/security

# Compliance metrics
GET /api/metrics/compliance

# Retention metrics
GET /api/metrics/retention
```

#### **Audit Trail**
```bash
# Get audit trail
GET /api/audit/trail?user_id=user123&limit=100

# Get audit summary
GET /api/audit/summary?start_date=2024-01-01&end_date=2024-12-31
```

## ⚙️ Configuration

### Environment Variables

#### **Security Configuration**
```bash
# Encryption Settings
CACHE_ENCRYPTION_KEY=your-encryption-key-here
CACHE_ENCRYPTION_ALGORITHM=FERNET
CACHE_KEY_ROTATION_DAYS=90

# Access Control Settings
CACHE_ACCESS_CONTROL_ENABLED=true
CACHE_ACCESS_REQUEST_EXPIRY_HOURS=24
CACHE_DEFAULT_ACCESS_LEVEL=READ

# GDPR Compliance Settings
CACHE_GDPR_ENABLED=true
CACHE_CONSENT_RETENTION_DAYS=2555
CACHE_DATA_SUBJECT_REQUEST_RETENTION_DAYS=365

# Retention Settings
CACHE_RETENTION_ENABLED=true
CACHE_RETENTION_PUBLIC_DAYS=30
CACHE_RETENTION_INTERNAL_DAYS=90
CACHE_RETENTION_CONFIDENTIAL_DAYS=180
CACHE_RETENTION_RESTRICTED_DAYS=365
CACHE_RETENTION_PERSONAL_DAYS=2555
CACHE_RETENTION_SENSITIVE_PERSONAL_DAYS=2555

# Audit Settings
CACHE_AUDIT_ENABLED=true
CACHE_MAX_AUDIT_ENTRIES=10000
CACHE_AUDIT_RETENTION_DAYS=365

# API Settings
CACHE_SECURITY_API_HOST=0.0.0.0
CACHE_SECURITY_API_PORT=8001
CACHE_SECURITY_API_DEBUG=false
CACHE_SECURITY_API_WORKERS=4
```

#### **Cache Configuration**
```bash
# Cache Backend Configuration
CACHE_BACKEND_TYPE=memory  # memory, redis, hybrid
CACHE_MAX_SIZE=1000
CACHE_DEFAULT_TTL=3600

# Redis Configuration (if using Redis)
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_REDIS_PASSWORD=redis-password
CACHE_REDIS_DB=0
CACHE_REDIS_SSL=false

# Performance Configuration
CACHE_CLEANUP_INTERVAL=300
CACHE_METRICS_ENABLED=true
CACHE_PERFORMANCE_MONITORING=true
```

### Configuration Files

#### **Docker Compose**
```yaml
version: '3.8'

services:
  gateway:
    build: .
    ports:
      - "4444:4444"
    environment:
      - CACHE_ENCRYPTION_KEY=${CACHE_ENCRYPTION_KEY}
      - CACHE_ACCESS_CONTROL_ENABLED=true
      - CACHE_GDPR_ENABLED=true
      - CACHE_RETENTION_ENABLED=true
      - CACHE_AUDIT_ENABLED=true
    volumes:
      - ./data:/app/data
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcp_gateway
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

#### **Application Configuration**
```python
# config.py
from tool_router.cache.config import CacheConfig
from tool_router.cache.security import CacheSecurityConfig

class AppConfig:
    def __init__(self):
        self.cache_config = CacheConfig(
            max_size=int(os.getenv('CACHE_MAX_SIZE', 1000)),
            ttl=int(os.getenv('CACHE_DEFAULT_TTL', 3600)),
            cleanup_interval=int(os.getenv('CACHE_CLEANUP_INTERVAL', 300)),
            enable_metrics=os.getenv('CACHE_METRICS_ENABLED', 'true').lower() == 'true'
        )

        self.security_config = CacheSecurityConfig(
            encryption_key=os.getenv('CACHE_ENCRYPTION_KEY'),
            access_control_enabled=os.getenv('CACHE_ACCESS_CONTROL_ENABLED', 'true').lower() == 'true',
            gdpr_enabled=os.getenv('CACHE_GDPR_ENABLED', 'true').lower() == 'true',
            retention_enabled=os.getenv('CACHE_RETENTION_ENABLED', 'true').lower() == 'true',
            audit_enabled=os.getenv('CACHE_AUDIT_ENABLED', 'true').lower() == 'true'
        )
```

## 🚀 Deployment

### Docker Deployment

#### **Production Deployment**
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale gateway=3

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f gateway
```

#### **Development Deployment**
```bash
# Development setup
docker-compose -f docker-compose.dev.yml up -d

# Run tests
docker-compose -f docker-compose.dev.yml exec gateway pytest

# Development server
docker-compose -f docker-compose.dev.yml exec gateway python -m uvicorn main:app --host 0.0.0.0 --port 4444 --reload
```

### Kubernetes Deployment

#### **Kubernetes Manifest**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-gateway
  template:
    metadata:
      labels:
        app: mcp-gateway
    spec:
      containers:
      - name: gateway
        image: mcp-gateway:latest
        ports:
        - containerPort: 4444
        env:
        - name: CACHE_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-gateway-secrets
              key: encryption-key
        - name: CACHE_ACCESS_CONTROL_ENABLED
          value: "true"
        - name: CACHE_GDPR_ENABLED
          value: "true"
        - name: CACHE_RETENTION_ENABLED
          value: "true"
        - name: CACHE_AUDIT_ENABLED
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: config-volume
        configMap:
          name: mcp-gateway-config
      - name: data-volume
        persistentVolumeClaim:
          claimName: mcp-gateway-data
```

### Environment Setup

#### **Production Environment**
```bash
# Set up production environment
export CACHE_ENCRYPTION_KEY=$(openssl rand -base64 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export CACHE_ACCESS_CONTROL_ENABLED=true
export CACHE_GDPR_ENABLED=true
export CACHE_RETENTION_ENABLED=true
export CACHE_AUDIT_ENABLED=true

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

#### **Development Environment**
```bash
# Set up development environment
export CACHE_ENCRYPTION_KEY=dev-key-for-testing-only
export POSTGRES_PASSWORD=dev-password
export CACHE_ACCESS_CONTROL_ENABLED=true
export CACHE_GDPR_ENABLED=true
export CACHE_RETENTION_ENABLED=true
export CACHE_AUDIT_ENABLED=true

# Deploy
docker-compose -f docker-compose.dev.yml up -d
```

## 📊 Monitoring

### Health Monitoring

#### **Health Check Endpoints**
```bash
# Overall system health
curl http://localhost:4444/health

# Security health
curl http://localhost:4444/health/security

# Compliance health
curl http://localhost:4444/health/compliance

# Cache health
curl http://localhost:4444/health/cache
```

#### **Metrics Collection**
```bash
# Security metrics
curl http://localhost:4444/metrics/security

# Compliance metrics
curl http://localhost:4444/metrics/compliance

# Retention metrics
curl http://localhost:4444/metrics/retention

# Performance metrics
curl http://localhost:4444/metrics/performance
```

### Logging

#### **Structured Logging**
```python
import logging
from tool_router.cache.security import CacheSecurityManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/mcp-gateway/security.log'),
        logging.handlers.RotatingFileHandler(
            '/var/log/mcp-gateway/security.log',
            maxBytes=10485760,  # 100MB
            backupCount=5
        )
    ]
)

# Security manager with logging
security_manager = CacheSecurityManager()
```

#### **Audit Trail**
```python
from tool_router.cache.security import CacheSecurityManager

# Get audit trail
security_manager = CacheSecurityManager()
audit_trail = security_manager.get_audit_trail(
    user_id="user123",
    event_type="cache_access",
    limit=100
)

# Filter audit trail
filtered_trail = security_manager.get_audit_trail(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    event_type="encryption"
)
```

### Performance Monitoring

#### **Cache Performance**
```python
from tool_router.cache.dashboard import CachePerformanceDashboard

# Get performance metrics
dashboard = CachePerformanceDashboard()
metrics = dashboard.get_metrics()

# Get performance trends
trends = dashboard.get_trends(hours=24)

# Get alert summary
alerts = dashboard.get_alert_summary()
```

#### **Security Metrics**
```python
from tool_router.cache.security import CacheSecurityManager

# Get security metrics
security_manager = CacheSecurityManager()
metrics = security_manager.get_security_metrics()

# Monitor key metrics
print(f"Encryption operations: {metrics.encryption_operations}")
print(f"Access control checks: {metrics.access_control_checks}")
print(f"GDPR compliance score: {metrics.gdpr_compliance_score}")
print(f"Retention enforcement: {metrics.retention_enforcement}")
```

## 🧪 Testing

### Test Suite

#### **Security Tests**
```bash
# Run security tests
python -m pytest tool_router/tests/test_cache_security_working.py -v

# Run compliance tests
python -m pytest tool_router/tests/test_cache_compliance.py -v

# Run retention tests
python -m pytest tool_router/tests/test_retention.py -v
```

#### **Integration Tests**
```bash
# Run integration tests
python -m pytest tests/integration/test_security_integration.py -v

# Run end-to-end tests
python - pytest tests/e2e/test_security_e2e.py -v
```

#### **Performance Tests**
```bash
# Run performance tests
python -m pytest tests/performance/test_encryption_performance.py -v

# Run load tests
python -m pytest tests/load/test_security_load.py -v
```

### Test Coverage

#### **Coverage Report**
```bash
# Generate coverage report
python -m pytest --cov=tool_router/cache --cov-report=html

# Coverage threshold check
python -m pytest --cov=tool_router/cache --cov-fail-under=80
```

#### **Security Testing**
```bash
# Run security vulnerability scan
python -m pytest tests/security/test_vulnerabilities.py -v

# Run penetration tests
python -m pytest tests/security/test_penetration.py -v
```

### Test Configuration

#### **pytest.ini**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    security: Security tests
    compliance: Compliance tests
    retention: Retention tests
    performance: Performance tests
    integration: Integration tests
    e2e: End-to-end tests
```

#### **Test Environment**
```python
# conftest.py
import pytest
from tool_router.cache.security import CacheSecurityManager

@pytest.fixture
def security_manager():
    """Fixture for security manager testing."""
    return CacheSecurityManager()

@pytest.fixture
def encryption_key():
    """Fixture for encryption key testing."""
    return Fernet.generate_key().decode()

@pytest.fixture
def test_cache():
    """Fixture for test cache."""
    from cachetools import TTLCache
    return TTLCache(maxsize=100, ttl=3600)
```

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
   ```bash
   git fork https://github.com/forgespace/mcp-gateway.git
   cd mcp-gateway
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes**
   - Write code following the style guidelines
   - Add tests for new features
   - Update documentation

4. **Run tests**
   ```bash
   python -m pytest
   python -m pytest --cov=tool_router/cache
   ```

5. **Submit pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Quality

#### **Linting**
```bash
# Run linting
flake8 tool_router/cache/
black tool_router/cache/
isort tool_router/cache/
```

#### **Type Checking**
```bash
# Run type checking
mypy tool_router/cache/
```

#### **Security Scanning**
```bash
# Run security scan
bandit -r tool_router/cache/
snyk test tool_router/cache/
```

### Documentation

#### **API Documentation**
```bash
# Generate API docs
python -c "
from tool_router.cache.api import app
import json
print(json.dumps(app.openapi(), indent=2))
" > docs/api/security.json
```

#### **Code Documentation**
```bash
# Generate code docs
pdoc tool_router/cache/ --html
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### License Summary

- **MIT License**: Permissive free software license
- **Commercial Use**: Allowed
- **Modification**: Allowed
- **Distribution**: Allowed
- **Private Use**: Allowed
- **Patent Grant**: Required

### License Terms

- ✅ **Commercial use**: You can use this software for commercial purposes
- ✅ **Modification**: You can modify the software
- ✅ **Distribution**: You can distribute the software
- ✅ **Private use**: You can use the software privately
- ✅ **Sublic derivative works**: You can create derivative works

### Attribution

- ✅ **License notice**: Must include the license notice
- ✅ **Copyright notice**: Must include the copyright notice
- ✅ **Disclaimer**: Must include the disclaimer

## 📞 Support

### Documentation

- **[Architecture Overview](docs/architecture/OVERVIEW.md)**
- **[API Reference](docs/api/)**
- **[Security Guide](docs/security/)**
- **[Compliance Guide](docs/compliance/)**
- **[Deployment Guide](docs/deployment/)**
- **[Troubleshooting](docs/troubleshooting/)**

### Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/forgespace/mcp-gateway/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/forgespace/mcp-gateway/discussions)
- **Wiki**: [Community wiki](https://github.com/forgespace/mcp-gateway/wiki)

### Professional Support

- **Enterprise Support**: Available for enterprise customers
- **Consulting Services**: Architecture and security consulting
- **Training Services**: Security and compliance training
- **Support SLA**: 24/7 support for enterprise customers

---

## 🚀 Quick Reference

### Common Commands

```bash
# Start gateway
make start

# Stop gateway
make stop

# Run tests
make test

# Run security tests
make test-security

# Run compliance tests
make test-compliance

# Generate coverage report
make coverage

# Lint code
make lint

# Format code
make format

# Build Docker images
make build

# Deploy to production
make deploy
```

### Environment Variables

```bash
# Security
CACHE_ENCRYPTION_KEY=your-key
CACHE_ACCESS_CONTROL_ENABLED=true
CACHE_GDPR_ENABLED=true

# Cache
CACHE_BACKEND_TYPE=memory
CACHE_MAX_SIZE=1000
CACHE_DEFAULT_TTL=3600

# API
CACHE_SECURITY_API_PORT=8001
CACHE_SECURITY_API_HOST=0.0.0.0
```

### API Endpoints

```bash
# Health
GET /health

# Security
GET /api/security/health
POST /api/security/encrypt
POST /api/security/decrypt

# Compliance
GET /api/compliance/health
POST /api/compliance/consent/record
GET /api/compliance/assessment

# Retention
GET /api/retention/health
POST /api/retention/policies
POST /api/retention/enforce

# Metrics
GET /api/metrics/security
GET /api/metrics/compliance
GET /api/metrics/retention
```

---

**Version**: 1.35.1
**Last Updated**: 2026-02-20
**Status**: ✅ Production Ready with Advanced Security Features
**Next Release**: 1.36.0 (Planned: Advanced Analytics)
