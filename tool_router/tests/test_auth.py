"""Tests for JoseJWTValidator."""

from __future__ import annotations

import time
from unittest.mock import Mock, patch

import pytest

from tool_router.security.auth import (
    AuthenticationError,
    JoseJWTValidator,
    JWTPayload,
)


MOCK_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "kid": "test-key-id",
            "use": "sig",
            "n": "test-n",
            "e": "AQAB",
        }
    ]
}

MOCK_JWKS_URL = "https://example.com/.well-known/jwks.json"
MOCK_ISSUER = "https://example.com"
MOCK_AUDIENCE = "test-audience"


@pytest.fixture
def validator() -> JoseJWTValidator:
    """Create a JoseJWTValidator instance."""
    return JoseJWTValidator(
        jwks_url=MOCK_JWKS_URL,
        jwt_issuer=MOCK_ISSUER,
        audience=MOCK_AUDIENCE,
    )


@pytest.fixture
def mock_jwks_response():
    """Mock httpx.get response for JWKS endpoint."""
    with patch("tool_router.security.auth.httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = MOCK_JWKS
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        yield mock_get


def test_valid_jwt_validation(validator: JoseJWTValidator, mock_jwks_response):
    """Test successful JWT validation with mocked JWKS endpoint."""
    valid_payload = {
        "sub": "user-123",
        "role": "developer",
        "permissions": ["component:read", "tool:execute"],
        "email": "test@example.com",
        "iss": MOCK_ISSUER,
        "aud": MOCK_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }

    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = valid_payload

            token = "mock.jwt.token"
            result = validator.validate(token)

            assert isinstance(result, JWTPayload)
            assert result.sub == "user-123"
            assert result.role == "developer"
            assert result.permissions == ["component:read", "tool:execute"]
            assert result.email == "test@example.com"
            assert result.raw == valid_payload

            mock_jwks_response.assert_called_once()
            mock_decode.assert_called_once()


def test_expired_token_raises_authentication_error(validator: JoseJWTValidator, mock_jwks_response):
    """Test that expired token raises AuthenticationError."""
    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            from jose.exceptions import ExpiredSignatureError

            mock_decode.side_effect = ExpiredSignatureError("Token expired")

            token = "expired.jwt.token"
            with pytest.raises(AuthenticationError) as exc_info:
                validator.validate(token)

            assert "Token has expired" in str(exc_info.value)
            assert exc_info.value.status_code == 401


def test_invalid_signature_raises_authentication_error(validator: JoseJWTValidator, mock_jwks_response):
    """Test that invalid signature raises AuthenticationError."""
    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            from jose import JWTError

            mock_decode.side_effect = JWTError("Invalid signature")

            token = "invalid.jwt.token"
            with pytest.raises(AuthenticationError) as exc_info:
                validator.validate(token)

            assert "Invalid token" in str(exc_info.value)
            assert exc_info.value.status_code == 401


def test_jwks_cache_hit(validator: JoseJWTValidator, mock_jwks_response):
    """Test that second validation uses cached JWKS."""
    valid_payload = {
        "sub": "user-123",
        "role": "user",
        "iss": MOCK_ISSUER,
        "aud": MOCK_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }

    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = valid_payload

            token = "mock.jwt.token"
            validator.validate(token)
            validator.validate(token)

            assert mock_jwks_response.call_count == 1


def test_missing_subject_claim(validator: JoseJWTValidator, mock_jwks_response):
    """Test that missing subject claim raises AuthenticationError."""
    invalid_payload = {
        "role": "user",
        "iss": MOCK_ISSUER,
        "aud": MOCK_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }

    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = invalid_payload

            token = "mock.jwt.token"
            with pytest.raises(AuthenticationError) as exc_info:
                validator.validate(token)

            assert "Token missing subject claim" in str(exc_info.value)


def test_extract_token_valid_header(validator: JoseJWTValidator):
    """Test extract_token with valid Authorization header."""
    auth_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    token = validator.extract_token(auth_header)
    assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"


def test_extract_token_missing_header(validator: JoseJWTValidator):
    """Test extract_token with missing Authorization header."""
    with pytest.raises(AuthenticationError) as exc_info:
        validator.extract_token(None)
    assert "Missing Authorization header" in str(exc_info.value)


def test_extract_token_invalid_format(validator: JoseJWTValidator):
    """Test extract_token with invalid Authorization header format."""
    with pytest.raises(AuthenticationError) as exc_info:
        validator.extract_token("InvalidFormat token")
    assert "Invalid Authorization header format" in str(exc_info.value)


def test_extract_token_missing_bearer_prefix(validator: JoseJWTValidator):
    """Test extract_token with missing Bearer prefix."""
    with pytest.raises(AuthenticationError) as exc_info:
        validator.extract_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    assert "Invalid Authorization header format" in str(exc_info.value)


def test_missing_kid_in_jwks(validator: JoseJWTValidator, mock_jwks_response):
    """Test validation fails when kid not found in JWKS."""
    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "unknown-key-id"}

        token = "mock.jwt.token"
        with pytest.raises(AuthenticationError) as exc_info:
            validator.validate(token)

        assert "Unable to find matching signing key" in str(exc_info.value)


