"""Audit events API for MCP Gateway governance."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEvent(BaseModel):
    timestamp: str
    event_type: str
    severity: str
    user_id: str | None = None
    request_id: str | None = None
    ip_address: str | None = None
    details: dict[str, Any] = {}


class AuditEventsResponse(BaseModel):
    events: list[AuditEvent]
    total: int
    page: int
    page_size: int


def _get_audit_logger():
    """Get the security audit logger singleton."""
    from tool_router.security import SecurityAuditLogger

    return SecurityAuditLogger()


@router.get("/events", response_model=AuditEventsResponse)
async def get_audit_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: str | None = Query(None),
    severity: str | None = Query(None),
    user_id: str | None = Query(None),
) -> AuditEventsResponse:
    """Retrieve audit events. Requires admin role."""
    audit_logger = _get_audit_logger()

    try:
        summary = audit_logger.get_security_summary()
    except Exception as exc:
        logger.error("Failed to retrieve audit events: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit events",
        ) from exc

    events: list[AuditEvent] = []
    for event_data in summary.get("recent_events", []):
        event = AuditEvent(
            timestamp=event_data.get("timestamp", ""),
            event_type=event_data.get("event_type", "unknown"),
            severity=event_data.get("severity", "info"),
            user_id=event_data.get("user_id"),
            request_id=event_data.get("request_id"),
            ip_address=event_data.get("ip_address"),
            details=event_data.get("details", {}),
        )
        if event_type and event.event_type != event_type:
            continue
        if severity and event.severity != severity:
            continue
        if user_id and event.user_id != user_id:
            continue
        events.append(event)

    total = len(events)
    start = (page - 1) * page_size
    paginated = events[start : start + page_size]

    return AuditEventsResponse(
        events=paginated,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary")
async def get_audit_summary() -> dict[str, Any]:
    """Get audit summary statistics. Requires admin role."""
    audit_logger = _get_audit_logger()
    try:
        return audit_logger.get_security_summary()
    except Exception as exc:
        logger.error("Failed to retrieve audit summary: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit summary",
        ) from exc
