"""Tests for GET /ai/ml-metrics endpoint.

Verifies:
- Response structure (timestamp, feedback_stats, selector_metrics, learning_health)
- RBAC enforcement (AUDIT_READ / SYSTEM_ADMIN required)
- Empty feedback store returns zero totals
- Populated feedback store returns correct stats
- FeedbackStats fields (total_entries, total_tools, tool_stats)
- ToolStatsSummary fields (tool_name, success_count, failure_count, total, success_rate, etc.)
- SelectorMetrics fields (total_requests, total_cost_saved, avg_response_time_ms, model_usage, cost_optimization_enabled)
- LearningHealth fields (top_performing_tools, low_confidence_tools, most_used_task_types)
- top_task_types and top_intents are lists of strings
- learning_health derived correctly from tool stats
- selector error falls back to defaults
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import tool_router.api.ai_ml_metrics as ml_mod
from tool_router.api.ai_ml_metrics import router as ai_ml_metrics_router
from tool_router.api.dependencies import get_security_context
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx(role: str) -> SecurityContext:
    return SecurityContext(
        user_id="user-test",
        session_id="sess-test",
        ip_address="127.0.0.1",
        user_agent="test-agent",
        request_id="req-test-1",
        endpoint="/ai/ml-metrics",
        authentication_method="jwt",
        user_role=role,
    )


def _make_tool_stats(
    tool_name: str,
    success: int = 5,
    failure: int = 1,
    avg_confidence: float = 0.8,
    recent_success_rate: float = 0.9,
    confidence_score: float | None = None,
    task_types: dict | None = None,
    intent_categories: dict | None = None,
) -> MagicMock:
    ts = MagicMock()
    ts.tool_name = tool_name
    ts.success_count = success
    ts.failure_count = failure
    ts.total = success + failure
    ts.success_rate = success / (success + failure)
    ts.avg_confidence = avg_confidence
    ts.recent_success_rate = recent_success_rate
    ts.confidence_score = confidence_score if confidence_score is not None else avg_confidence * recent_success_rate
    ts.task_types = task_types or {"search_operations": 3, "file_operations": 2}
    ts.intent_categories = intent_categories or {"search": 3, "read": 2}
    return ts


def _make_perf_metrics(
    total_requests: int = 0,
    total_cost_saved: float = 0.0,
    avg_response_time: float = 0.0,
    model_usage_stats: dict | None = None,
    cost_optimization_enabled: bool = False,
) -> dict:
    return {
        "total_requests": total_requests,
        "total_cost_saved": total_cost_saved,
        "average_response_time": avg_response_time,
        "model_usage_stats": model_usage_stats or {},
        "cost_optimization_enabled": cost_optimization_enabled,
        "cache_hit_rate": 0.0,
        "hardware_constraints": {},
    }


def _client(
    role: str,
    tool_stats: dict | None = None,
    perf_metrics: dict | None = None,
    selector_raises: bool = False,
) -> TestClient:
    """Build a TestClient with mocked store and selector."""
    mock_store = MagicMock()
    mock_store.get_all_stats.return_value = tool_stats or {}

    mock_selector_instance = MagicMock()
    if selector_raises:
        mock_selector_instance.get_performance_metrics.side_effect = RuntimeError("broken")
    else:
        mock_selector_instance.get_performance_metrics.return_value = perf_metrics or _make_perf_metrics()

    app = FastAPI()
    app.include_router(ai_ml_metrics_router)

    ctx = _make_ctx(role)

    async def _mock_ctx() -> SecurityContext:
        return ctx

    app.dependency_overrides[get_security_context] = _mock_ctx

    with (
        patch.object(ml_mod, "_store", mock_store),
        patch("tool_router.api.ai_ml_metrics.EnhancedAISelector", return_value=mock_selector_instance),
    ):
        client = TestClient(app)
        # Force requests to go through during the patch context
        return client


# ---------------------------------------------------------------------------
# RBAC tests
# ---------------------------------------------------------------------------


def test_user_role_forbidden() -> None:
    """user role lacks AUDIT_READ — should return 403."""
    app = FastAPI()
    app.include_router(ai_ml_metrics_router)
    app.dependency_overrides[get_security_context] = lambda: _make_ctx("user")  # type: ignore[return-value]
    r = TestClient(app, raise_server_exceptions=False).get("/ai/ml-metrics")
    assert r.status_code == 403


def test_guest_role_forbidden() -> None:
    """guest role lacks AUDIT_READ — should return 403."""
    app = FastAPI()
    app.include_router(ai_ml_metrics_router)
    app.dependency_overrides[get_security_context] = lambda: _make_ctx("guest")  # type: ignore[return-value]
    r = TestClient(app, raise_server_exceptions=False).get("/ai/ml-metrics")
    assert r.status_code == 403


def test_developer_role_allowed() -> None:
    """developer has AUDIT_READ — should return 200."""
    mock_store = MagicMock()
    mock_store.get_all_stats.return_value = {}
    mock_sel = MagicMock()
    mock_sel.get_performance_metrics.return_value = _make_perf_metrics()

    app = FastAPI()
    app.include_router(ai_ml_metrics_router)
    app.dependency_overrides[get_security_context] = lambda: _make_ctx("developer")  # type: ignore[return-value]

    with (
        patch.object(ml_mod, "_store", mock_store),
        patch("tool_router.api.ai_ml_metrics.EnhancedAISelector", return_value=mock_sel),
    ):
        r = TestClient(app).get("/ai/ml-metrics")
    assert r.status_code == 200


def test_admin_role_allowed() -> None:
    """admin has all permissions — should return 200."""
    mock_store = MagicMock()
    mock_store.get_all_stats.return_value = {}
    mock_sel = MagicMock()
    mock_sel.get_performance_metrics.return_value = _make_perf_metrics()

    app = FastAPI()
    app.include_router(ai_ml_metrics_router)
    app.dependency_overrides[get_security_context] = lambda: _make_ctx("admin")  # type: ignore[return-value]

    with (
        patch.object(ml_mod, "_store", mock_store),
        patch("tool_router.api.ai_ml_metrics.EnhancedAISelector", return_value=mock_sel),
    ):
        r = TestClient(app).get("/ai/ml-metrics")
    assert r.status_code == 200


def test_no_security_context_fails() -> None:
    """No dependency override — missing ctx raises 422 or 403."""
    app = FastAPI()
    app.include_router(ai_ml_metrics_router)
    r = TestClient(app, raise_server_exceptions=False).get("/ai/ml-metrics")
    assert r.status_code in {401, 403, 422}


# ---------------------------------------------------------------------------
# Response structure tests
# ---------------------------------------------------------------------------


def _get_data(role: str = "developer", tool_stats: dict | None = None, perf: dict | None = None) -> dict:
    mock_store = MagicMock()
    mock_store.get_all_stats.return_value = tool_stats or {}
    mock_sel = MagicMock()
    mock_sel.get_performance_metrics.return_value = perf or _make_perf_metrics()

    app = FastAPI()
    app.include_router(ai_ml_metrics_router)
    app.dependency_overrides[get_security_context] = lambda: _make_ctx(role)  # type: ignore[return-value]

    with (
        patch.object(ml_mod, "_store", mock_store),
        patch("tool_router.api.ai_ml_metrics.EnhancedAISelector", return_value=mock_sel),
    ):
        return TestClient(app).get("/ai/ml-metrics").json()


def test_response_has_required_fields() -> None:
    data = _get_data()
    assert "timestamp" in data
    assert "feedback_stats" in data
    assert "selector_metrics" in data
    assert "learning_health" in data


def test_feedback_stats_fields_present() -> None:
    fs = _get_data()["feedback_stats"]
    assert "total_entries" in fs
    assert "total_tools" in fs
    assert "tool_stats" in fs


def test_selector_metrics_fields_present() -> None:
    sm = _get_data()["selector_metrics"]
    assert "total_requests" in sm
    assert "total_cost_saved" in sm
    assert "avg_response_time_ms" in sm
    assert "model_usage" in sm
    assert "cost_optimization_enabled" in sm


def test_learning_health_fields_present() -> None:
    lh = _get_data()["learning_health"]
    assert "top_performing_tools" in lh
    assert "low_confidence_tools" in lh
    assert "most_used_task_types" in lh


# ---------------------------------------------------------------------------
# Empty store tests
# ---------------------------------------------------------------------------


def test_empty_store_zero_totals() -> None:
    fs = _get_data()["feedback_stats"]
    assert fs["total_entries"] == 0
    assert fs["total_tools"] == 0
    assert fs["tool_stats"] == {}


def test_empty_store_learning_health_empty() -> None:
    lh = _get_data()["learning_health"]
    assert lh["top_performing_tools"] == []
    assert lh["low_confidence_tools"] == []
    assert lh["most_used_task_types"] == []


# ---------------------------------------------------------------------------
# Populated store tests
# ---------------------------------------------------------------------------


def test_populated_store_counts() -> None:
    ts1 = _make_tool_stats("tool_a", success=8, failure=2)
    ts2 = _make_tool_stats("tool_b", success=3, failure=1)
    data = _get_data(tool_stats={"tool_a": ts1, "tool_b": ts2})
    fs = data["feedback_stats"]
    assert fs["total_tools"] == 2
    assert fs["total_entries"] == 14  # 10 + 4


def test_tool_stats_summary_fields() -> None:
    ts = _make_tool_stats("my_tool", success=4, failure=1)
    tool_data = _get_data(tool_stats={"my_tool": ts})["feedback_stats"]["tool_stats"]["my_tool"]
    assert tool_data["tool_name"] == "my_tool"
    assert tool_data["success_count"] == 4
    assert tool_data["failure_count"] == 1
    assert tool_data["total"] == 5
    assert isinstance(tool_data["success_rate"], float)
    assert isinstance(tool_data["avg_confidence"], float)
    assert isinstance(tool_data["top_task_types"], list)
    assert isinstance(tool_data["top_intents"], list)


def test_top_task_types_limited_to_3() -> None:
    ts = _make_tool_stats("tool_x", task_types={"a": 10, "b": 8, "c": 6, "d": 4, "e": 2})
    tool_data = _get_data(tool_stats={"tool_x": ts})["feedback_stats"]["tool_stats"]["tool_x"]
    assert len(tool_data["top_task_types"]) <= 3


def test_top_intents_limited_to_3() -> None:
    ts = _make_tool_stats("tool_y", intent_categories={"search": 10, "read": 7, "write": 5, "delete": 3})
    tool_data = _get_data(tool_stats={"tool_y": ts})["feedback_stats"]["tool_stats"]["tool_y"]
    assert len(tool_data["top_intents"]) <= 3


# ---------------------------------------------------------------------------
# Selector metrics tests
# ---------------------------------------------------------------------------


def test_selector_metrics_values() -> None:
    perf = _make_perf_metrics(
        total_requests=42,
        total_cost_saved=1.5,
        avg_response_time=120.0,
        cost_optimization_enabled=True,
        model_usage_stats={"gpt-4": {"usage_count": 20, "total_tokens": 1000, "total_cost": 0.5}},
    )
    sm = _get_data(perf=perf)["selector_metrics"]
    assert sm["total_requests"] == 42
    assert sm["total_cost_saved"] == 1.5
    assert sm["avg_response_time_ms"] == 120.0
    assert sm["cost_optimization_enabled"] is True
    assert len(sm["model_usage"]) == 1
    assert sm["model_usage"][0]["model"] == "gpt-4"
    assert sm["model_usage"][0]["usage_count"] == 20


def test_selector_metrics_empty_model_usage() -> None:
    sm = _get_data()["selector_metrics"]
    assert sm["model_usage"] == []


def test_selector_error_returns_defaults() -> None:
    """If selector raises, defaults are returned (empty metrics)."""
    mock_store = MagicMock()
    mock_store.get_all_stats.return_value = {}
    bad_sel = MagicMock()
    bad_sel.get_performance_metrics.side_effect = RuntimeError("broken")

    app = FastAPI()
    app.include_router(ai_ml_metrics_router)
    app.dependency_overrides[get_security_context] = lambda: _make_ctx("developer")  # type: ignore[return-value]

    with (
        patch.object(ml_mod, "_store", mock_store),
        patch("tool_router.api.ai_ml_metrics.EnhancedAISelector", return_value=bad_sel),
    ):
        sm = TestClient(app).get("/ai/ml-metrics").json()["selector_metrics"]
    assert sm["total_requests"] == 0
    assert sm["model_usage"] == []


# ---------------------------------------------------------------------------
# Learning health tests
# ---------------------------------------------------------------------------


def test_learning_health_top_tools_order() -> None:
    ts_high = _make_tool_stats("high_tool", success=9, failure=1)  # 0.9
    ts_low = _make_tool_stats("low_tool", success=1, failure=9)  # 0.1
    lh = _get_data(tool_stats={"high_tool": ts_high, "low_tool": ts_low})["learning_health"]
    assert lh["top_performing_tools"][0] == "high_tool"


def test_learning_health_low_confidence_detected() -> None:
    ts = _make_tool_stats("weak_tool", confidence_score=0.2)
    lh = _get_data(tool_stats={"weak_tool": ts})["learning_health"]
    assert "weak_tool" in lh["low_confidence_tools"]


def test_learning_health_high_confidence_not_in_low() -> None:
    ts = _make_tool_stats("strong_tool", confidence_score=0.9)
    lh = _get_data(tool_stats={"strong_tool": ts})["learning_health"]
    assert "strong_tool" not in lh["low_confidence_tools"]


def test_learning_health_most_used_task_types() -> None:
    ts1 = _make_tool_stats("t1", task_types={"search_operations": 10, "file_operations": 2})
    ts2 = _make_tool_stats("t2", task_types={"search_operations": 5, "code_operations": 8})
    lh = _get_data(tool_stats={"t1": ts1, "t2": ts2})["learning_health"]
    # search_operations=15, code_operations=8, file_operations=2
    assert lh["most_used_task_types"][0] == "search_operations"


def test_timestamp_is_iso_format() -> None:
    from datetime import datetime

    ts = _get_data()["timestamp"]
    datetime.fromisoformat(ts)  # should not raise