def test_empty_token_raises_error(validator: JoseJWTValidator):
    """Test that empty token raises AuthenticationError."""
    with pytest.raises(AuthenticationError) as exc_info:
        validator.validate("")
    assert "Missing authentication token" in str(exc_info.value)


def test_permissions_as_string(validator: JoseJWTValidator, mock_jwks_response):
    """Test that permissions string is converted to list."""
    valid_payload = {
        "sub": "user-123",
        "role": "user",
        "permissions": "component:read",
        "iss": MOCK_ISSUER,
        "aud": MOCK_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }

    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = valid_payload

            token = "mock.jwt.token"
            result = validator.validate(token)

            assert result.permissions == ["component:read"]


def test_role_fallback_to_user_role(validator: JoseJWTValidator, mock_jwks_response):
    """Test role fallback from user_role claim if role not present."""
    valid_payload = {
        "sub": "user-123",
        "user_role": "admin",
        "iss": MOCK_ISSUER,
        "aud": MOCK_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }

    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = valid_payload

            token = "mock.jwt.token"
            result = validator.validate(token)

            assert result.role == "admin"


def test_jwks_cache_expiry(validator: JoseJWTValidator, mock_jwks_response):
    """Test that JWKS cache expires after TTL."""
    valid_payload = {
        "sub": "user-123",
        "role": "user",
        "iss": MOCK_ISSUER,
        "aud": MOCK_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }

    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = valid_payload

            token = "mock.jwt.token"
            validator.validate(token)

            validator._jwks_cache_time = time.time() - 3601

            validator.validate(token)

            assert mock_jwks_response.call_count == 2


def test_jwks_fetch_failure_with_stale_cache(validator: JoseJWTValidator, mock_jwks_response):
    """Test that stale cache is used when JWKS fetch fails."""
    validator._jwks_cache = MOCK_JWKS
    validator._jwks_cache_time = time.time() - 3601

    mock_jwks_response.side_effect = Exception("Network error")

    valid_payload = {
        "sub": "user-123",
        "role": "user",
        "iss": MOCK_ISSUER,
        "aud": MOCK_AUDIENCE,
        "exp": int(time.time()) + 3600,
    }

    with patch("tool_router.security.auth.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "test-key-id"}
        with patch("tool_router.security.auth.jwt.decode") as mock_decode:
            mock_decode.return_value = valid_payload

            token = "mock.jwt.token"
            result = validator.validate(token)
            assert result.sub == "user-123"


def test_jwks_fetch_failure_without_cache(validator: JoseJWTValidator):
    """Test that JWKS fetch failure without cache raises AuthenticationError."""
    with patch("tool_router.security.auth.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        token = "mock.jwt.token"
        with pytest.raises(AuthenticationError) as exc_info:
            validator.validate(token)

        assert "Failed to fetch JWKS" in str(exc_info.value)
