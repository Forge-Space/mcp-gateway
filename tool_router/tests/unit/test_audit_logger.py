"""Unit tests for tool_router/security/audit_logger.py module."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from tool_router.security.audit_logger import (
    SecurityAuditLogger,
    SecurityEvent,
    SecurityEventType,
    SecuritySeverity,
)


class TestSecurityAuditLogger:
    """Test cases for SecurityAuditLogger functionality."""

    def test_initialization_with_file(self, tmp_path: Path) -> None:
        """Test SecurityAuditLogger initialization with log file."""
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file=str(log_file), enable_console=True)

        assert logger.log_file == str(log_file)
        assert logger.enable_console is True
        assert logger.logger is not None
        assert logger.logger.name == "security_audit"
        assert logger.logger.level == logging.INFO

    def test_initialization_console_only(self) -> None:
        """Test SecurityAuditLogger initialization with console only."""
        logger = SecurityAuditLogger(log_file=None, enable_console=True)

        assert logger.log_file is None
        assert logger.enable_console is True
        assert len(logger.logger.handlers) == 1
        assert isinstance(logger.logger.handlers[0], logging.StreamHandler)

    def test_initialization_file_only(self, tmp_path: Path) -> None:
        """Test SecurityAuditLogger initialization with file only."""
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file=str(log_file), enable_console=False)

        assert logger.log_file == str(log_file)
        assert logger.enable_console is False
        assert len(logger.logger.handlers) == 1
        assert isinstance(logger.logger.handlers[0], logging.FileHandler)

    def test_initialization_both_handlers(self, tmp_path: Path) -> None:
        """Test SecurityAuditLogger initialization with both console and file."""
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file=str(log_file), enable_console=True)

        assert len(logger.logger.handlers) == 2
        handler_types = [type(h) for h in logger.logger.handlers]
        assert logging.StreamHandler in handler_types
        assert logging.FileHandler in handler_types

    def test_log_security_event_low_severity(self) -> None:
        """Test logging a low severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        event = SecurityEvent(
            event_id="test-123",
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.REQUEST_RECEIVED,
            severity=SecuritySeverity.LOW,
            user_id="user123",
            session_id="session123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-123",
            endpoint="/api/tools",
            details={"action": "test"},
            risk_score=0.0,
            blocked=False,
            metadata={"key": "value"},
        )

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_security_event(event)
            mock_info.assert_called_once()

            # Verify the logged message contains expected data
            call_args = mock_info.call_args[0][0]
            assert "SECURITY_EVENT:" in call_args
            event_data = json.loads(call_args.replace("SECURITY_EVENT: ", ""))
            assert event_data["event_id"] == "test-123"
            assert event_data["event_type"] == "request_received"
            assert event_data["severity"] == "low"

    def test_log_security_event_medium_severity(self) -> None:
        """Test logging a medium severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        event = SecurityEvent(
            event_id="test-456",
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SecuritySeverity.MEDIUM,
            user_id="user456",
            session_id=None,
            ip_address="192.168.1.2",
            user_agent=None,
            request_id="req-456",
            endpoint="/api/tools",
            details={"limit": 100},
            risk_score=0.6,
            blocked=True,
            metadata={},
        )

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.log_security_event(event)
            mock_warning.assert_called_once()

    def test_log_security_event_high_severity(self) -> None:
        """Test logging a high severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        event = SecurityEvent(
            event_id="test-789",
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.AUTHENTICATION_FAILED,
            severity=SecuritySeverity.HIGH,
            user_id="user789",
            session_id=None,
            ip_address="192.168.1.3",
            user_agent="Mozilla/5.0",
            request_id="req-789",
            endpoint="/api/auth",
            details={"reason": "invalid_password"},
            risk_score=0.7,
            blocked=True,
            metadata={},
        )

        with patch.object(logger.logger, "error") as mock_error:
            logger.log_security_event(event)
            mock_error.assert_called_once()

    def test_log_security_event_critical_severity(self) -> None:
        """Test logging a critical severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        event = SecurityEvent(
            event_id="test-critical",
            timestamp=datetime.now(UTC),
            event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
            severity=SecuritySeverity.CRITICAL,
            user_id="user-critical",
            session_id="session-critical",
            ip_address="192.168.1.4",
            user_agent=None,
            request_id="req-critical",
            endpoint="/api/chat",
            details={"patterns": ["<script>", "javascript:"], "risk_score": 0.9},
            risk_score=0.9,
            blocked=True,
            metadata={},
        )

        with patch.object(logger.logger, "error") as mock_error:
            logger.log_security_event(event)
            mock_error.assert_called_once()

    def test_log_request_received(self) -> None:
        """Test request received logging."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_received(
                user_id="user123",
                session_id="session123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                request_id="req-123",
                endpoint="/api/tools",
                details={"tool": "read_file"},
            )

            assert event_id is not None
            mock_log.assert_called_once()

            # Verify the event structure
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.REQUEST_RECEIVED
            assert event.severity == SecuritySeverity.LOW
            assert event.user_id == "user123"
            assert event.ip_address == "192.168.1.1"
            assert event.risk_score == 0.0
            assert event.blocked is False

    def test_log_request_blocked_high_risk(self) -> None:
        """Test request blocked logging with high risk."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_blocked(
                user_id="user456",
                session_id="session456",
                ip_address="192.168.1.2",
                user_agent="Mozilla/5.0",
                request_id="req-456",
                endpoint="/api/admin",
                reason="Rate limit exceeded",
                risk_score=0.8,
                details={"limit": 100, "current": 150},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.REQUEST_BLOCKED
            assert event.severity == SecuritySeverity.HIGH  # High risk >= 0.8
            assert event.blocked is True
            assert event.risk_score == 0.8

    def test_log_request_blocked_medium_risk(self) -> None:
        """Test request blocked logging with medium risk."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_blocked(
                user_id="user789",
                session_id="session789",
                ip_address="192.168.1.3",
                user_agent=None,
                request_id="req-789",
                endpoint="/api/tools",
                reason="Suspicious activity",
                risk_score=0.6,
                details={"pattern": "rapid_requests"},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.REQUEST_BLOCKED
            assert event.severity == SecuritySeverity.MEDIUM  # Medium risk < 0.8

    def test_log_rate_limit_exceeded(self) -> None:
        """Test rate limit exceeded logging."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_rate_limit_exceeded(
                user_id="user-rate",
                session_id="session-rate",
                ip_address="192.168.1.100",
                request_id="req-rate",
                endpoint="/api/tools",
                limit_type="requests_per_minute",
                current_count=150,
                limit=100,
                details={"window": "60s"},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
            assert event.severity == SecuritySeverity.MEDIUM
            assert event.risk_score == 0.6
            assert event.blocked is True
            assert event.details["limit_type"] == "requests_per_minute"
            assert event.details["current_count"] == 150
            assert event.details["limit"] == 100

    def test_log_prompt_injection_detected_critical(self) -> None:
        """Test prompt injection detection with critical severity."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_prompt_injection_detected(
                user_id="user-inject",
                session_id="session-inject",
                ip_address="192.168.1.200",
                request_id="req-inject",
                endpoint="/api/chat",
                patterns=["<script>", "javascript:", "data:"],
                risk_score=0.9,
                details={"prompt_length": 1000},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.PROMPT_INJECTION_DETECTED
            assert event.severity == SecuritySeverity.CRITICAL  # Critical risk >= 0.8
            assert event.blocked is True

    def test_log_prompt_injection_detected_high(self) -> None:
        """Test prompt injection detection with high severity."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_prompt_injection_detected(
                user_id="user-inject2",
                session_id="session-inject2",
                ip_address="192.168.1.201",
                request_id="req-inject2",
                endpoint="/api/chat",
                patterns=["DROP TABLE"],
                risk_score=0.7,
                details={"prompt_length": 500},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.PROMPT_INJECTION_DETECTED
            assert event.severity == SecuritySeverity.HIGH  # High risk < 0.8

    def test_log_authentication_failed(self) -> None:
        """Test authentication failure logging."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_authentication_failed(
                user_id="user-auth",
                ip_address="192.168.1.300",
                user_agent="Mozilla/5.0",
                request_id="req-auth",
                endpoint="/api/login",
                auth_method="password",
                reason="Invalid credentials",
                details={"attempts": 3},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.AUTHENTICATION_FAILED
            assert event.severity == SecuritySeverity.HIGH
            assert event.risk_score == 0.7
            assert event.blocked is True
            assert event.session_id is None  # Not set for auth failures

    def test_log_authorization_failed(self) -> None:
        """Test authorization failure logging."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_authorization_failed(
                user_id="user-authz",
                session_id="session-authz",
                ip_address="192.168.1.400",
                request_id="req-authz",
                endpoint="/api/admin",
                required_permission="admin:access",
                user_permissions=["user:read", "user:write"],
                details={"resource": "user_data"},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.AUTHORIZATION_FAILED
            assert event.severity == SecuritySeverity.MEDIUM
            assert event.risk_score == 0.5
            assert event.blocked is True

    def test_log_validation_failed_high_risk(self) -> None:
        """Test validation failure logging with high risk."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_validation_failed(
                user_id="user-val",
                session_id="session-val",
                ip_address="192.168.1.500",
                request_id="req-val",
                endpoint="/api/tools",
                validation_type="input_validation",
                violations=["missing_required_field", "invalid_format"],
                risk_score=0.8,
                details={"field": "tool_name"},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.VALIDATION_FAILED
            assert event.severity == SecuritySeverity.HIGH  # High risk >= 0.7

    def test_log_validation_failed_medium_risk(self) -> None:
        """Test validation failure logging with medium risk."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_validation_failed(
                user_id="user-val2",
                session_id="session-val2",
                ip_address="192.168.1.501",
                request_id="req-val2",
                endpoint="/api/tools",
                validation_type="schema_validation",
                violations=["additional_property"],
                risk_score=0.5,
                details={"field": "extra_data"},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.VALIDATION_FAILED
            assert event.severity == SecuritySeverity.MEDIUM  # Medium risk < 0.7

    def test_log_penalty_applied(self) -> None:
        """Test penalty application logging."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_penalty_applied(
                user_id="user-penalty",
                session_id="session-penalty",
                ip_address="192.168.1.600",
                request_id="req-penalty",
                endpoint="/api/tools",
                penalty_type="rate_limit",
                duration=300,
                reason="Too many requests",
                details={"previous_violations": 5},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.PENALTY_APPLIED
            assert event.severity == SecuritySeverity.MEDIUM
            assert event.risk_score == 0.6
            assert event.blocked is False  # Penalties don't block by default

    def test_log_suspicious_activity_high_risk(self) -> None:
        """Test suspicious activity logging with high risk."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_suspicious_activity(
                user_id="user-suspicious",
                session_id="session-suspicious",
                ip_address="192.168.1.700",
                request_id="req-suspicious",
                endpoint="/api/tools",
                activity_type="rapid_tool_requests",
                risk_score=0.8,
                details={"request_count": 50, "time_window": "60s"},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
            assert event.severity == SecuritySeverity.HIGH  # High risk >= 0.7
            assert event.blocked is True  # High risk suspicious activity blocks

    def test_log_suspicious_activity_medium_risk(self) -> None:
        """Test suspicious activity logging with medium risk."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_suspicious_activity(
                user_id="user-suspicious2",
                session_id="session-suspicious2",
                ip_address="192.168.1.701",
                request_id="req-suspicious2",
                endpoint="/api/tools",
                activity_type="unusual_time_pattern",
                risk_score=0.6,
                details={"time": "03:00:00", "timezone": "UTC"},
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
            assert event.severity == SecuritySeverity.MEDIUM  # Medium risk < 0.7
            assert event.blocked is False  # Medium risk doesn't block

    def test_get_security_summary(self) -> None:
        """Test security summary generation."""
        logger = SecurityAuditLogger(enable_console=False)

        summary = logger.get_security_summary(hours=24)

        assert isinstance(summary, dict)
        assert summary["period_hours"] == 24
        assert summary["total_events"] == 0  # Placeholder implementation
        assert summary["blocked_requests"] == 0
        assert summary["high_risk_events"] == 0
        assert summary["critical_events"] == 0
        assert summary["top_event_types"] == []
        assert summary["top_ip_addresses"] == []
        assert summary["risk_trends"] == []

    def test_get_security_summary_custom_hours(self) -> None:
        """Test security summary with custom hours."""
        logger = SecurityAuditLogger(enable_console=False)

        summary = logger.get_security_summary(hours=48)

        assert summary["period_hours"] == 48

    def test_create_request_hash_consistency(self) -> None:
        """Test request hash creation produces consistent results."""
        logger = SecurityAuditLogger(enable_console=False)

        request_data = {
            "method": "POST",
            "path": "/api/tools",
            "user_id": "user123",
            "body": "test data",
        }

        hash1 = logger.create_request_hash(request_data)
        hash2 = logger.create_request_hash(request_data)

        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of SHA256

    def test_create_request_hash_uniqueness(self) -> None:
        """Test request hash creates different hashes for different data."""
        logger = SecurityAuditLogger(enable_console=False)

        request_data1 = {"method": "POST", "path": "/api/tools", "user_id": "user123"}
        request_data2 = {"method": "POST", "path": "/api/tools", "user_id": "user456"}

        hash1 = logger.create_request_hash(request_data1)
        hash2 = logger.create_request_hash(request_data2)

        assert hash1 != hash2

    def test_create_request_hash_order_independence(self) -> None:
        """Test request hash is independent of key order."""
        logger = SecurityAuditLogger(enable_console=False)

        request_data1 = {"a": "1", "b": "2", "c": "3"}
        request_data2 = {"c": "3", "a": "1", "b": "2"}

        hash1 = logger.create_request_hash(request_data1)
        hash2 = logger.create_request_hash(request_data2)

        assert hash1 == hash2

    def test_security_event_dataclass(self) -> None:
        """Test SecurityEvent dataclass functionality."""
        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="test-event",
            timestamp=timestamp,
            event_type=SecurityEventType.REQUEST_RECEIVED,
            severity=SecuritySeverity.LOW,
            user_id="user123",
            session_id="session123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-123",
            endpoint="/api/test",
            details={"key": "value"},
            risk_score=0.0,
            blocked=False,
            metadata={"meta": "data"},
        )

        assert event.event_id == "test-event"
        assert event.timestamp == timestamp
        assert event.event_type == SecurityEventType.REQUEST_RECEIVED
        assert event.severity == SecuritySeverity.LOW
        assert event.user_id == "user123"
        assert event.session_id == "session123"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"
        assert event.request_id == "req-123"
        assert event.endpoint == "/api/test"
        assert event.details == {"key": "value"}
        assert event.risk_score == 0.0
        assert event.blocked is False
        assert event.metadata == {"meta": "data"}

    def test_security_event_enums(self) -> None:
        """Test security event enums."""
        # Test SecurityEventType
        assert SecurityEventType.REQUEST_RECEIVED.value == "request_received"
        assert SecurityEventType.REQUEST_BLOCKED.value == "request_blocked"
        assert SecurityEventType.RATE_LIMIT_EXCEEDED.value == "rate_limit_exceeded"
        assert SecurityEventType.PROMPT_INJECTION_DETECTED.value == "prompt_injection_detected"
        assert SecurityEventType.AUTHENTICATION_FAILED.value == "authentication_failed"
        assert SecurityEventType.AUTHORIZATION_FAILED.value == "authorization_failed"
        assert SecurityEventType.VALIDATION_FAILED.value == "validation_failed"
        assert SecurityEventType.PENALTY_APPLIED.value == "penalty_applied"
        assert SecurityEventType.SUSPICIOUS_ACTIVITY.value == "suspicious_activity"
        assert SecurityEventType.SECURITY_POLICY_VIOLATION.value == "security_policy_violation"

        # Test SecuritySeverity
        assert SecuritySeverity.LOW.value == "low"
        assert SecuritySeverity.MEDIUM.value == "medium"
        assert SecuritySeverity.HIGH.value == "high"
        assert SecuritySeverity.CRITICAL.value == "critical"

    def test_logger_handler_configuration(self) -> None:
        """Test logger handler configuration."""
        logger = SecurityAuditLogger(enable_console=True)

        # Verify formatter is applied
        for handler in logger.logger.handlers:
            assert isinstance(handler.formatter, logging.Formatter)
            fmt = handler.formatter._fmt
            assert fmt is not None
            assert "%(asctime)s" in fmt
            assert "%(name)s" in fmt
            assert "%(levelname)s" in fmt
            assert "%(message)s" in fmt

    def test_event_id_generation(self) -> None:
        """Test that event IDs are unique UUIDs."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event"):
            event_id1 = logger.log_request_received(
                user_id="user1",
                session_id="session1",
                ip_address="192.168.1.1",
                user_agent=None,
                request_id="req1",
                endpoint="/api/test",
                details={},
            )

            event_id2 = logger.log_request_received(
                user_id="user2",
                session_id="session2",
                ip_address="192.168.1.2",
                user_agent=None,
                request_id="req2",
                endpoint="/api/test",
                details={},
            )

            assert event_id1 != event_id2
            assert len(event_id1) > 0
            assert len(event_id2) > 0
