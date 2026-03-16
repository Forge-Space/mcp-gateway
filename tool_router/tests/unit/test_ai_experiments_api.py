"""Tests for GET /ai/experiments endpoint.

Verifies:
- Response structure (experiments list, total)
- RBAC enforcement (AUDIT_READ / SYSTEM_ADMIN required)
- Empty experiments list when no experiments registered
- Experiment with variants and stats
- Winner detection (None when insufficient samples, name when threshold met)
- ExperimentSummary fields (id, description, active, variant_count, variants, stats, winner)
- VariantStats fields (count, avg_score, avg_latency_ms, success_rate, min_score, max_score)
- VariantSummary fields (name, weight, config)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.ai.ab_testing import ABTestManager, Experiment, ExperimentOutcome, Variant
from tool_router.api.ai_experiments import router as ai_experiments_router
from tool_router.api.dependencies import get_security_context
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(security_context: SecurityContext | None, manager: ABTestManager | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(ai_experiments_router)

    if security_context is not None:

        async def _mock_ctx() -> SecurityContext:
            return security_context

        app.dependency_overrides[get_security_context] = _mock_ctx

    # Patch the module-level manager if provided
    if manager is not None:
        import tool_router.api.ai_experiments as ai_exp_module

        ai_exp_module._manager = manager

    return app


def _make_ctx(role: str) -> SecurityContext:
    return SecurityContext(
        user_id="user-test",
        session_id="sess-test",
        ip_address="127.0.0.1",
        user_agent="test-agent",
        request_id="req-test-1",
        endpoint="/ai/experiments",
        authentication_method="jwt",
        user_role=role,
    )


def _make_experiment(exp_id: str, variant_names: list[str] = None, description: str = "Test experiment") -> Experiment:
    if variant_names is None:
        variant_names = ["control", "variant_a"]
    variants = [Variant(name=name, weight=1.0, config={}) for name in variant_names]
    return Experiment(id=exp_id, variants=variants, description=description, active=True)


def _make_manager_with_experiment(exp_id: str = "exp-1") -> ABTestManager:
    manager = ABTestManager()
    exp = _make_experiment(exp_id)
    manager.register(exp)
    return manager


# ---------------------------------------------------------------------------
# RBAC tests
# ---------------------------------------------------------------------------


def test_get_experiments_requires_authentication() -> None:
    """No security context → 401/403/422 (dependency injection missing)."""
    app = _make_app(security_context=None)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/ai/experiments")
    assert response.status_code in (401, 403, 422)


def test_get_experiments_forbidden_for_user() -> None:
    """user role has no AUDIT_READ → 403."""
    app = _make_app(security_context=_make_ctx("user"))
    client = TestClient(app)
    response = client.get("/ai/experiments")
    assert response.status_code == 403


def test_get_experiments_forbidden_for_guest() -> None:
    """guest role has no AUDIT_READ → 403."""
    app = _make_app(security_context=_make_ctx("guest"))
    client = TestClient(app)
    response = client.get("/ai/experiments")
    assert response.status_code == 403


def test_get_experiments_allowed_for_developer() -> None:
    """developer role has AUDIT_READ → 200."""
    app = _make_app(security_context=_make_ctx("developer"))
    client = TestClient(app)
    response = client.get("/ai/experiments")
    assert response.status_code == 200


def test_get_experiments_allowed_for_admin() -> None:
    """admin role has all permissions → 200."""
    app = _make_app(security_context=_make_ctx("admin"))
    client = TestClient(app)
    response = client.get("/ai/experiments")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Response structure tests (empty manager)
# ---------------------------------------------------------------------------


def test_get_experiments_response_structure() -> None:
    """Response has experiments list and total field."""
    app = _make_app(security_context=_make_ctx("developer"))
    client = TestClient(app)
    response = client.get("/ai/experiments")
    assert response.status_code == 200
    data = response.json()
    assert "experiments" in data
    assert "total" in data
    assert isinstance(data["experiments"], list)
    assert isinstance(data["total"], int)


def test_get_experiments_empty_by_default() -> None:
    """Fresh manager has no experiments — returns empty list with total=0."""
    manager = ABTestManager()
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["experiments"] == []
    assert data["total"] == 0


def test_get_experiments_total_matches_list_length() -> None:
    """total field == len(experiments)."""
    manager = _make_manager_with_experiment("exp-total-test")
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["total"] == len(data["experiments"])


# ---------------------------------------------------------------------------
# Experiment content tests
# ---------------------------------------------------------------------------


def test_experiment_has_required_fields() -> None:
    """Each experiment entry has all required fields."""
    manager = _make_manager_with_experiment("exp-fields")
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert len(data["experiments"]) == 1
    exp = data["experiments"][0]
    assert "id" in exp
    assert "description" in exp
    assert "active" in exp
    assert "variant_count" in exp
    assert "variants" in exp
    assert "stats" in exp
    assert "winner" in exp


def test_experiment_id_matches_registered() -> None:
    """Experiment id matches what was registered."""
    manager = _make_manager_with_experiment("my-experiment-id")
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["experiments"][0]["id"] == "my-experiment-id"


def test_experiment_description_non_empty() -> None:
    """description field is a non-empty string."""
    manager = ABTestManager()
    exp = _make_experiment("exp-desc", description="My test description")
    manager.register(exp)
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["experiments"][0]["description"] == "My test description"


def test_experiment_variant_count_matches_variants() -> None:
    """variant_count equals len(variants)."""
    manager = _make_manager_with_experiment("exp-vc")
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    exp = data["experiments"][0]
    assert exp["variant_count"] == len(exp["variants"])


def test_experiment_active_flag() -> None:
    """active field reflects experiment active status."""
    manager = ABTestManager()
    exp = Experiment(id="exp-active", variants=[Variant(name="ctrl")], active=True)
    manager.register(exp)
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["experiments"][0]["active"] is True


# ---------------------------------------------------------------------------
# VariantSummary tests
# ---------------------------------------------------------------------------


def test_variant_summary_has_required_fields() -> None:
    """Each variant has name, weight, config fields."""
    manager = _make_manager_with_experiment("exp-vs")
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    for variant in data["experiments"][0]["variants"]:
        assert "name" in variant
        assert "weight" in variant
        assert "config" in variant


def test_variant_names_match_registered() -> None:
    """Variant names in response match what was registered."""
    manager = ABTestManager()
    exp = Experiment(
        id="exp-vnames",
        variants=[Variant(name="control", weight=1.0), Variant(name="treatment", weight=1.5)],
    )
    manager.register(exp)
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    names = {v["name"] for v in data["experiments"][0]["variants"]}
    assert names == {"control", "treatment"}


# ---------------------------------------------------------------------------
# Stats and winner tests
# ---------------------------------------------------------------------------


def test_stats_empty_when_no_outcomes() -> None:
    """stats dict is empty when no outcomes recorded."""
    manager = _make_manager_with_experiment("exp-nostats")
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["experiments"][0]["stats"] == {}


def test_winner_none_when_no_outcomes() -> None:
    """winner is null when no outcomes recorded."""
    manager = _make_manager_with_experiment("exp-nowinner")
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["experiments"][0]["winner"] is None


def test_stats_populated_after_outcomes() -> None:
    """stats dict contains variant stats after recording outcomes."""
    manager = ABTestManager()
    exp = Experiment(id="exp-stats", variants=[Variant(name="control"), Variant(name="variant_a")])
    manager.register(exp)
    for i in range(5):
        manager.record_outcome(
            ExperimentOutcome(
                experiment_id="exp-stats",
                variant_name="control",
                user_id=f"user-{i}",
                quality_score=0.8,
                latency_ms=100.0,
                success=True,
            )
        )
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    stats = data["experiments"][0]["stats"]
    assert "control" in stats
    s = stats["control"]
    assert "count" in s
    assert "avg_score" in s
    assert "avg_latency_ms" in s
    assert "success_rate" in s
    assert "min_score" in s
    assert "max_score" in s


def test_multiple_experiments_all_returned() -> None:
    """Multiple registered experiments all appear in response."""
    manager = ABTestManager()
    for i in range(3):
        manager.register(Experiment(id=f"exp-multi-{i}", variants=[Variant(name="ctrl")]))
    app = _make_app(security_context=_make_ctx("developer"), manager=manager)
    client = TestClient(app)
    response = client.get("/ai/experiments")
    data = response.json()
    assert data["total"] == 3
    assert len(data["experiments"]) == 3
