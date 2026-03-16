"""ML monitoring metrics API — exposes FeedbackStore and AI selector learning data."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from tool_router.ai.enhanced_selector import EnhancedAISelector
from tool_router.ai.feedback import FeedbackStore
from tool_router.security.authorization import Permission, RBACEvaluator, Role
from tool_router.security.security_middleware import SecurityContext

from .dependencies import get_security_context


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Performance"])

_rbac = RBACEvaluator()
_store = FeedbackStore()


def _require_audit_read(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """Require AUDIT_READ or SYSTEM_ADMIN permission."""
    role: Role = _rbac.resolve_role(ctx.user_role)
    has_audit_read = _rbac.check_permission(role, Permission.AUDIT_READ)
    has_system_admin = _rbac.check_permission(role, Permission.SYSTEM_ADMIN)
    if not (has_audit_read or has_system_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role.value}' does not have permission to view ML metrics.",
        )
    return ctx


class ToolStatsSummary(BaseModel):
    tool_name: str
    success_count: int
    failure_count: int
    total: int
    success_rate: float
    avg_confidence: float
    recent_success_rate: float
    confidence_score: float
    top_task_types: list[str]
    top_intents: list[str]


class FeedbackStats(BaseModel):
    total_entries: int
    total_tools: int
    tool_stats: dict[str, ToolStatsSummary]


class ModelUsage(BaseModel):
    model: str
    usage_count: int
    total_tokens: int
    total_cost: float


class SelectorMetrics(BaseModel):
    total_requests: int
    total_cost_saved: float
    avg_response_time_ms: float
    model_usage: list[ModelUsage]
    cost_optimization_enabled: bool


class LearningHealth(BaseModel):
    top_performing_tools: list[str]
    low_confidence_tools: list[str]
    most_used_task_types: list[str]


class MLMetricsResponse(BaseModel):
    timestamp: str
    feedback_stats: FeedbackStats
    selector_metrics: SelectorMetrics
    learning_health: LearningHealth


def _build_feedback_stats() -> FeedbackStats:
    all_stats = _store.get_all_stats()
    tool_summaries: dict[str, ToolStatsSummary] = {}
    total_entries = 0
    for tool_name, ts in all_stats.items():
        total_entries += ts.total
        top_tasks = sorted(ts.task_types, key=lambda k: ts.task_types[k], reverse=True)[:3]
        top_intents = sorted(ts.intent_categories, key=lambda k: ts.intent_categories[k], reverse=True)[:3]
        tool_summaries[tool_name] = ToolStatsSummary(
            tool_name=tool_name,
            success_count=ts.success_count,
            failure_count=ts.failure_count,
            total=ts.total,
            success_rate=ts.success_rate,
            avg_confidence=ts.avg_confidence,
            recent_success_rate=ts.recent_success_rate,
            confidence_score=ts.confidence_score,
            top_task_types=top_tasks,
            top_intents=top_intents,
        )
    return FeedbackStats(
        total_entries=total_entries,
        total_tools=len(tool_summaries),
        tool_stats=tool_summaries,
    )


def _build_selector_metrics() -> SelectorMetrics:
    try:
        selector = EnhancedAISelector()
        perf = selector.get_performance_metrics()
    except Exception:
        perf = {}
    raw_usage: dict[str, Any] = perf.get("model_usage_stats", {})
    model_usage = [
        ModelUsage(
            model=model,
            usage_count=stats.get("usage_count", 0),
            total_tokens=stats.get("total_tokens", 0),
            total_cost=stats.get("total_cost", 0.0),
        )
        for model, stats in raw_usage.items()
    ]
    return SelectorMetrics(
        total_requests=perf.get("total_requests", 0),
        total_cost_saved=perf.get("total_cost_saved", 0.0),
        avg_response_time_ms=perf.get("average_response_time", 0.0),
        model_usage=model_usage,
        cost_optimization_enabled=perf.get("cost_optimization_enabled", False),
    )


def _build_learning_health(all_stats: dict[str, Any]) -> LearningHealth:
    sorted_by_rate = sorted(all_stats.items(), key=lambda x: x[1].success_rate, reverse=True)
    top_tools = [t for t, _ in sorted_by_rate[:5]]
    low_conf = [t for t, s in all_stats.items() if s.confidence_score < 0.5][:5]
    task_counter: dict[str, int] = {}
    for ts in all_stats.values():
        for task, count in ts.task_types.items():
            task_counter[task] = task_counter.get(task, 0) + count
    top_tasks = sorted(task_counter, key=lambda k: task_counter[k], reverse=True)[:5]
    return LearningHealth(
        top_performing_tools=top_tools,
        low_confidence_tools=low_conf,
        most_used_task_types=top_tasks,
    )


@router.get(
    "/ml-metrics",
    response_model=MLMetricsResponse,
    summary="ML monitoring metrics",
    description="Returns FeedbackStore stats, AI selector cost metrics, and learning health indicators.",
)
async def get_ml_metrics(
    _ctx: Annotated[SecurityContext, Depends(_require_audit_read)],
) -> MLMetricsResponse:
    all_stats = _store.get_all_stats()
    feedback_stats = _build_feedback_stats()
    selector_metrics = _build_selector_metrics()
    learning_health = _build_learning_health(all_stats)
    return MLMetricsResponse(
        timestamp=datetime.now(UTC).isoformat(),
        feedback_stats=feedback_stats,
        selector_metrics=selector_metrics,
        learning_health=learning_health,
    )
