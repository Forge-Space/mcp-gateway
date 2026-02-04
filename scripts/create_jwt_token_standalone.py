#!/usr/bin/env python3
"""
Generate a JWT compatible with MCP Context Forge without loading gateway config.
Uses PLATFORM_ADMIN_EMAIL, JWT_SECRET_KEY (and optional JWT_ISSUER, JWT_AUDIENCE)
from the environment. Run with .env sourced (e.g. make jwt) or pass vars explicitly.
Requires: PyJWT (pip install pyjwt).
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

try:
    import jwt
except ImportError:
    print("PyJWT required. Install with: pip install pyjwt", file=sys.stderr)
    sys.exit(1)

ISSUER_DEFAULT = "mcpgateway"
AUDIENCE_DEFAULT = "mcpgateway-api"
EXP_MINUTES_DEFAULT = 10080


def main() -> None:
    username = os.environ.get("PLATFORM_ADMIN_EMAIL")
    secret = os.environ.get("JWT_SECRET_KEY")
    if not username or not secret:
        print(
            "Set PLATFORM_ADMIN_EMAIL and JWT_SECRET_KEY (e.g. source .env).",
            file=sys.stderr,
        )
        sys.exit(1)

    issuer = os.environ.get("JWT_ISSUER", ISSUER_DEFAULT)
    audience = os.environ.get("JWT_AUDIENCE", AUDIENCE_DEFAULT)
    try:
        exp_minutes = int(os.environ.get("JWT_EXP_MINUTES", EXP_MINUTES_DEFAULT))
    except ValueError:
        exp_minutes = EXP_MINUTES_DEFAULT

    now = datetime.now(timezone.utc)
    payload = {
        "username": username,
        "sub": username,
        "iat": int(now.timestamp()),
        "iss": issuer,
        "aud": audience,
        "jti": str(uuid.uuid4()),
    }
    if exp_minutes > 0:
        payload["exp"] = int((now + timedelta(minutes=exp_minutes)).timestamp())

    token = jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )
    if hasattr(token, "decode"):
        token = token.decode("utf-8")
    print(token)


if __name__ == "__main__":
    main()
