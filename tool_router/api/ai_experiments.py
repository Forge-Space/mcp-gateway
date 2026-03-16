"""AI A/B testing experiments endpoint."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from tool_router.ai.ab_testing import ABTestManager
from tool_router.security.authorization import Permission, RBACEvaluator
from tool_router.security.security_middleware import SecurityContext

from .dependencies import get_security_context

router = APIRouter(prefix="/ai", tags=["AI Performance"])

_rbac = RBACEvaluator()
_manager = ABTestManager()


def _require_audit_read(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    role = _rbac.resolve_role(ctx.user_role)
    has_audit_read = _rbac.check_permission(role, Permission.AUDIT_READ)
    has_system_admin = _rbac.check_permission(role, Permission.SYSTEM_ADMIN)
    if not (has_audit_read or has_system_admin):
        raise HTTPException(
            status_code=403,
            detail="Requires AUDIT_READ or SYSTEM_ADMIN permission",
        )
    return ctx


class VariantStats(BaseModel):
    count: int
    avg_score: float
    avg_latency_ms: float
    success_rate: float
    min_score: float
    max_score: float


class VariantSummary(BaseModel):
    name: str
    weight: float
    config: dict[str, Any]


class ExperimentSummary(BaseModel):
    id: str
    description: str
    active: bool
    variant_count: int
    variants: list[VariantSummary]
    stats: dict[str, VariantStats]
    winner: str | None


class ExperimentsResponse(BaseModel):
    experiments: list[ExperimentSummary]
    total: int


@router.get(
    "/experiments",
    response_model=ExperimentsResponse,
    summary="List A/B test experiments",
    description=(
        "Returns all registered A/B test experiments with per-variant performance stats "
        "and the current winner (if sufficient samples exist). "
        "Requires AUDIT_READ or SYSTEM_ADMIN permission."
    ),
)
async def get_experiments(
    _ctx: Annotated[SecurityContext, Depends(_require_audit_read)],
) -> ExperimentsResponse:
    experiments: list[ExperimentSummary] = []

    for exp_id, exp in _manager._experiments.items():
        raw_stats = _manager.get_variant_stats(exp_id)
        typed_stats: dict[str, VariantStats] = {}
        for variant_name, s in raw_stats.items():
            typed_stats[variant_name] = VariantStats(
                count=s["count"],
                avg_score=s["avg_score"],
                avg_latency_ms=s["avg_latency_ms"],
                success_rate=s["success_rate"],
                min_score=s["min_score"],
                max_score=s["max_score"],
            )

        winner = _manager.get_winner(exp_id)
        variant_summaries = [VariantSummary(name=v.name, weight=v.weight, config=v.config) for v in exp.variants]

        experiments.append(
            ExperimentSummary(
                id=exp_id,
                description=exp.description,
                active=exp.active,
                variant_count=len(exp.variants),
                variants=variant_summaries,
                stats=typed_stats,
                winner=winner,
            )
        )

    return ExperimentsResponse(experiments=experiments, total=len(experiments))
