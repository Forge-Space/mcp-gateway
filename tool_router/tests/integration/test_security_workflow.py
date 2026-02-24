"""Integration tests for security middleware workflows."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tool_router.security.input_validator import SecurityValidationResult
from tool_router.security.rate_limiter import RateLimitResult
from tool_router.security.security_middleware import SecurityContext, SecurityMiddleware


class TestSecurityWorkflow:
    """Integration tests for complete security workflows."""

    @pytest.fixture
    def security_config(self) -> dict:
        """Security middleware configuration."""
        return {
            "enabled": True,
            "strict_mode": False,
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 60,
                "burst_size": 10,
            },
            "input_validation": {
                "enabled": True,
                "max_input_length": 1000,
                "blocked_patterns": ["password", "secret", "token"],
            },
        }

    @pytest.fixture
    def middleware(self, security_config: dict) -> SecurityMiddleware:
        """Security middleware instance."""
        return SecurityMiddleware(security_config)

    def test_complete_security_check_workflow(self, middleware: SecurityMiddleware) -> None:
        """Test complete security check workflow for clean request."""
        context = SecurityContext(user_id="user123", ip_address="192.168.1.1", session_id="session456")

        task = "search for information"
        category = "research"
        context_data = "academic research project"

        with patch.object(middleware.audit_logger, "log_request_received") as mock_log:
            with patch.object(middleware.input_validator, "validate_prompt") as mock_validate:
                with patch.object(middleware.rate_limiter, "check_rate_limit") as mock_rate_limit:
                    # Mock successful validation
                    mock_validate.return_value = SecurityValidationResult(
                        is_valid=True,
                        risk_score=0.1,
                        violations=[],
                        sanitized_input=task,
                        blocked=False,
                        metadata={},
                    )

                    # Mock successful rate limit check
                    mock_rate_limit.return_value = RateLimitResult(
                        allowed=True,
                        remaining=50,
                        reset_time=1234567890,
                        retry_after=0,
                        metadata={},
                    )

                    result = middleware.check_request_security(context, task, category, context_data, "{}")

                    # Business logic validation
                    assert result.allowed is True
                    assert result.risk_score < 0.5
                    assert len(result.violations) == 0

                    # Should log the request
                    mock_log.assert_called_once()

                    # Should include sanitized inputs
                    assert "task" in result.sanitized_inputs
                    assert result.sanitized_inputs["task"] == task

    def test_security_workflow_with_violations(self, middleware: SecurityMiddleware) -> None:
        """Test security workflow when violations are detected."""
        context = SecurityContext(user_id="user123", ip_address="192.168.1.1")

        # Task with suspicious content
        task = "here is my password: secret123"
        category = "authentication"
        context_data = "login attempt"

        with patch.object(middleware.input_validator, "validate_prompt") as mock_validate:
            with patch.object(middleware.rate_limiter, "check_rate_limit") as mock_rate_limit:
                # Mock validation with violations
                mock_validate.return_value = SecurityValidationResult(
                    is_valid=False,
                    risk_score=0.9,
                    violations=["Password detected", "High risk pattern"],
                    sanitized_input="here is my password: [REDACTED]",
                    blocked=True,
                    metadata={"blocked_patterns": ["password"]},
                )

                # Mock rate limit check
                mock_rate_limit.return_value = RateLimitResult(
                    allowed=True,
                    remaining=50,
                    reset_time=1234567890,
                    retry_after=0,
                    metadata={},
                )

                result = middleware.check_request_security(context, task, category, context_data, "{}")

                # Business logic: high risk should be blocked
                assert result.allowed is False
                assert result.risk_score > 0.8
                assert len(result.violations) > 0

                # Should sanitize sensitive content
                assert "[REDACTED]" in result.sanitized_inputs["task"]
                assert "secret123" not in result.sanitized_inputs["task"]

    def test_rate_limiting_workflow(self, middleware: SecurityMiddleware) -> None:
        """Test rate limiting workflow."""
        context = SecurityContext(user_id="user123", ip_address="192.168.1.1")

        task = "normal request"
        category = "data"
        context_data = "regular operation"

        with patch.object(middleware.input_validator, "validate_prompt") as mock_validate:
            with patch.object(middleware.rate_limiter, "check_rate_limit") as mock_rate_limit:
                # Mock successful validation
                mock_validate.return_value = SecurityValidationResult(
                    is_valid=True,
                    risk_score=0.1,
                    violations=[],
                    sanitized_input=task,
                    blocked=False,
                    metadata={},
                )

                # Mock rate limit exceeded
                mock_rate_limit.return_value = RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=1234567890,
                    retry_after=60,  # 1 minute retry
                    metadata={"window_type": "minute"},
                )

                result = middleware.check_request_security(context, task, category, context_data, "{}")

                # Business logic: rate limit exceeded should be blocked
                assert result.allowed is False
                assert "rate limit" in result.blocked_reason.lower()

                # Should include rate limit metadata
                assert result.metadata["rate_limit"]["allowed"] is False
                assert result.metadata["rate_limit"]["retry_after"] == 60

    def test_strict_mode_security_workflow(self, security_config: dict) -> None:
        """Test security workflow in strict mode."""
        # Enable strict mode
        security_config["strict_mode"] = True
        strict_middleware = SecurityMiddleware(security_config)

        context = SecurityContext(user_id="user123", ip_address="192.168.1.1")

        # Medium risk task
        task = "execute system command"
        category = "system"
        context_data = "administrative task"

        with patch.object(strict_middleware.input_validator, "validate_prompt") as mock_validate:
            with patch.object(strict_middleware.rate_limiter, "check_rate_limit") as mock_rate_limit:
                # Mock medium risk validation
                mock_validate.return_value = SecurityValidationResult(
                    is_valid=True,
                    risk_score=0.6,  # Medium risk
                    violations=[],
                    sanitized_input=task,
                    blocked=False,
                    metadata={},
                )

                # Mock successful rate limit check
                mock_rate_limit.return_value = RateLimitResult(
                    allowed=True,
                    remaining=50,
                    reset_time=1234567890,
                    retry_after=0,
                    metadata={},
                )

                result = strict_middleware.check_request_security(context, task, category, context_data, "{}")

                # Business logic: strict mode should block medium risk
                assert result.allowed is False
                assert result.risk_score > 0.5
                assert "strict mode" in result.blocked_reason.lower()

    def test_anonymous_user_security_workflow(self, middleware: SecurityMiddleware) -> None:
        """Test security workflow for anonymous users."""
        # Anonymous context (no user_id)
        context = SecurityContext(ip_address="192.168.1.1", user_agent="Mozilla/5.0")

        task = "public information request"
        category = "general"
        context_data = "public data access"

        with patch.object(middleware.audit_logger, "log_request_received") as mock_log:
            with patch.object(middleware.input_validator, "validate_prompt") as mock_validate:
                with patch.object(middleware.rate_limiter, "check_rate_limit") as mock_rate_limit:
                    # Mock successful validation
                    mock_validate.return_value = SecurityValidationResult(
                        is_valid=True,
                        risk_score=0.3,  # Higher risk for anonymous
                        violations=[],
                        sanitized_input=task,
                        blocked=False,
                        metadata={},
                    )

                    # Mock rate limit check (stricter for anonymous)
                    mock_rate_limit.return_value = RateLimitResult(
                        allowed=True,
                        remaining=20,  # Lower limit for anonymous
                        reset_time=1234567890,
                        retry_after=0,
                        metadata={"user_type": "anonymous"},
                    )

                    result = middleware.check_request_security(context, task, category, context_data, "{}")

                    # Business logic: anonymous users should have higher scrutiny
                    assert result.allowed is True  # Still allowed for low-risk tasks
                    assert result.risk_score > 0.2  # Higher baseline risk

                    # Should generate request ID for anonymous users
                    assert context.request_id is not None
                    assert len(context.request_id) > 10

    def test_security_workflow_with_multiple_violations(self, middleware: SecurityMiddleware) -> None:
        """Test security workflow with multiple types of violations."""
        context = SecurityContext(user_id="user123", ip_address="192.168.1.1")

        # Task with multiple issues
        task = "execute 'rm -rf /' with api_token=secret_key"
        category = "system"
        context_data = "dangerous operation"

        with patch.object(middleware.input_validator, "validate_prompt") as mock_validate:
            with patch.object(middleware.rate_limiter, "check_rate_limit") as mock_rate_limit:
                # Mock validation with multiple violations
                mock_validate.return_value = SecurityValidationResult(
                    is_valid=False,
                    risk_score=0.95,  # Very high risk
                    violations=[
                        "Dangerous command detected",
                        "API token exposed",
                        "System operation risk",
                    ],
                    sanitized_input="execute '[REDACTED]' with api_token='[REDACTED]'",
                    blocked=True,
                    metadata={"blocked_patterns": ["rm -rf", "api_token"]},
                )

                # Mock rate limit check
                mock_rate_limit.return_value = RateLimitResult(
                    allowed=True,
                    remaining=50,
                    reset_time=1234567890,
                    retry_after=0,
                    metadata={},
                )

                result = middleware.check_request_security(context, task, category, context_data, "{}")

                # Business logic: multiple violations should be blocked
                assert result.allowed is False
                assert result.risk_score > 0.9
                assert len(result.violations) >= 2

                # Should sanitize all sensitive content
                sanitized = result.sanitized_inputs["task"]
                assert "rm -rf" not in sanitized
                assert "secret_key" not in sanitized
                assert "[REDACTED]" in sanitized

    def test_security_workflow_with_high_risk_allowed(self, middleware: SecurityMiddleware) -> None:
        """Test security workflow with high-risk but non-blocked request."""
        context = SecurityContext(user_id="user123", ip_address="192.168.1.1")

        task = "slightly suspicious request"
        category = "data"
        context_data = "testing security"

        with patch.object(middleware.input_validator, "validate_prompt") as mock_validate:
            with patch.object(middleware.rate_limiter, "check_rate_limit") as mock_rate_limit:
                mock_validate.return_value = SecurityValidationResult(
                    is_valid=True,
                    risk_score=0.8,
                    violations=[],
                    sanitized_input=task,
                    blocked=False,
                    metadata={},
                )

                mock_rate_limit.return_value = RateLimitResult(
                    allowed=True,
                    remaining=50,
                    reset_time=1234567890,
                    retry_after=0,
                    metadata={},
                )

                result = middleware.check_request_security(context, task, category, context_data, "{}")

                assert result.risk_score == 0.8
