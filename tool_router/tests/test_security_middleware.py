"""Tests for security middleware module."""

from unittest.mock import patch

from tool_router.security.input_validator import SecurityValidationResult
from tool_router.security.rate_limiter import RateLimitResult
from tool_router.security.security_middleware import (
    SecurityCheckResult,
    SecurityContext,
    SecurityMiddleware,
)


class TestSecurityContext:
    """Test cases for SecurityContext dataclass."""

    def test_security_context_creation_minimal(self) -> None:
        """Test creating SecurityContext with minimal fields."""
        context = SecurityContext()

        assert context.user_id is None
        assert context.session_id is None
        assert context.ip_address is None
        assert context.user_agent is None
        assert context.request_id is None
        assert context.endpoint is None
        assert context.authentication_method is None
        assert context.user_role is None

    def test_security_context_creation_full(self) -> None:
        """Test creating SecurityContext with all fields."""
        context = SecurityContext(
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-789",
            endpoint="/api/tools",
            authentication_method="jwt",
            user_role="admin",
        )

        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.ip_address == "192.168.1.1"
        assert context.user_agent == "Mozilla/5.0"
        assert context.request_id == "req-789"
        assert context.endpoint == "/api/tools"
        assert context.authentication_method == "jwt"
        assert context.user_role == "admin"


class TestSecurityCheckResult:
    """Test cases for SecurityCheckResult dataclass."""

    def test_security_check_result_allowed(self) -> None:
        """Test creating SecurityCheckResult for allowed request."""
        result = SecurityCheckResult(
            allowed=True,
            risk_score=0.2,
            violations=[],
            sanitized_inputs={},
            metadata={"check_time": "2023-01-01T12:00:00"},
            blocked_reason=None,
        )

        assert result.allowed is True
        assert result.risk_score == 0.2
        assert result.violations == []
        assert result.sanitized_inputs == {}
        assert result.metadata["check_time"] == "2023-01-01T12:00:00"
        assert result.blocked_reason is None

    def test_security_check_result_blocked(self) -> None:
        """Test creating SecurityCheckResult for blocked request."""
        result = SecurityCheckResult(
            allowed=False,
            risk_score=0.9,
            violations=["malicious_input", "rate_limit_exceeded"],
            sanitized_inputs={"query": "sanitized_query"},
            metadata={"check_time": "2023-01-01T12:00:00"},
            blocked_reason="High risk score detected",
        )

        assert result.allowed is False
        assert result.risk_score == 0.9
        assert "malicious_input" in result.violations
        assert "rate_limit_exceeded" in result.violations
        assert result.sanitized_inputs["query"] == "sanitized_query"
        assert result.blocked_reason == "High risk score detected"


