"""Security audit logging for AI agent requests and responses."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class SecurityEventType(Enum):
    """Types of security events."""

    REQUEST_RECEIVED = "request_received"
    REQUEST_BLOCKED = "request_blocked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHORIZATION_FAILED = "authorization_failed"
    VALIDATION_FAILED = "validation_failed"
    PENALTY_APPLIED = "penalty_applied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"


class SecuritySeverity(Enum):
    """Security event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security audit event."""

    event_id: str
    timestamp: datetime
    event_type: SecurityEventType
    severity: SecuritySeverity
    user_id: str | None
    session_id: str | None
    ip_address: str | None
    user_agent: str | None
    request_id: str | None
    endpoint: str | None
    details: dict[str, Any]
    risk_score: float
    blocked: bool
    metadata: dict[str, Any]


class SecurityAuditLogger:
    """Security audit logging system."""

    def __init__(self, log_file: str | None = None, enable_console: bool = True):
        self.log_file = log_file
        self.enable_console = enable_console
        self._init_logger()

    def _init_logger(self) -> None:
        """Initialize the security audit logger."""
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_security_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        # Convert event to JSON for structured logging
        event_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "request_id": event.request_id,
            "endpoint": event.endpoint,
            "details": event.details,
            "risk_score": event.risk_score,
            "blocked": event.blocked,
            "metadata": event.metadata,
        }

        # Log the event
        log_message = f"SECURITY_EVENT: {json.dumps(event_data)}"

        if event.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]:
            self.logger.error(log_message)
        elif event.severity == SecuritySeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def log_request_received(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        request_id: str | None,
        endpoint: str | None,
        details: dict[str, Any],
    ) -> str:
        """Log a received request."""
        event_id = str(uuid.uuid4())
        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.REQUEST_RECEIVED,
            severity=SecuritySeverity.LOW,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            endpoint=endpoint,
            details=details,
            risk_score=0.0,
            blocked=False,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_request_blocked(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        request_id: str | None,
        endpoint: str | None,
        reason: str,
        risk_score: float,
        details: dict[str, Any],
    ) -> str:
        """Log a blocked request."""
        event_id = str(uuid.uuid4())
        severity = (
            SecuritySeverity.HIGH if risk_score >= 0.8 else SecuritySeverity.MEDIUM
        )

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.REQUEST_BLOCKED,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            endpoint=endpoint,
            details={"reason": reason, **details},
            risk_score=risk_score,
            blocked=True,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_rate_limit_exceeded(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        request_id: str | None,
        endpoint: str | None,
        limit_type: str,
        current_count: int,
        limit: int,
        details: dict[str, Any],
    ) -> str:
        """Log a rate limit exceeded event."""
        event_id = str(uuid.uuid4())

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SecuritySeverity.MEDIUM,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            request_id=request_id,
            endpoint=endpoint,
            details={
                "limit_type": limit_type,
                "current_count": current_count,
                "limit": limit,
                **details,
            },
            risk_score=0.6,
            blocked=True,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_prompt_injection_detected(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        request_id: str | None,
        endpoint: str | None,
        patterns: list[str],
        risk_score: float,
        details: dict[str, Any],
    ) -> str:
        """Log a prompt injection detection event."""
        event_id = str(uuid.uuid4())
        severity = (
            SecuritySeverity.CRITICAL if risk_score >= 0.8 else SecuritySeverity.HIGH
        )

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            request_id=request_id,
            endpoint=endpoint,
            details={"detected_patterns": patterns, **details},
            risk_score=risk_score,
            blocked=True,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_authentication_failed(
        self,
        user_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        request_id: str | None,
        endpoint: str | None,
        auth_method: str,
        reason: str,
        details: dict[str, Any],
    ) -> str:
        """Log an authentication failure."""
        event_id = str(uuid.uuid4())

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.AUTHENTICATION_FAILED,
            severity=SecuritySeverity.HIGH,
            user_id=user_id,
            session_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            endpoint=endpoint,
            details={"auth_method": auth_method, "reason": reason, **details},
            risk_score=0.7,
            blocked=True,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_authorization_failed(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        request_id: str | None,
        endpoint: str | None,
        required_permission: str,
        user_permissions: list[str],
        details: dict[str, Any],
    ) -> str:
        """Log an authorization failure."""
        event_id = str(uuid.uuid4())

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.AUTHORIZATION_FAILED,
            severity=SecuritySeverity.MEDIUM,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            request_id=request_id,
            endpoint=endpoint,
            details={
                "required_permission": required_permission,
                "user_permissions": user_permissions,
                **details,
            },
            risk_score=0.5,
            blocked=True,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_validation_failed(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        request_id: str | None,
        endpoint: str | None,
        validation_type: str,
        violations: list[str],
        risk_score: float,
        details: dict[str, Any],
    ) -> str:
        """Log a validation failure."""
        event_id = str(uuid.uuid4())
        severity = (
            SecuritySeverity.HIGH if risk_score >= 0.7 else SecuritySeverity.MEDIUM
        )

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.VALIDATION_FAILED,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            request_id=request_id,
            endpoint=endpoint,
            details={
                "validation_type": validation_type,
                "violations": violations,
                **details,
            },
            risk_score=risk_score,
            blocked=True,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_penalty_applied(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        request_id: str | None,
        endpoint: str | None,
        penalty_type: str,
        duration: int,
        reason: str,
        details: dict[str, Any],
    ) -> str:
        """Log a penalty application."""
        event_id = str(uuid.uuid4())

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.PENALTY_APPLIED,
            severity=SecuritySeverity.MEDIUM,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            request_id=request_id,
            endpoint=endpoint,
            details={
                "penalty_type": penalty_type,
                "duration": duration,
                "reason": reason,
                **details,
            },
            risk_score=0.6,
            blocked=False,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def log_suspicious_activity(
        self,
        user_id: str | None,
        session_id: str | None,
        ip_address: str | None,
        request_id: str | None,
        endpoint: str | None,
        activity_type: str,
        risk_score: float,
        details: dict[str, Any],
    ) -> str:
        """Log suspicious activity."""
        event_id = str(uuid.uuid4())
        severity = (
            SecuritySeverity.HIGH if risk_score >= 0.7 else SecuritySeverity.MEDIUM
        )

        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=None,
            request_id=request_id,
            endpoint=endpoint,
            details={"activity_type": activity_type, **details},
            risk_score=risk_score,
            blocked=risk_score >= 0.8,
            metadata={},
        )

        self.log_security_event(event)
        return event_id

    def get_security_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get security summary for the last N hours."""
        # This would typically query a database or log aggregation system
        # For now, return a placeholder summary
        return {
            "period_hours": hours,
            "total_events": 0,
            "blocked_requests": 0,
            "high_risk_events": 0,
            "critical_events": 0,
            "top_event_types": [],
            "top_ip_addresses": [],
            "risk_trends": [],
        }

    def create_request_hash(self, request_data: dict[str, Any]) -> str:
        """Create a hash for request deduplication."""
        # Create a normalized string representation
        normalized_data = json.dumps(
            request_data, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(normalized_data.encode()).hexdigest()[:16]
