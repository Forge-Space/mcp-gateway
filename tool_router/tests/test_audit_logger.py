"""Tests for tool_router.security.audit_logger module."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from tool_router.security.audit_logger import (
    SecurityAuditLogger,
    SecurityEvent,
    SecurityEventType,
    SecuritySeverity,
)


class TestSecurityEventType:
    """Test cases for SecurityEventType enum."""

    def test_security_event_type_values(self):
        """Test that SecurityEventType has expected values."""
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

    def test_security_event_type_count(self):
        """Test number of security event types."""
        assert len(SecurityEventType) == 10


class TestSecuritySeverity:
    """Test cases for SecuritySeverity enum."""

    def test_security_severity_values(self):
        """Test that SecuritySeverity has expected values."""
        assert SecuritySeverity.LOW.value == "low"
        assert SecuritySeverity.MEDIUM.value == "medium"
        assert SecuritySeverity.HIGH.value == "high"
        assert SecuritySeverity.CRITICAL.value == "critical"

    def test_security_severity_count(self):
        """Test number of security severity levels."""
        assert len(SecuritySeverity) == 4


class TestSecurityEvent:
    """Test cases for SecurityEvent dataclass."""

    def test_security_event_creation(self):
        """Test SecurityEvent creation with all fields."""
        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="test-event-123",
            timestamp=timestamp,
            event_type=SecurityEventType.REQUEST_RECEIVED,
            severity=SecuritySeverity.LOW,
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-789",
            endpoint="/api/tools",
            details={"action": "test"},
            risk_score=0.5,
            blocked=False,
            metadata={"extra": "info"},
        )

        assert event.event_id == "test-event-123"
        assert event.timestamp == timestamp
        assert event.event_type == SecurityEventType.REQUEST_RECEIVED
        assert event.severity == SecuritySeverity.LOW
        assert event.user_id == "user123"
        assert event.session_id == "session456"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"
        assert event.request_id == "req-789"
        assert event.endpoint == "/api/tools"
        assert event.details == {"action": "test"}
        assert event.risk_score == 0.5
        assert event.blocked is False
        assert event.metadata == {"extra": "info"}

    def test_security_event_minimal(self):
        """Test SecurityEvent creation with minimal required fields."""
        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="minimal-event",
            timestamp=timestamp,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecuritySeverity.HIGH,
            user_id=None,
            session_id=None,
            ip_address=None,
            user_agent=None,
            request_id=None,
            endpoint=None,
            details={},
            risk_score=0.9,
            blocked=True,
            metadata={},
        )

        assert event.event_id == "minimal-event"
        assert event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
        assert event.severity == SecuritySeverity.HIGH
        assert event.user_id is None
        assert event.session_id is None
        assert event.ip_address is None
        assert event.user_agent is None
        assert event.request_id is None
        assert event.endpoint is None
        assert event.details == {}
        assert event.risk_score == 0.9
        assert event.blocked is True
        assert event.metadata == {}

    def test_security_event_asdict(self):
        """Test SecurityEvent conversion to dict."""
        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="test-event",
            timestamp=timestamp,
            event_type=SecurityEventType.REQUEST_RECEIVED,
            severity=SecuritySeverity.LOW,
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-789",
            endpoint="/api/tools",
            details={"action": "test"},
            risk_score=0.5,
            blocked=False,
            metadata={"extra": "info"},
        )

        event_dict = event.__dict__

        assert event_dict["event_id"] == "test-event"
        assert event_dict["timestamp"] == timestamp
        assert event_dict["event_type"] == SecurityEventType.REQUEST_RECEIVED
        assert event_dict["severity"] == SecuritySeverity.LOW
        assert event_dict["user_id"] == "user123"
        assert event_dict["session_id"] == "session456"
        assert event_dict["ip_address"] == "192.168.1.1"
        assert event_dict["user_agent"] == "Mozilla/5.0"
        assert event_dict["request_id"] == "req-789"
        assert event_dict["endpoint"] == "/api/tools"
        assert event_dict["details"] == {"action": "test"}
        assert event_dict["risk_score"] == 0.5
        assert event_dict["blocked"] is False
        assert event_dict["metadata"] == {"extra": "info"}


class TestSecurityAuditLogger:
    """Test cases for SecurityAuditLogger."""

    def test_initialization_default(self):
        """Test SecurityAuditLogger initialization with defaults."""
        logger = SecurityAuditLogger()

        assert logger.log_file is None
        assert logger.enable_console is True
        assert logger.logger.name == "security_audit"
        assert len(logger.logger.handlers) == 1  # Only console handler

    def test_initialization_with_file(self):
        """Test SecurityAuditLogger initialization with log file."""
        logger = SecurityAuditLogger(log_file="/tmp/security.log")

        assert logger.log_file == "/tmp/security.log"
        assert logger.enable_console is True
        assert len(logger.logger.handlers) == 2  # Console + file handlers

    def test_initialization_console_disabled(self):
        """Test SecurityAuditLogger initialization with console disabled."""
        logger = SecurityAuditLogger(enable_console=False)

        assert logger.enable_console is False
        assert len(logger.logger.handlers) == 0  # No handlers

    def test_init_logger_setup(self):
        """Test logger initialization setup."""
        logger = SecurityAuditLogger(enable_console=True)

        # Check logger level
        assert logger.logger.level == logging.INFO

        # Check handlers
        assert len(logger.logger.handlers) == 1
        handler = logger.logger.handlers[0]

        # Check formatter
        assert isinstance(handler, logging.StreamHandler)
        assert handler.level == logging.INFO
        assert isinstance(handler.formatter, logging.Formatter)

    @patch("logging.FileHandler")
    @patch("logging.StreamHandler")
    def test_init_logger_with_file(self, mock_stream_handler, mock_file_handler):
        """Test logger initialization with file handler."""
        mock_stream_instance = MagicMock()
        mock_file_instance = MagicMock()
        mock_stream_handler.return_value = mock_stream_instance
        mock_file_handler.return_value = mock_file_instance

        logger = SecurityAuditLogger(log_file="/tmp/test.log")

        # Verify both handlers were created
        mock_stream_handler.assert_called_once()
        mock_file_handler.assert_called_once_with("/tmp/test.log")

        # Verify both handlers were added
        assert len(logger.logger.handlers) == 2

    def test_log_security_event_low_severity(self):
        """Test logging a low severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="test-event",
            timestamp=timestamp,
            event_type=SecurityEventType.REQUEST_RECEIVED,
            severity=SecuritySeverity.LOW,
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-789",
            endpoint="/api/tools",
            details={"action": "test"},
            risk_score=0.1,
            blocked=False,
            metadata={},
        )

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_security_event(event)

            mock_info.assert_called_once()
            args, _kwargs = mock_info.call_args
            assert "SECURITY_EVENT:" in args[0]
            assert "test-event" in args[0]
            assert "low" in args[0]

    def test_log_security_event_medium_severity(self):
        """Test logging a medium severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="test-event",
            timestamp=timestamp,
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SecuritySeverity.MEDIUM,
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            user_agent=None,
            request_id="req-789",
            endpoint="/api/tools",
            details={"limit": 100},
            risk_score=0.5,
            blocked=False,
            metadata={},
        )

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.log_security_event(event)

            mock_warning.assert_called_once()
            args, _kwargs = mock_warning.call_args
            assert "SECURITY_EVENT:" in args[0]
            assert "test-event" in args[0]
            assert "medium" in args[0]

    def test_log_security_event_high_severity(self):
        """Test logging a high severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="test-event",
            timestamp=timestamp,
            event_type=SecurityEventType.REQUEST_BLOCKED,
            severity=SecuritySeverity.HIGH,
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-789",
            endpoint="/api/tools",
            details={"reason": "malicious"},
            risk_score=0.9,
            blocked=True,
            metadata={},
        )

        with patch.object(logger.logger, "error") as mock_error:
            logger.log_security_event(event)

            mock_error.assert_called_once()
            args, _kwargs = mock_error.call_args
            assert "SECURITY_EVENT:" in args[0]
            assert "test-event" in args[0]
            assert "high" in args[0]

    def test_log_security_event_critical_severity(self):
        """Test logging a critical severity security event."""
        logger = SecurityAuditLogger(enable_console=False)

        timestamp = datetime.now(UTC)
        event = SecurityEvent(
            event_id="test-event",
            timestamp=timestamp,
            event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
            severity=SecuritySeverity.CRITICAL,
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-789",
            endpoint="/api/tools",
            details={"injection": "detected"},
            risk_score=1.0,
            blocked=True,
            metadata={},
        )

        with patch.object(logger.logger, "error") as mock_error:
            logger.log_security_event(event)

            mock_error.assert_called_once()
            args, _kwargs = mock_error.call_args
            assert "SECURITY_EVENT:" in args[0]
            assert "test-event" in args[0]
            assert "critical" in args[0]

    def test_log_request_received(self):
        """Test logging a received request."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_received(
                user_id="user123",
                session_id="session456",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                request_id="req-789",
                endpoint="/api/tools",
                details={"action": "test"},
            )

            # Verify event ID is returned
            assert event_id is not None
            assert len(event_id) > 0

            # Verify log_security_event was called
            mock_log.assert_called_once()
            event_arg = mock_log.call_args[0][0]
            assert event_arg.event_type == SecurityEventType.REQUEST_RECEIVED
            assert event_arg.severity == SecuritySeverity.LOW
            assert event_arg.user_id == "user123"
            assert event_arg.session_id == "session456"
            assert event_arg.ip_address == "192.168.1.1"
            assert event_arg.user_agent == "Mozilla/5.0"
            assert event_arg.request_id == "req-789"
            assert event_arg.endpoint == "/api/tools"
            assert event_arg.details == {"action": "test"}
            assert event_arg.risk_score == 0.0
            assert event_arg.blocked is False

    def test_log_request_received_minimal(self):
        """Test logging a received request with minimal data."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_received(
                user_id=None,
                session_id=None,
                ip_address=None,
                user_agent=None,
                request_id=None,
                endpoint=None,
                details={},
            )

            # Verify event ID is returned
            assert event_id is not None

            # Verify log_security_event was called
            mock_log.assert_called_once()
            event_arg = mock_log.call_args[0][0]
            assert event_arg.event_type == SecurityEventType.REQUEST_RECEIVED
            assert event_arg.severity == SecuritySeverity.LOW
            assert event_arg.user_id is None
            assert event_arg.session_id is None
            assert event_arg.ip_address is None
            assert event_arg.user_agent is None
            assert event_arg.request_id is None
            assert event_arg.endpoint is None
            assert event_arg.details == {}
            assert event_arg.risk_score == 0.0
            assert event_arg.blocked is False

    def test_log_request_blocked_high_risk(self):
        """Test logging a blocked request with high risk score."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_blocked(
                user_id="user123",
                session_id="session456",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                request_id="req-789",
                endpoint="/api/tools",
                reason="malicious payload",
                risk_score=0.9,
                details={"payload": "test"},
            )

            # Verify event ID is returned
            assert event_id is not None

            # Verify log_security_event was called
            mock_log.assert_called_once()
            event_arg = mock_log.call_args[0][0]
            assert event_arg.event_type == SecurityEventType.REQUEST_BLOCKED
            assert event_arg.severity == SecuritySeverity.HIGH
            assert event_arg.user_id == "user123"
            assert event_arg.session_id == "session456"
            assert event_arg.ip_address == "192.168.1.1"
            assert event_arg.user_agent == "Mozilla/5.0"
            assert event_arg.request_id == "req-789"
            assert event_arg.endpoint == "/api/tools"
            assert event_arg.details["reason"] == "malicious payload"
            assert event_arg.details["payload"] == "test"
            assert event_arg.risk_score == 0.9
            assert event_arg.blocked is True

    def test_log_request_blocked_medium_risk(self):
        """Test logging a blocked request with medium risk score."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_blocked(
                user_id="user123",
                session_id="session456",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                request_id="req-789",
                endpoint="/api/tools",
                reason="suspicious pattern",
                risk_score=0.6,
                details={"pattern": "test"},
            )

            # Verify event ID is returned
            assert event_id is not None

            # Verify log_security_event was called
            mock_log.assert_called_once()
            event_arg = mock_log.call_args[0][0]
            assert event_arg.event_type == SecurityEventType.REQUEST_BLOCKED
            assert event_arg.severity == SecuritySeverity.MEDIUM
            assert event_arg.risk_score == 0.6
            assert event_arg.blocked is True

    def test_log_request_blocked_minimal(self):
        """Test logging a blocked request with minimal data."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_request_blocked(
                user_id=None,
                session_id=None,
                ip_address=None,
                user_agent=None,
                request_id=None,
                endpoint=None,
                reason="test reason",
                risk_score=0.5,
                details={},
            )

            # Verify event ID is returned
            assert event_id is not None

            # Verify log_security_event was called
            mock_log.assert_called_once()
            event_arg = mock_log.call_args[0][0]
            assert event_arg.event_type == SecurityEventType.REQUEST_BLOCKED
            assert event_arg.severity == SecuritySeverity.MEDIUM
            assert event_arg.risk_score == 0.5
            assert event_arg.blocked is True

    def test_log_rate_limit_exceeded(self):
        """Test logging a rate limit exceeded event."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_rate_limit_exceeded(
                user_id="user123",
                session_id="session456",
                ip_address="192.168.1.1",
                request_id="req-789",
                endpoint="/api/tools",
                limit_type="requests_per_minute",
                current_count=150,
                limit=100,
                details={"window": "60s"},
            )

            # Verify event ID is returned
            assert event_id is not None

            # Verify log_security_event was called
            mock_log.assert_called_once()
            event_arg = mock_log.call_args[0][0]
            assert event_arg.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
            assert event_arg.severity == SecuritySeverity.MEDIUM
            assert event_arg.user_id == "user123"
            assert event_arg.session_id == "session456"
            assert event_arg.ip_address == "192.168.1.1"
            assert event_arg.request_id == "req-789"
            assert event_arg.endpoint == "/api/tools"
            assert event_arg.details["limit_type"] == "requests_per_minute"
            assert event_arg.details["current_count"] == 150
            assert event_arg.details["limit"] == 100
            assert event_arg.details["window"] == "60s"
            assert event_arg.risk_score == 0.6  # Fixed risk score for rate limit
            assert event_arg.blocked is True

    def test_log_rate_limit_exceeded_minimal(self):
        """Test logging a rate limit exceeded event with minimal data."""
        logger = SecurityAuditLogger(enable_console=False)

        with patch.object(logger, "log_security_event") as mock_log:
            event_id = logger.log_rate_limit_exceeded(
                user_id=None,
                session_id=None,
                ip_address=None,
                request_id=None,
                endpoint=None,
                limit_type="global",
                current_count=1000,
                limit=500,
                details={},
            )

            # Verify event ID is returned
            assert event_id is not None

            # Verify log_security_event was called
            mock_log.assert_called_once()
            event_arg = mock_log.call_args[0][0]
            assert event_arg.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
            assert event_arg.severity == SecuritySeverity.MEDIUM
            assert event_arg.details["limit_type"] == "global"
            assert event_arg.details["current_count"] == 1000
            assert event_arg.details["limit"] == 500
            assert event_arg.risk_score == 0.6  # Fixed risk score for rate limit
            assert event_arg.blocked is True
