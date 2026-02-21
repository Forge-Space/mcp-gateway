"""Main security middleware for AI agent requests."""

import json
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass

from .input_validator import InputValidator, SecurityValidationResult, ValidationLevel
from .rate_limiter import RateLimiter, RateLimitConfig, RateLimitResult
from .audit_logger import SecurityAuditLogger, SecurityEventType, SecuritySeverity


@dataclass
class SecurityContext:
    """Security context for a request."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    authentication_method: Optional[str] = None
    user_role: Optional[str] = None


@dataclass
class SecurityCheckResult:
    """Result of security checks."""
    allowed: bool
    risk_score: float
    violations: list[str]
    sanitized_inputs: Dict[str, str]
    metadata: Dict[str, Any]
    blocked_reason: Optional[str] = None


class SecurityMiddleware:
    """Main security middleware orchestrating all security components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.strict_mode = config.get("strict_mode", False)
        
        # Initialize security components
        validation_level = ValidationLevel(config.get("validation_level", "standard"))
        self.input_validator = InputValidator(validation_level)
        
        # Rate limiter configuration
        rate_limit_config = config.get("rate_limiting", {})
        self.rate_limiter = RateLimiter(
            use_redis=rate_limit_config.get("use_redis", False),
            redis_url=rate_limit_config.get("redis_url")
        )
        
        # Audit logger
        audit_config = config.get("audit_logging", {})
        self.audit_logger = SecurityAuditLogger(
            log_file=audit_config.get("log_file"),
            enable_console=audit_config.get("enable_console", True)
        )
        
        # Default rate limit configurations
        self.default_rate_limit = RateLimitConfig(
            requests_per_minute=rate_limit_config.get("default", {}).get("requests_per_minute", 60),
            requests_per_hour=rate_limit_config.get("default", {}).get("requests_per_hour", 1000),
            requests_per_day=rate_limit_config.get("default", {}).get("requests_per_day", 10000),
            burst_capacity=rate_limit_config.get("default", {}).get("burst_capacity", 10),
            penalty_duration=rate_limit_config.get("penalty_duration", 300)
        )
        
        self.authenticated_rate_limit = RateLimitConfig(
            requests_per_minute=rate_limit_config.get("authenticated_user", {}).get("requests_per_minute", 120),
            requests_per_hour=rate_limit_config.get("authenticated_user", {}).get("requests_per_hour", 2000),
            requests_per_day=rate_limit_config.get("authenticated_user", {}).get("requests_per_day", 20000),
            burst_capacity=rate_limit_config.get("authenticated_user", {}).get("burst_capacity", 20),
            penalty_duration=rate_limit_config.get("penalty_duration", 300)
        )
        
        self.enterprise_rate_limit = RateLimitConfig(
            requests_per_minute=rate_limit_config.get("enterprise_user", {}).get("requests_per_minute", 300),
            requests_per_hour=rate_limit_config.get("enterprise_user", {}).get("requests_per_hour", 5000),
            requests_per_day=rate_limit_config.get("enterprise_user", {}).get("requests_per_day", 50000),
            burst_capacity=rate_limit_config.get("enterprise_user", {}).get("burst_capacity", 50),
            penalty_duration=rate_limit_config.get("penalty_duration", 300)
        )
    
    def check_request_security(self, context: SecurityContext, 
                               task: str, category: str, context_str: str,
                               user_preferences: str) -> SecurityCheckResult:
        """Perform comprehensive security checks on a request."""
        if not self.enabled:
            return SecurityCheckResult(
                allowed=True,
                risk_score=0.0,
                violations=[],
                sanitized_inputs={"task": task, "context": context_str, "user_preferences": user_preferences},
                metadata={"security_disabled": True}
            )
        
        violations = []
        risk_score = 0.0
        sanitized_inputs = {}
        metadata = {}
        blocked_reason = None
        
        # Generate request ID if not provided
        if not context.request_id:
            context.request_id = f"req_{int(time.time())}_{hash(context.ip_address or 'unknown') % 10000}"
        
        # Log request received
        self.audit_logger.log_request_received(
            user_id=context.user_id,
            session_id=context.session_id,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            request_id=context.request_id,
            endpoint=context.endpoint,
            details={"category": category, "task_length": len(task)}
        )
        
        # Input validation
        prompt_result = self.input_validator.validate_prompt(task, context_str)
        sanitized_inputs["task"] = prompt_result.sanitized_input
        sanitized_inputs["context"] = context_str  # Context is validated within prompt validation
        
        violations.extend(prompt_result.violations)
        risk_score += prompt_result.risk_score
        
        if prompt_result.blocked:
            violations.append("Prompt blocked by security validation")
            risk_score = max(risk_score, 0.8)
            blocked_reason = "Prompt contains suspicious content"
            
            self.audit_logger.log_request_blocked(
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                request_id=context.request_id,
                endpoint=context.endpoint,
                reason=blocked_reason,
                risk_score=risk_score,
                details={"violations": prompt_result.violations}
            )
        
        # User preferences validation
        prefs_result = self.input_validator.validate_user_preferences(user_preferences)
        sanitized_inputs["user_preferences"] = prefs_result.sanitized_input
        
        violations.extend(prefs_result.violations)
        risk_score += prefs_result.risk_score * 0.5  # Lower weight for preferences
        
        if prefs_result.blocked:
            violations.append("User preferences blocked by security validation")
            risk_score = max(risk_score, 0.6)
            if not blocked_reason:
                blocked_reason = "User preferences contain suspicious content"
        
        # Rate limiting
        identifier = self._get_rate_limit_identifier(context)
        rate_limit_config = self._get_rate_limit_config(context)
        
        rate_limit_result = self.rate_limiter.check_rate_limit(identifier, rate_limit_config)
        
        if not rate_limit_result.allowed:
            violations.append("Rate limit exceeded")
            risk_score = max(risk_score, 0.7)
            if not blocked_reason:
                blocked_reason = f"Rate limit exceeded: {rate_limit_result.metadata.get('window_type', 'unknown')}"
            
            self.audit_logger.log_rate_limit_exceeded(
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                request_id=context.request_id,
                endpoint=context.endpoint,
                limit_type=rate_limit_result.metadata.get('window_type', 'unknown'),
                current_count=rate_limit_result.metadata.get('current_count', 0),
                limit=rate_limit_result.metadata.get('max_requests', 0),
                details={"retry_after": rate_limit_result.retry_after}
            )
        
        # Check for prompt injection patterns specifically
        if self.config.get("prompt_injection", {}).get("enabled", True):
            injection_patterns = self._detect_prompt_injection_patterns(prompt_result.sanitized_input)
            if injection_patterns:
                violations.append("Prompt injection patterns detected")
                risk_score = max(risk_score, 0.9)
                blocked_reason = "Prompt injection attempt detected"
                
                self.audit_logger.log_prompt_injection_detected(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    ip_address=context.ip_address,
                    request_id=context.request_id,
                    endpoint=context.endpoint,
                    patterns=injection_patterns,
                    risk_score=risk_score,
                    details={"sanitized_prompt": prompt_result.sanitized_input[:200] + "..."}
                )
        
        # Apply strict mode rules
        if self.strict_mode and risk_score > 0.3:
            violations.append("Strict mode: risk score too high")
            blocked_reason = "Strict mode security policy violation"
            risk_score = max(risk_score, 0.8)
        
        # Determine if request should be blocked
        blocked = (
            blocked_reason is not None or
            risk_score >= 0.8 or
            len(violations) > 5 or
            (self.strict_mode and risk_score > 0.5)
        )
        
        # Log suspicious activity
        if 0.5 <= risk_score < 0.8 and not blocked:
            self.audit_logger.log_suspicious_activity(
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                request_id=context.request_id,
                endpoint=context.endpoint,
                activity_type="high_risk_request",
                risk_score=risk_score,
                details={"violations": violations, "risk_score": risk_score}
            )
        
        # Apply penalty if risk is high
        if risk_score >= 0.7 and not blocked:
            penalty_duration = int(300 * risk_score)  # Scale penalty with risk
            self.rate_limiter.apply_penalty(identifier, penalty_duration)
            
            self.audit_logger.log_penalty_applied(
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                request_id=context.request_id,
                endpoint=context.endpoint,
                penalty_type="high_risk_penalty",
                duration=penalty_duration,
                reason=f"High risk score: {risk_score:.2f}",
                details={"violations": violations}
            )
        
        # Update metadata
        metadata.update({
            "validation_results": {
                "prompt": {"valid": prompt_result.is_valid, "risk": prompt_result.risk_score},
                "preferences": {"valid": prefs_result.is_valid, "risk": prefs_result.risk_score}
            },
            "rate_limit": {
                "allowed": rate_limit_result.allowed,
                "remaining": rate_limit_result.remaining,
                "retry_after": rate_limit_result.retry_after
            },
            "security_level": self.config.get("validation_level", "standard"),
            "strict_mode": self.strict_mode
        })
        
        return SecurityCheckResult(
            allowed=not blocked,
            risk_score=min(risk_score, 1.0),
            violations=violations,
            sanitized_inputs=sanitized_inputs,
            metadata=metadata,
            blocked_reason=blocked_reason
        )
    
    def _get_rate_limit_identifier(self, context: SecurityContext) -> str:
        """Get identifier for rate limiting."""
        # Priority: user_id > session_id > ip_address
        if context.user_id:
            return f"user:{context.user_id}"
        elif context.session_id:
            return f"session:{context.session_id}"
        elif context.ip_address:
            return f"ip:{context.ip_address}"
        else:
            return "anonymous"
    
    def _get_rate_limit_config(self, context: SecurityContext) -> RateLimitConfig:
        """Get rate limit configuration based on user context."""
        if context.user_role == "enterprise":
            return self.enterprise_rate_limit
        elif context.user_id:  # Authenticated user
            return self.authenticated_rate_limit
        else:
            return self.default_rate_limit
    
    def _detect_prompt_injection_patterns(self, prompt: str) -> list[str]:
        """Detect prompt injection patterns in the prompt."""
        injection_patterns = []
        
        # Additional injection patterns not caught by general validation
        injection_checks = [
            r'(?i)(ignore|forget|disregard).*(previous|above|system).*(prompt|instruction)',
            r'(?i)(you are|act as|pretend to be).*(not|no longer).*(an? )?(ai|assistant)',
            r'(?i)(new|different|changed).*(role|persona|character)',
            r'(?i)(instead|rather|alternatively).*(do|perform|execute)',
            r'(?i)(stop|cease|halt).*(following|obeying)',
            r'(?i)(override|bypass|ignore).*(rules|guidelines|restrictions)',
            r'(?i)(###|---|\*\*\*|===).*(end|stop|finish)',
            r'(?i)(\\n\\n|\\r\\n|\\t).*(new|separate|different)',
        ]
        
        import re
        for pattern in injection_checks:
            if re.search(pattern, prompt):
                injection_patterns.append(pattern)
        
        return injection_patterns
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        return {
            "enabled": self.enabled,
            "strict_mode": self.strict_mode,
            "validation_level": self.input_validator.validation_level.value,
            "rate_limiting": {
                "default": self.default_rate_limit.__dict__,
                "authenticated": self.authenticated_rate_limit.__dict__,
                "enterprise": self.enterprise_rate_limit.__dict__
            },
            "audit_summary": self.audit_logger.get_security_summary()
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update security configuration."""
        self.config.update(new_config)
        
        # Reinitialize components if needed
        if "validation_level" in new_config:
            validation_level = ValidationLevel(new_config["validation_level"])
            self.input_validator = InputValidator(validation_level)
        
        if "rate_limiting" in new_config:
            rate_limit_config = new_config["rate_limiting"]
            if "default" in rate_limit_config:
                self.default_rate_limit = RateLimitConfig(**rate_limit_config["default"])
            if "authenticated_user" in rate_limit_config:
                self.authenticated_rate_limit = RateLimitConfig(**rate_limit_config["authenticated_user"])
            if "enterprise_user" in rate_limit_config:
                self.enterprise_rate_limit = RateLimitConfig(**rate_limit_config["enterprise_user"])
