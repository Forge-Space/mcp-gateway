"""Jose JWT validation for Supabase-issued tokens."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError


logger = logging.getLogger(__name__)

JWKS_CACHE_TTL = 3600  # 1 hour


@dataclass
class JWTPayload:
    """Validated JWT payload."""

    sub: str
    role: str
    permissions: list[str] = field(default_factory=list)
    email: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class AuthenticationError(Exception):
    """Raised when JWT validation fails."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


class JoseJWTValidator:
    """Validates Supabase JWTs using JWKS and python-jose."""

    def __init__(
        self,
        jwks_url: str,
        jwt_issuer: str,
        audience: str | None = None,
        algorithms: list[str] | None = None,
    ):
        self.jwks_url = jwks_url
        self.jwt_issuer = jwt_issuer
        self.audience = audience
        self.algorithms = algorithms or ["RS256"]
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cache_time: float = 0

    def _fetch_jwks(self) -> dict[str, Any]:
        now = time.time()
        if self._jwks_cache and (now - self._jwks_cache_time) < JWKS_CACHE_TTL:
            return self._jwks_cache

        try:
            resp = httpx.get(self.jwks_url, timeout=10)
            resp.raise_for_status()
            self._jwks_cache = resp.json()
            self._jwks_cache_time = now
            logger.info("JWKS refreshed from %s", self.jwks_url)
            return self._jwks_cache
        except Exception as exc:
            if self._jwks_cache:
                logger.warning("JWKS refresh failed, using stale cache: %s", exc)
                return self._jwks_cache
            raise AuthenticationError(f"Failed to fetch JWKS: {exc}") from exc

    def validate(self, token: str) -> JWTPayload:
        """Validate a JWT and extract claims."""
        if not token:
            raise AuthenticationError("Missing authentication token")

        jwks = self._fetch_jwks()

        try:
            unverified_header = jwt.get_unverified_header(token)
        except JWTError as exc:
            raise AuthenticationError(f"Invalid token header: {exc}") from exc

        kid = unverified_header.get("kid")
        rsa_key: dict[str, str] = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key.get("use", "sig"),
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise AuthenticationError("Unable to find matching signing key")

        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self.algorithms,
                issuer=self.jwt_issuer,
                audience=self.audience,
                options={"verify_aud": self.audience is not None},
            )
        except ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except JWTError as exc:
            raise AuthenticationError(f"Invalid token: {exc}") from exc

        sub = payload.get("sub")
        if not sub:
            raise AuthenticationError("Token missing subject claim")

        role = payload.get("role", payload.get("user_role", "user"))
        permissions = payload.get("permissions", [])
        if isinstance(permissions, str):
            permissions = [permissions]

        return JWTPayload(
            sub=sub,
            role=role,
            permissions=permissions,
            email=payload.get("email"),
            raw=payload,
        )

    def extract_token(self, authorization: str | None) -> str:
        """Extract Bearer token from Authorization header."""
        if not authorization:
            raise AuthenticationError("Missing Authorization header")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationError("Invalid Authorization header format")
        return parts[1]
