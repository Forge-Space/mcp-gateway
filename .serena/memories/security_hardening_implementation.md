# Security Hardening Implementation

## Purpose
Ensure Serena applies security best practices when editing authentication, authorization, audit logging, and input validation code.

## Key Files
- `SECURITY_IMPLEMENTATION_SUMMARY.md` — Complete security documentation
- `tool_router/security/security_middleware.py` — Main security orchestration
- `tool_router/security/input_validator.py` — Input validation
- `tool_router/security/rate_limiter.py` — Multi-strategy rate limiting
- `tool_router/security/audit_logger.py` — Security audit logging
- `config/security.yaml` — Security configuration

## Architecture

**Prompt Injection Protection**:
- 15+ pattern detection rules
- Risk scoring: 0.0-1.0 scale, threshold 0.5 for blocking
- HTML/JavaScript sanitization using bleach library
- SQL/command injection prevention

**JWT Authentication Flow**:
1. Token generated with 7-day expiration (HS256)
2. Token validated on every request
3. Token refresh supported
4. Secrets encrypted with 32+ character keys
5. HTTPS-only cookies in production

**Rate Limiting (Token Bucket)**:
- Anonymous: 60 req/min, 10 burst
- Authenticated: 120 req/min, 20 burst
- Enterprise: 300 req/min, 50 burst
- Per-user, per-session, per-IP tracking

**Audit Logging**:
- 8 event types: request, blocked, injection, violation, anomaly, authentication, authorization, security
- Severity: Low, Medium, High, Critical
- Structured JSON with request IDs
- Immutable logs with cryptographic signing

## Critical Constraints
- ALL user input MUST be validated before processing
- JWT secrets MUST be 32+ characters
- Rate limit violations MUST trigger automatic penalties
- High-risk requests (score over 0.7) MUST be blocked automatically
- HTTPS MUST be enforced in production
- Security middleware overhead MUST be under 1ms per request
