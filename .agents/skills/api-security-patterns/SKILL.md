---
name: api-security-patterns
description: Guide for adding authentication and RBAC enforcement to FastAPI endpoints in the MCP Gateway. Use when adding new API endpoints, reviewing existing endpoints for auth gaps, or implementing role-based access control.
---

# API Security Patterns

## The Problem Pattern (Common Mistake)

```python
# ❌ WRONG — endpoint documents auth but doesn't enforce it
@router.get("/audit/events", description="Requires admin role.")
async def get_audit_events(
    page: int = Query(1),
) -> AuditEventsResponse:
    # No dependency injection! Anyone can call this.
    ...
```

## The Correct Pattern

```python
# ✅ CORRECT — auth is enforced via FastAPI dependency injection
from typing import Annotated
from fastapi import Depends, HTTPException
from tool_router.api.dependencies import get_security_context
from tool_router.security.authorization import Permission, RBACEvaluator, Role
from tool_router.security.security_middleware import SecurityContext

_rbac = RBACEvaluator()

def _require_my_permission(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    role: Role = _rbac.resolve_role(ctx.user_role)
    if not _rbac.check_permission(role, Permission.MY_PERMISSION):
        raise HTTPException(status_code=403, detail=f"Role '{role.value}' lacks required permission.")
    return ctx

@router.get("/my-endpoint")
async def my_endpoint(
    _ctx: Annotated[SecurityContext, Depends(_require_my_permission)],
) -> MyResponse:
    ...
```

## RBAC Permissions (per `authorization.py`)

| Role | Has AUDIT_READ | Has TOOL_EXECUTE | Has SYSTEM_ADMIN |
|------|---------------|-----------------|-----------------|
| `admin` | ✅ | ✅ | ✅ |
| `developer` | ✅ | ✅ | ❌ |
| `user` | ❌ | ✅ | ❌ |
| `guest` | ❌ | ❌ | ❌ |

## Auth Flow

1. `get_security_context()` in `dependencies.py` validates the JWT and returns `SecurityContext`
2. `RBACEvaluator.resolve_role()` maps role string → `Role` enum (defaults to `guest`)
3. `RBACEvaluator.check_permission()` checks `ROLE_PERMISSIONS[role]` list
4. If permission missing → `HTTPException(status_code=403)`

## Testing Auth Enforcement

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tool_router.api.dependencies import get_security_context
from tool_router.security.security_middleware import SecurityContext

def _make_app(role: str) -> FastAPI:
    app = FastAPI()
    app.include_router(my_router)

    async def _mock_ctx() -> SecurityContext:
        return SecurityContext(user_id="test", user_role=role, ...)

    app.dependency_overrides[get_security_context] = _mock_ctx
    return app

def test_admin_returns_200():
    client = TestClient(_make_app("admin"))
    assert client.get("/my-endpoint").status_code == 200

def test_user_returns_403():
    client = TestClient(_make_app("user"))
    assert client.get("/my-endpoint").status_code == 403
```

## Audit Endpoints Status

Both `/audit/events` and `/audit/summary` now enforce RBAC (PR #187):
- Admin → 200
- Developer → 200 (has AUDIT_READ)  
- User/Guest → 403
- No JWT → 401

## Checklist for New Endpoints

- [ ] Has `Annotated[SecurityContext, Depends(get_security_context)]` or a permission-specific guard
- [ ] Guard function raises `HTTPException(403)` for insufficient role
- [ ] Tests cover: admin/developer pass, user/guest blocked, no auth → 401/422
- [ ] Endpoint description accurately states required role/permission