class TestSecurityMiddleware:
    """Test cases for SecurityMiddleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "strict_mode": False,
            "validation_level": "standard",
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 100,
                "burst_size": 10,
            },
            "audit_logging": {"enabled": True, "log_file": "/tmp/security_audit.log"},
        }
        self.middleware = SecurityMiddleware(self.config)

    def test_initialization_default_config(self) -> None:
        """Test middleware initialization with default config."""
        config = {}
        middleware = SecurityMiddleware(config)

        assert middleware.enabled is True  # Default value
        assert middleware.strict_mode is False  # Default value

    def test_initialization_custom_config(self) -> None:
        """Test middleware initialization with custom config."""
        config = {"enabled": False, "strict_mode": True, "validation_level": "strict"}
        middleware = SecurityMiddleware(config)

        assert middleware.enabled is False
        assert middleware.strict_mode is True

    def test_check_request_allowed(self) -> None:
        """Test request check that should be allowed."""
        context = SecurityContext(
            user_id="user123", ip_address="192.168.1.1", endpoint="/api/tools"
        )
        request_data = {"query": "search for information"}

        with (
            patch.object(
                self.middleware.input_validator, "validate_input"
            ) as mock_validate,
            patch.object(
                self.middleware.rate_limiter, "check_rate_limit"
            ) as mock_rate_limit,
            patch.object(self.middleware.audit_logger, "log_event") as mock_audit,
        ):

            # Mock successful validation
            mock_validate.return_value = SecurityValidationResult(
                is_valid=True, violations=[], sanitized_data=request_data
            )
            mock_rate_limit.return_value = RateLimitResult(
                allowed=True, remaining_requests=50
            )

            result = self.middleware.check_request(context, request_data)

            assert result.allowed is True
            assert result.risk_score < 0.5
            assert len(result.violations) == 0
            assert result.sanitized_inputs == request_data

    def test_check_request_blocked_by_validation(self) -> None:
        """Test request check blocked by input validation."""
        context = SecurityContext(
            user_id="user123", ip_address="192.168.1.1", endpoint="/api/tools"
        )
        request_data = {"query": "<script>alert('xss')</script>"}

        with (
            patch.object(
                self.middleware.input_validator, "validate_input"
            ) as mock_validate,
            patch.object(self.middleware.audit_logger, "log_event") as mock_audit,
        ):

            # Mock validation failure
            mock_validate.return_value = SecurityValidationResult(
                is_valid=False,
                violations=["xss_attempt"],
                sanitized_data={"query": "sanitized_query"},
            )

            result = self.middleware.check_request(context, request_data)

            assert result.allowed is False
            assert result.risk_score > 0.7
            assert "xss_attempt" in result.violations
            assert result.sanitized_inputs["query"] == "sanitized_query"
            assert result.blocked_reason is not None

    def test_check_request_blocked_by_rate_limit(self) -> None:
        """Test request check blocked by rate limiting."""
        context = SecurityContext(
            user_id="user123", ip_address="192.168.1.1", endpoint="/api/tools"
        )
        request_data = {"query": "search for information"}

        with (
            patch.object(
                self.middleware.input_validator, "validate_input"
            ) as mock_validate,
            patch.object(
                self.middleware.rate_limiter, "check_rate_limit"
            ) as mock_rate_limit,
            patch.object(self.middleware.audit_logger, "log_event") as mock_audit,
        ):

            # Mock successful validation but rate limit exceeded
            mock_validate.return_value = SecurityValidationResult(
                is_valid=True, violations=[], sanitized_data=request_data
            )
            mock_rate_limit.return_value = RateLimitResult(
                allowed=False, remaining_requests=0, retry_after=60
            )

            result = self.middleware.check_request(context, request_data)

            assert result.allowed is False
            assert "rate_limit_exceeded" in result.violations
            assert result.metadata.get("retry_after") == 60

    def test_check_request_disabled_middleware(self) -> None:
        """Test request check when middleware is disabled."""
        config = {"enabled": False}
        middleware = SecurityMiddleware(config)

        context = SecurityContext(user_id="user123")
        request_data = {"query": "any data"}

        result = middleware.check_request(context, request_data)

        # Should allow all requests when disabled
        assert result.allowed is True
        assert result.risk_score == 0.0
        assert result.violations == []

    def test_check_request_strict_mode(self) -> None:
        """Test request check in strict mode."""
        config = {"enabled": True, "strict_mode": True, "validation_level": "strict"}
        middleware = SecurityMiddleware(config)

        context = SecurityContext(
            user_id="user123", ip_address="192.168.1.1", endpoint="/api/tools"
        )
        request_data = {"query": "test data"}

        with (
            patch.object(middleware.input_validator, "validate_input") as mock_validate,
            patch.object(
                middleware.rate_limiter, "check_rate_limit"
            ) as mock_rate_limit,
            patch.object(middleware.audit_logger, "log_event") as mock_audit,
        ):

            # Mock validation with minor issues that would be allowed in standard mode
            mock_validate.return_value = SecurityValidationResult(
                is_valid=False,  # In strict mode, even minor issues block
                violations=["suspicious_pattern"],
                sanitized_data=request_data,
            )
            mock_rate_limit.return_value = RateLimitResult(
                allowed=True, remaining_requests=50
            )

            result = middleware.check_request(context, request_data)

            assert result.allowed is False
            assert "suspicious_pattern" in result.violations
            assert result.risk_score > 0.5

    def test_get_security_statistics(self) -> None:
        """Test getting security statistics."""
        with patch.object(self.middleware.audit_logger, "get_statistics") as mock_stats:
            mock_stats.return_value = {
                "total_requests": 1000,
                "blocked_requests": 50,
                "high_risk_requests": 25,
                "common_violations": {
                    "xss_attempt": 20,
                    "sql_injection": 15,
                    "rate_limit_exceeded": 10,
                    "suspicious_pattern": 5,
                },
            }

            stats = self.middleware.get_security_statistics()

            assert stats["total_requests"] == 1000
            assert stats["blocked_requests"] == 50
            assert stats["high_risk_requests"] == 25
            assert stats["block_rate"] == 0.05
            assert "common_violations" in stats

    def test_update_configuration(self) -> None:
        """Test updating middleware configuration."""
        new_config = {
            "enabled": False,
            "strict_mode": True,
            "validation_level": "strict",
        }

        self.middleware.update_configuration(new_config)

        assert self.middleware.enabled is False
        assert self.middleware.strict_mode is True

    def test_security_context_enrichment(self) -> None:
        """Test security context enrichment from request data."""
        request_headers = {
            "X-User-ID": "user123",
            "X-Session-ID": "session456",
            "User-Agent": "TestAgent/1.0",
            "X-Forwarded-For": "10.0.0.1",
        }

        with patch.object(self.middleware, "_extract_ip_from_headers") as mock_ip:
            mock_ip.return_value = "10.0.0.1"

            context = self.middleware.create_security_context(
                request_headers=request_headers,
                endpoint="/api/tools",
                request_id="req-123",
            )

            assert context.user_id == "user123"
            assert context.session_id == "session456"
            assert context.user_agent == "TestAgent/1.0"
            assert context.ip_address == "10.0.0.1"
            assert context.request_id == "req-123"
            assert context.endpoint == "/api/tools"

    def test_risk_score_calculation(self) -> None:
        """Test risk score calculation."""
        # Test with no violations
        result1 = SecurityCheckResult(
            allowed=True,
            risk_score=0.0,
            violations=[],
            sanitized_inputs={},
            metadata={},
        )

        # Test with minor violations
        result2 = SecurityCheckResult(
            allowed=True,
            risk_score=0.3,
            violations=["suspicious_pattern"],
            sanitized_inputs={},
            metadata={},
        )

        # Test with major violations
        result3 = SecurityCheckResult(
            allowed=False,
            risk_score=0.8,
            violations=["xss_attempt", "sql_injection"],
            sanitized_inputs={},
            metadata={},
        )

        assert result1.risk_score < result2.risk_score < result3.risk_score
        assert result1.allowed is True
        assert result2.allowed is True
        assert result3.allowed is False
