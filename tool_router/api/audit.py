"""Audit events API for MCP Gateway governance."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEvent(BaseModel):
    """A single audit trail entry."""

    timestamp: str = Field(description="ISO 8601 timestamp")
    event_type: str = Field(description="Event category (e.g. request_received, request_blocked)")
    severity: str = Field(description="Severity level: info, warning, error, critical")
    user_id: str | None = Field(default=None, description="Authenticated user ID")
    request_id: str | None = Field(default=None, description="Correlation ID for the request")
    ip_address: str | None = Field(default=None, description="Client IP address")
    details: dict[str, Any] = Field(default_factory=dict, description="Event-specific metadata")


class AuditEventsResponse(BaseModel):
    """Paginated audit events response."""

    events: list[AuditEvent]
    total: int = Field(description="Total events matching the filter")
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Number of events per page")


class AuditSummaryResponse(BaseModel):
    """Aggregate audit statistics."""

    total_events: int = Field(default=0)
    events_by_type: dict[str, int] = Field(default_factory=dict)
    events_by_severity: dict[str, int] = Field(default_factory=dict)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)


def _get_audit_logger():
    """Get the security audit logger singleton."""
    from tool_router.security import SecurityAuditLogger

    return SecurityAuditLogger()


@router.get(
    "/events",
    response_model=AuditEventsResponse,
    summary="List audit events",
    description="Retrieve paginated audit trail with optional filters. Requires admin role.",
)
async def get_audit_events(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Events per page"),
    event_type: str | None = Query(None, description="Filter by event type"),
    severity: str | None = Query(None, description="Filter by severity level"),
    user_id: str | None = Query(None, description="Filter by user ID"),
) -> AuditEventsResponse:
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


@router.get(
    "/summary",
    response_model=AuditSummaryResponse,
    summary="Get audit summary",
    description="Aggregate audit statistics. Requires admin role.",
)
async def get_audit_summary() -> dict[str, Any]:
    audit_logger = _get_audit_logger()
    try:
        return audit_logger.get_security_summary()
    except Exception as exc:
        logger.error("Failed to retrieve audit summary: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit summary",
        ) from exc
