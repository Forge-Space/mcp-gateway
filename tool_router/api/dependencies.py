"""FastAPI dependencies for JWT authentication and security context."""

from __future__ import annotations

import logging
import os
import time
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from tool_router.security.auth import AuthenticationError, JoseJWTValidator, JWTPayload
from tool_router.security.security_middleware import SecurityContext


logger = logging.getLogger(__name__)

_jwt_validator: JoseJWTValidator | None = None


def get_jwt_validator() -> JoseJWTValidator:
    global _jwt_validator
    if _jwt_validator is None:
        supabase_url = os.getenv("SUPABASE_URL", "")
        jwks_url = os.getenv(
            "SUPABASE_JWKS_URL",
            f"{supabase_url}/auth/v1/.well-known/jwks.json",
        )
        jwt_issuer = os.getenv(
            "JWT_ISSUER",
            f"{supabase_url}/auth/v1",
        )
        jwt_audience = os.getenv("JWT_AUDIENCE")
        _jwt_validator = JoseJWTValidator(
            jwks_url=jwks_url,
            jwt_issuer=jwt_issuer,
            audience=jwt_audience,
        )
    return _jwt_validator


async def get_jwt_payload(
    authorization: Annotated[str | None, Header()] = None,
) -> JWTPayload:
    validator = get_jwt_validator()
    try:
        token = validator.extract_token(authorization)
        return validator.validate(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


async def get_security_context(
    request: Request,
    jwt_payload: Annotated[JWTPayload, Depends(get_jwt_payload)],
) -> SecurityContext:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return SecurityContext(
        user_id=jwt_payload.sub,
        session_id=jwt_payload.raw.get("session_id"),
        ip_address=client_ip,
        user_agent=user_agent,
        request_id=f"rpc_{int(time.time())}_{hash(jwt_payload.sub) % 10000}",
        endpoint="/rpc",
        authentication_method="jwt",
        user_role=jwt_payload.role,
    )
