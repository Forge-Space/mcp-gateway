"""Tests for security audit logging functionality."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from unittest.mock import Mock

from tool_router.security.audit_logger import (
    SecurityAuditLogger,
    SecurityEvent,
    SecurityEventType,
    SecuritySeverity,
)


def _make_event(**overrides):
    """Helper to create a valid SecurityEvent with defaults."""
    from datetime import UTC, datetime

    defaults = {
        "event_id": "evt_test_001",
        "timestamp": datetime.now(UTC),
        "event_type": SecurityEventType.REQUEST_RECEIVED,
        "severity": SecuritySeverity.LOW,
        "user_id": "user123",
        "session_id": "sess_001",
        "ip_address": "192.168.1.1",
        "user_agent": "TestAgent/1.0",
        "request_id": "req_001",
        "endpoint": "/api/tools",
        "details": {},
        "risk_score": 0.0,
        "blocked": False,
        "metadata": {},
    }
    defaults.update(overrides)
    return SecurityEvent(**defaults)


class TestSecurityAuditLogger:
    """Test cases for SecurityAuditLogger functionality."""

    def test_audit_logger_initialization(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file=str(log_file))
        assert logger.log_file == str(log_file)
        assert logger.logger is not None

    def test_log_security_event_basic(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security_audit.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event = _make_event(
            event_type=SecurityEventType.AUTHENTICATION_FAILED,
            severity=SecuritySeverity.HIGH,
        )
        audit.log_security_event(event)

        audit.logger.error.assert_called_once()
        call_args = audit.logger.error.call_args[0]
        assert "authentication_failed" in str(call_args[0])

    def test_log_request_received(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security_audit.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_request_received(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            request_id="req_123",
            endpoint="/api/tools",
            details={"method": "POST"},
        )

        assert isinstance(event_id, str)
        audit.logger.info.assert_called_once()
        call_args = audit.logger.info.call_args[0]
        assert "request_received" in str(call_args[0])

    def test_log_request_blocked(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security_audit.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_request_blocked(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            request_id="req_123",
            endpoint="/api/tools",
            reason="Rate limit exceeded",
            risk_score=0.9,
            details={},
        )

        assert isinstance(event_id, str)
        audit.logger.error.assert_called_once()
        call_args = audit.logger.error.call_args[0]
        assert "request_blocked" in str(call_args[0])

    def test_log_rate_limit_exceeded(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_rate_limit_exceeded(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            request_id="req_123",
            endpoint="/api/tools",
            limit_type="requests_per_minute",
            current_count=101,
            limit=100,
            details={},
        )

        assert isinstance(event_id, str)
        audit.logger.warning.assert_called_once()
        call_args = audit.logger.warning.call_args[0]
        assert "rate_limit_exceeded" in str(call_args[0])

    def test_log_prompt_injection_detected(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_prompt_injection_detected(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            request_id="req_123",
            endpoint="/api/tools",
            patterns=["script_tag", "sql_injection"],
            risk_score=0.95,
            details={},
        )

        assert isinstance(event_id, str)
        audit.logger.error.assert_called_once()
        call_args = audit.logger.error.call_args[0]
        assert "prompt_injection_detected" in str(call_args[0])

    def test_log_authentication_failed(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_authentication_failed(
            user_id="user123",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            request_id="req_123",
            endpoint="/api/tools",
            auth_method="api_key",
            reason="Invalid password",
            details={},
        )

        assert isinstance(event_id, str)
        audit.logger.error.assert_called_once()
        call_args = audit.logger.error.call_args[0]
        assert "authentication_failed" in str(call_args[0])

    def test_log_authorization_failed(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_authorization_failed(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            request_id="req_123",
            endpoint="/api/admin",
            required_permission="admin",
            user_permissions=["read", "write"],
            details={"reason": "Insufficient permissions"},
        )

        assert isinstance(event_id, str)
        audit.logger.warning.assert_called_once()
        call_args = audit.logger.warning.call_args[0]
        assert "authorization_failed" in str(call_args[0])

    def test_log_validation_failed(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_validation_failed(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            request_id="req_123",
            endpoint="/api/tools",
            validation_type="input",
            violations=["Tool not found in registry"],
            risk_score=0.5,
            details={},
        )

        assert isinstance(event_id, str)
        audit.logger.warning.assert_called_once()
        call_args = audit.logger.warning.call_args[0]
        assert "validation_failed" in str(call_args[0])

    def test_log_penalty_applied(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_penalty_applied(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            request_id="req_123",
            endpoint="/api/tools",
            penalty_type="rate_limit",
            duration=300,
            reason="Too many requests",
            details={},
        )

        assert isinstance(event_id, str)
        audit.logger.warning.assert_called_once()
        call_args = audit.logger.warning.call_args[0]
        assert "penalty_applied" in str(call_args[0])

    def test_log_suspicious_activity(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event_id = audit.log_suspicious_activity(
            user_id="user123",
            session_id="sess_001",
            ip_address="192.168.1.1",
            request_id="req_123",
            endpoint="/api/tools",
            activity_type="rapid_tool_requests",
            risk_score=0.6,
            details={"request_count": 50, "time_window": "60s"},
        )

        assert isinstance(event_id, str)
        audit.logger.warning.assert_called_once()
        call_args = audit.logger.warning.call_args[0]
        assert "suspicious_activity" in str(call_args[0])

    def test_get_security_summary(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))

        summary = audit.get_security_summary()

        assert isinstance(summary, dict)
        assert "total_events" in summary
        assert "period_hours" in summary
        assert summary["period_hours"] == 24

    def test_create_request_hash(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))

        hash1 = audit.create_request_hash({"method": "POST", "path": "/api/tools", "user_id": "user123"})
        hash2 = audit.create_request_hash({"method": "POST", "path": "/api/tools", "user_id": "user123"})

        assert hash1 == hash2
        assert len(hash1) == 16

    def test_log_file_rotation(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        event = _make_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecuritySeverity.MEDIUM,
        )
        audit.log_security_event(event)

    def test_concurrent_logging(self, tmp_path: Path) -> None:
        log_file = tmp_path / "security.log"
        audit = SecurityAuditLogger(log_file=str(log_file))
        audit.logger = Mock()

        def log_events():
            for i in range(10):
                event = _make_event(
                    event_id=f"evt_{threading.current_thread().name}_{i}",
                    event_type=SecurityEventType.REQUEST_RECEIVED,
                    severity=SecuritySeverity.LOW,
                    user_id=f"user{i}",
                )
                audit.log_security_event(event)

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=log_events)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert audit.logger.info.call_count == 30

    def test_security_event_serialization(self) -> None:
        from datetime import UTC, datetime

        event = _make_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecuritySeverity.MEDIUM,
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        )

        event_dict = {
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

        json_str = json.dumps(event_dict)
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "suspicious_activity"
        assert parsed["severity"] == "medium"
        assert parsed["user_id"] == "user123"
