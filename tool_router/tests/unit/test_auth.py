"""Tests for tool_router.security.auth module."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tool_router.security.auth import (
    AuthenticationError,
    JoseJWTValidator,
    JWTPayload,
)


# ---------------------------------------------------------------------------
# JWTPayload
# ---------------------------------------------------------------------------


class TestJWTPayload:
    def test_basic(self):
        payload = JWTPayload(sub="user-1", role="admin")
        assert payload.sub == "user-1"
        assert payload.role == "admin"
        assert payload.permissions == []
        assert payload.email is None
        assert payload.raw == {}

    def test_full(self):
        payload = JWTPayload(
            sub="u2",
            role="developer",
            permissions=["read"],
            email="dev@example.com",
            raw={"sub": "u2"},
        )
        assert payload.email == "dev@example.com"
        assert "read" in payload.permissions


# ---------------------------------------------------------------------------
# AuthenticationError
# ---------------------------------------------------------------------------


class TestAuthenticationError:
    def test_default_status(self):
        err = AuthenticationError("bad token")
        assert err.status_code == 401
        assert str(err) == "bad token"

    def test_custom_status(self):
        err = AuthenticationError("expired", status_code=403)
        assert err.status_code == 403

    def test_is_exception(self):
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("boom")


# ---------------------------------------------------------------------------
# JoseJWTValidator.extract_token
# ---------------------------------------------------------------------------


class TestExtractToken:
    def setup_method(self):
        self.validator = JoseJWTValidator(
            jwks_url="https://example.com/.well-known/jwks.json",
            jwt_issuer="https://example.com",
        )

    def test_valid_bearer(self):
        token = self.validator.extract_token("Bearer abc.def.ghi")
        assert token == "abc.def.ghi"

    def test_case_insensitive_bearer(self):
        token = self.validator.extract_token("bearer abc.def.ghi")
        assert token == "abc.def.ghi"

    def test_missing_header_raises(self):
        with pytest.raises(AuthenticationError, match="Missing Authorization"):
            self.validator.extract_token(None)

    def test_empty_header_raises(self):
        with pytest.raises(AuthenticationError):
            self.validator.extract_token("")

    def test_invalid_format_raises(self):
        with pytest.raises(AuthenticationError, match="Invalid Authorization"):
            self.validator.extract_token("Basic abc")

    def test_missing_token_part_raises(self):
        with pytest.raises(AuthenticationError):
            self.validator.extract_token("Bearer")


# ---------------------------------------------------------------------------
# JoseJWTValidator._fetch_jwks
# ---------------------------------------------------------------------------


def _make_jwks_response(data: dict[str, Any]) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


class TestFetchJwks:
    def setup_method(self):
        self.validator = JoseJWTValidator(
            jwks_url="https://example.com/.well-known/jwks.json",
            jwt_issuer="https://example.com",
        )

    def test_fetches_and_caches(self):
        jwks = {"keys": [{"kid": "k1"}]}
        with patch("tool_router.security.auth.httpx.get") as mock_get:
            mock_get.return_value = _make_jwks_response(jwks)
            result = self.validator._fetch_jwks()
            assert result == jwks
            # Second call should use cache
            result2 = self.validator._fetch_jwks()
            assert result2 == jwks
            assert mock_get.call_count == 1  # only fetched once

    def test_returns_stale_cache_on_failure(self):
        jwks = {"keys": [{"kid": "k1"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 0  # expired
        with patch("tool_router.security.auth.httpx.get", side_effect=Exception("network")):
            result = self.validator._fetch_jwks()
            assert result == jwks

    def test_raises_when_no_cache_and_fetch_fails(self):
        with patch("tool_router.security.auth.httpx.get", side_effect=Exception("network")):
            with pytest.raises(AuthenticationError, match="Failed to fetch JWKS"):
                self.validator._fetch_jwks()


# ---------------------------------------------------------------------------
# JoseJWTValidator.validate
# ---------------------------------------------------------------------------


class TestValidate:
    def setup_method(self):
        self.validator = JoseJWTValidator(
            jwks_url="https://example.com/.well-known/jwks.json",
            jwt_issuer="https://example.com",
        )

    def test_empty_token_raises(self):
        with pytest.raises(AuthenticationError, match="Missing authentication token"):
            self.validator.validate("")

    def test_invalid_header_raises(self):
        jwks = {"keys": []}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999
        with pytest.raises(AuthenticationError, match="Invalid token header"):
            self.validator.validate("not.a.jwt")

    def test_no_matching_key_raises(self):
        from jose import jwt as jose_jwt

        header = {"alg": "HS256", "kid": "unknown-kid"}
        payload = {"sub": "u1"}
        # Create a minimal token with HS256 for header parsing only
        token = jose_jwt.encode(payload, "secret", algorithm="HS256")
        jwks = {"keys": [{"kid": "other-kid", "kty": "RSA", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999
        with pytest.raises(AuthenticationError, match=r"Invalid token header|Unable to find"):
            self.validator.validate(token)

    def test_valid_token(self):
        """Validate a HS256 token by mocking jwt.decode."""
        from jose import jwt as jose_jwt

        token = jose_jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")
        jwks = {"keys": [{"kid": None, "kty": "oct", "use": "sig", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999

        decoded = {
            "sub": "u1",
            "role": "developer",
            "permissions": ["read"],
            "email": "dev@example.com",
        }
        with patch("tool_router.security.auth.jwt.decode", return_value=decoded):
            with patch("tool_router.security.auth.jwt.get_unverified_header", return_value={"kid": None}):
                result = self.validator.validate(token)
        assert result.sub == "u1"
        assert result.role == "developer"
        assert result.permissions == ["read"]
        assert result.email == "dev@example.com"

    def test_valid_token_permissions_as_string(self):
        """permissions as string gets coerced to list."""
        jwks = {"keys": [{"kid": None, "kty": "oct", "use": "sig", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999

        decoded = {"sub": "u1", "role": "user", "permissions": "single_perm"}
        with patch("tool_router.security.auth.jwt.decode", return_value=decoded):
            with patch("tool_router.security.auth.jwt.get_unverified_header", return_value={"kid": None}):
                result = self.validator.validate("fake.token.here")
        assert result.permissions == ["single_perm"]

    def test_token_missing_sub_raises(self):
        jwks = {"keys": [{"kid": None, "kty": "oct", "use": "sig", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999

        decoded = {"role": "user"}  # no sub
        with patch("tool_router.security.auth.jwt.decode", return_value=decoded):
            with patch("tool_router.security.auth.jwt.get_unverified_header", return_value={"kid": None}):
                with pytest.raises(AuthenticationError, match="missing subject"):
                    self.validator.validate("fake.token.here")

    def test_expired_token_raises(self):
        from jose.exceptions import ExpiredSignatureError

        jwks = {"keys": [{"kid": None, "kty": "oct", "use": "sig", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999

        with patch("tool_router.security.auth.jwt.decode", side_effect=ExpiredSignatureError("expired")):
            with patch("tool_router.security.auth.jwt.get_unverified_header", return_value={"kid": None}):
                with pytest.raises(AuthenticationError, match="expired"):
                    self.validator.validate("fake.token.here")

    def test_jwt_error_raises(self):
        from jose import JWTError

        jwks = {"keys": [{"kid": None, "kty": "oct", "use": "sig", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999

        with patch("tool_router.security.auth.jwt.decode", side_effect=JWTError("bad")):
            with patch("tool_router.security.auth.jwt.get_unverified_header", return_value={"kid": None}):
                with pytest.raises(AuthenticationError, match="Invalid token"):
                    self.validator.validate("fake.token.here")

    def test_default_role_fallback(self):
        """When payload has no role/user_role field, defaults to 'user'."""
        jwks = {"keys": [{"kid": None, "kty": "oct", "use": "sig", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999

        decoded = {"sub": "u1"}  # no role
        with patch("tool_router.security.auth.jwt.decode", return_value=decoded):
            with patch("tool_router.security.auth.jwt.get_unverified_header", return_value={"kid": None}):
                result = self.validator.validate("fake.token.here")
        assert result.role == "user"

    def test_user_role_fallback(self):
        """Uses user_role field when role is absent."""
        jwks = {"keys": [{"kid": None, "kty": "oct", "use": "sig", "n": "a", "e": "b"}]}
        self.validator._jwks_cache = jwks
        self.validator._jwks_cache_time = 9999999999

        decoded = {"sub": "u1", "user_role": "admin"}
        with patch("tool_router.security.auth.jwt.decode", return_value=decoded):
            with patch("tool_router.security.auth.jwt.get_unverified_header", return_value={"kid": None}):
                result = self.validator.validate("fake.token.here")
        assert result.role == "admin"


# ---------------------------------------------------------------------------
# JoseJWTValidator constructor defaults
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_defaults(self):
        v = JoseJWTValidator(jwks_url="https://jwks", jwt_issuer="https://issuer")
        assert v.algorithms == ["RS256"]
        assert v.audience is None
        assert v._jwks_cache is None
        assert v._jwks_cache_time == 0

    def test_custom_algorithms(self):
        v = JoseJWTValidator(
            jwks_url="https://jwks",
            jwt_issuer="https://issuer",
            algorithms=["HS256"],
        )
        assert v.algorithms == ["HS256"]

    def test_audience(self):
        v = JoseJWTValidator(
            jwks_url="https://jwks",
            jwt_issuer="https://issuer",
            audience="my-api",
        )
        assert v.audience == "my-api"
