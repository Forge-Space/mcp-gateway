"""Tests for security audit logging functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from tool_router.security.audit_logger import SecurityAuditLogger, SecurityEvent


class TestSecurityAuditLogger:
    """Test cases for SecurityAuditLogger functionality."""

    def test_audit_logger_initialization(self, tmp_path: Path) -> None:
        """Test SecurityAuditLogger initialization."""
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        assert logger.log_file_path == str(log_file)
        assert logger.logger is not None

    def test_log_security_event_basic(self, tmp_path: Path) -> None:
        """Test basic security event logging."""
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        # Mock the logger to capture calls
        logger.logger = Mock()

        event = SecurityEvent(
            event_type="authentication_failed",
            severity="high",
            user_id="user123",
            ip_address="192.168.1.1",
            details={"reason": "Invalid credentials"}
        )

        logger.log_security_event(event)

        # Verify logger was called
        logger.logger.info.assert_called_once()
        call_args = logger.logger.info.call_args[0]
        assert "authentication_failed" in str(call_args[0])
        assert "high" in str(call_args[0])

    def test_log_request_received(self, tmp_path: Path) -> None:
        """Test request received logging."""
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_request_received(
            request_id="req_123",
            method="POST",
            path="/api/tools",
            user_id="user123",
            ip_address="192.168.1.1"
        )

        logger.logger.info.assert_called_once()
        call_args = logger.logger.info.call_args[0]
        assert "request_received" in str(call_args[0])

    def test_log_request_blocked(self, tmp_path: Path) -> None:
        """Test request blocked logging."""
        log_file = tmp_path / "security_audit.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_request_blocked(
            request_id="req_123",
            reason="Rate limit exceeded",
            user_id="user123",
            ip_address="192.168.1.1"
        )

        logger.logger.warning.assert_called_once()
        call_args = logger.logger.warning.call_args[0]
        assert "request_blocked" in str(call_args[0])

    def test_log_rate_limit_exceeded(self, tmp_path: Path) -> None:
        """Test rate limit exceeded logging."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_rate_limit_exceeded(
            user_id="user123",
            ip_address="192.168.1.1",
            limit_type="requests_per_minute",
            limit_value=100
        )

        logger.logger.warning.assert_called_once()
        call_args = logger.logger.warning.call_args[0]
        assert "rate_limit_exceeded" in str(call_args[0])

    def test_log_prompt_injection_detected(self, tmp_path: Path) -> None:
        """Test prompt injection detection logging."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_prompt_injection_detected(
            request_id="req_123",
            prompt_content="malicious<script>alert('xss')</script>",
            user_id="user123",
            confidence=0.95
        )

        logger.logger.error.assert_called_once()
        call_args = logger.logger.error.call_args[0]
        assert "prompt_injection_detected" in str(call_args[0])

    def test_log_authentication_failed(self, tmp_path: Path) -> None:
        """Test authentication failure logging."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_authentication_failed(
            user_id="user123",
            reason="Invalid password",
            ip_address="192.168.1.1"
        )

        logger.logger.warning.assert_called_once()
        call_args = logger.logger.warning.call_args[0]
        assert "authentication_failed" in str(call_args[0])

    def test_log_authorization_failed(self, tmp_path: Path) -> None:
        """Test authorization failure logging."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_str(log_file))

        logger.logger = Mock()

        logger.log_authorization_failed(
            user_id="user123",
            resource="/api/admin",
            reason="Insufficient permissions",
            ip_address="192.168.1.1"
        )

        logger.logger.warning.assert_called_once()
        call_args = logger.logger.warning.call_args[0]
        assert "authorization_failed" in str(call_args[0])

    def test_log_validation_failed(self, tmp_path: Path) -> None:
        """Test validation failure logging."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_validation_failed(
            field_name="tool_name",
            value="invalid_tool",
            reason="Tool not found in registry",
            user_id="user123"
        )

        logger.logger.warning.assert_called_once()
        call_args = logger.logger.warning.call_args[0]
        assert "validation_failed" in str(call_args[0])

    def test_log_penalty_applied(self, tmp_path: Path) -> None:
        """Test penalty application logging."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_penalty_applied(
            user_id="user123",
            penalty_type="rate_limit",
            duration_seconds=300,
            reason="Too many requests"
        )

        logger.logger.info.assert_called_once()
        call_args = logger.logger.info.call_args[0]
        assert "penalty_applied" in str(call_args[0])

    def test_log_suspicious_activity(self, tmp_path: Path) -> None:
        """Test suspicious activity logging."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        logger.logger = Mock()

        logger.log_suspicious_activity(
            user_id="user123",
            activity_pattern="rapid_tool_requests",
            details={"request_count": 50, "time_window": "60s"}
        )

        logger.logger.warning.assert_called_once()
        call_args = logger.logger.warning.call_args[0]
        assert "suspicious_activity" in str(call_args[0])

    def test_get_security_summary(self, tmp_path: Path) -> None:
        """Test security summary generation."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        # Mock some internal data
        logger._event_counts = {
            "authentication_failed": 5,
            "request_blocked": 3,
            "prompt_injection_detected": 1
        }

        summary = logger.get_security_summary()

        assert isinstance(summary, dict)
        assert "total_events" in summary
        assert summary["total_events"] == 9
        assert "event_counts" in summary
        assert summary["event_counts"]["authentication_failed"] == 5

    def test_create_request_hash(self, tmp_path: Path) -> None:
        """Test request hash creation for tracking."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        # Test hash creation
        hash1 = logger.create_request_hash(
            method="POST",
            path="/api/tools",
            user_id="user123",
            body="test data"
        )
        hash2 = logger.create_request_hash(
            method="POST",
            path="/api/tools",
            user_id="user123",
            body="test data"
        )

        assert hash1 == hash2  # Same input should produce same hash
        assert len(hash1) == 32  # SHA256 produces 32 char hex string

    def test_log_file_rotation(self, tmp_path: Path) -> None:
        """Test log file rotation handling."""
        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        # Mock file operations
        with patch('builtins.open', side_effect=OSError("File too large")) as mock_open:
            with patch('os.rename', side_effect=OSError("Cannot rename")):
                # Should handle file rotation errors gracefully
                logger.log_security_event(
                    SecurityEvent(
                        event_type="test",
                        severity="low",
                        user_id="user123",
                        ip_address="192.168.1.1",
                        details={}
                    )
                )
                # Should not raise exception

    def test_concurrent_logging(self, tmp_path: Path) -> None:
        """Test concurrent logging operations."""
        import threading
        import time

        log_file = tmp_path / "security.log"
        logger = SecurityAuditLogger(log_file_path=str(log_file))

        # Mock logger to capture calls
        logger.logger = Mock()

        def log_events():
            for i in range(10):
                logger.log_security_event(
                    SecurityEvent(
                        event_type=f"event_{i}",
                        severity="low",
                        user_id=f"user{i}",
                        ip_address="192.168.1.1",
                        details={}
                    )
                )

        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=log_events)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all events were logged
        assert logger.logger.info.call_count == 30

    def test_security_event_serialization(self, tmp_path: Path) -> None:
        """Test SecurityEvent serialization to JSON."""
        event = SecurityEvent(
            event_type="test_event",
            severity="medium",
            user_id="user123",
            ip_address="192.168.1.1",
            details={"key": "value", "nested": {"inner": "data"}}
        )

        # Test JSON serialization
        import json
        event_dict = event.__dict__
        json_str = json.dumps(event_dict)

        # Should be serializable
        assert json.loads(json_str) == event_dict

        # Test deserialization
        reconstructed_event = SecurityEvent(**event_dict)
        assert reconstructed_event.event_type == "test_event"
        assert reconstructed_event.severity == "medium"
        assert reconstructed_event.user_id == "user123"
        assert reconstructed_event.ip_address == "192.168.1.1"
