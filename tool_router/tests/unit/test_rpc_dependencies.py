"""Tests for RPC endpoint dependencies (JWT auth, security context)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tool_router.api.dependencies import (
    get_jwt_payload,
    get_jwt_validator,
    get_security_context,
)
from tool_router.security.auth import AuthenticationError, JWTPayload


class TestGetJwtValidator:
    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co"})
    def test_creates_validator_from_env(self) -> None:
        import tool_router.api.dependencies as deps

        deps._jwt_validator = None
        validator = get_jwt_validator()
        assert validator.jwks_url == "https://test.supabase.co/auth/v1/.well-known/jwks.json"
        assert validator.jwt_issuer == "https://test.supabase.co/auth/v1"
        deps._jwt_validator = None

    @patch.dict(
        "os.environ",
        {
            "SUPABASE_JWKS_URL": "https://custom/jwks",
            "JWT_ISSUER": "https://custom/issuer",
            "JWT_AUDIENCE": "my-app",
        },
    )
    def test_custom_jwks_url(self) -> None:
        import tool_router.api.dependencies as deps

        deps._jwt_validator = None
        validator = get_jwt_validator()
        assert validator.jwks_url == "https://custom/jwks"
        assert validator.jwt_issuer == "https://custom/issuer"
        assert validator.audience == "my-app"
        deps._jwt_validator = None


class TestGetJwtPayload:
    @pytest.mark.asyncio
    async def test_missing_header_raises_401(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_jwt_payload(None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_format_raises_401(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_jwt_payload("not-bearer-format")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("tool_router.api.dependencies.get_jwt_validator")
    async def test_valid_token_returns_payload(self, mock_validator_fn: MagicMock) -> None:
        mock_validator = MagicMock()
        mock_validator.extract_token.return_value = "raw-token"
        mock_validator.validate.return_value = JWTPayload(
            sub="user-123",
            role="user",
            permissions=["generate"],
            email="test@example.com",
            raw={"sub": "user-123"},
        )
        mock_validator_fn.return_value = mock_validator

        payload = await get_jwt_payload("Bearer test-jwt-token")
        assert payload.sub == "user-123"
        assert payload.role == "user"
        mock_validator.extract_token.assert_called_once_with("Bearer test-jwt-token")
        mock_validator.validate.assert_called_once_with("raw-token")

    @pytest.mark.asyncio
    @patch("tool_router.api.dependencies.get_jwt_validator")
    async def test_expired_token_raises_401(self, mock_validator_fn: MagicMock) -> None:
        from fastapi import HTTPException

        mock_validator = MagicMock()
        mock_validator.extract_token.return_value = "expired-token"
        mock_validator.validate.side_effect = AuthenticationError("Token has expired")
        mock_validator_fn.return_value = mock_validator

        with pytest.raises(HTTPException) as exc_info:
            await get_jwt_payload("Bearer expired-token")
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()


class TestGetSecurityContext:
    @pytest.mark.asyncio
    async def test_builds_context_from_request(self) -> None:
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"user-agent": "Mozilla/5.0"}

        jwt_payload = JWTPayload(
            sub="user-456",
            role="admin",
            permissions=["generate", "manage"],
            raw={"sub": "user-456", "session_id": "sess-789"},
        )

        ctx = await get_security_context(mock_request, jwt_payload)
        assert ctx.user_id == "user-456"
        assert ctx.user_role == "admin"
        assert ctx.ip_address == "192.168.1.1"
        assert ctx.user_agent == "Mozilla/5.0"
        assert ctx.session_id == "sess-789"
        assert ctx.authentication_method == "jwt"
        assert ctx.endpoint == "/rpc"
        assert ctx.request_id.startswith("rpc_")

    @pytest.mark.asyncio
    async def test_handles_missing_client(self) -> None:
        mock_request = MagicMock()
        mock_request.client = None
        mock_request.headers = {}

        jwt_payload = JWTPayload(sub="user-1", role="user", raw={})

        ctx = await get_security_context(mock_request, jwt_payload)
        assert ctx.ip_address is None
        assert ctx.user_agent is None
