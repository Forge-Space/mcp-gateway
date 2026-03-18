"""Tests for AI Performance Dashboard API endpoint."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import tool_router.api.ai_performance as ai_perf_module
from tool_router.api.ai_performance import router


def _make_app() -> FastAPI:
    """Build isolated test app with just the ai_performance router."""
    app = FastAPI()
    app.include_router(router)
    return app


class TestAIPerformanceEndpoint:
    """Tests for GET /ai/performance."""

    def test_get_ai_performance_returns_200(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        assert response.status_code == 200

    def test_get_ai_performance_has_required_fields(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        data = response.json()
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "system_status" in data
        assert "cache_metrics" in data
        assert "cloud_health" in data
        assert "ai_selector" in data
        assert "providers" in data
        assert "learning_metrics" in data

    def test_uptime_seconds_is_positive(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        assert response.json()["uptime_seconds"] >= 0

    def test_timestamp_is_iso_format(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        ts = response.json()["timestamp"]
        # Should not raise
        datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def test_system_status_is_valid(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        assert response.json()["system_status"] in ("healthy", "degraded", "starting")

    def test_cache_metrics_structure(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        cache = response.json()["cache_metrics"]
        assert "cache_hit_rate" in cache
        assert "total_hits" in cache
        assert "total_misses" in cache
        assert "total_requests" in cache

    def test_cache_hit_rate_is_numeric(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        cache = response.json()["cache_metrics"]
        assert isinstance(cache["cache_hit_rate"], (float, int))

    def test_cloud_health_structure(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        cloud = response.json()["cloud_health"]
        assert "overall_status" in cloud
        assert "total_providers" in cloud
        assert "healthy_providers" in cloud
        assert "degraded_providers" in cloud
        assert "unhealthy_providers" in cloud

    def test_cloud_health_overall_status_valid(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        cloud = response.json()["cloud_health"]
        assert cloud["overall_status"] in ("healthy", "warning", "degraded", "unknown")

    def test_ai_selector_structure(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        ai = response.json()["ai_selector"]
        assert "cache_hit_rate" in ai
        assert "total_requests" in ai
        assert "total_cost_saved" in ai
        assert "average_response_time" in ai
        assert "cost_optimization_enabled" in ai
        assert "model_usage_stats" in ai

    def test_providers_is_list(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        assert isinstance(response.json()["providers"], list)

    def test_learning_metrics_is_list(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        assert isinstance(response.json()["learning_metrics"], list)

    def test_learning_metrics_has_four_task_types(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        assert len(response.json()["learning_metrics"]) == 4

    def test_learning_metrics_structure(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        for item in response.json()["learning_metrics"]:
            assert "task_type" in item
            assert "total_tasks" in item
            assert "success_rate" in item
            assert "average_confidence" in item
            assert "improvement_rate" in item
            assert "last_updated" in item

    def test_learning_metrics_success_rate_range(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        for item in response.json()["learning_metrics"]:
            assert 0 <= item["success_rate"] <= 100

    def test_learning_metrics_confidence_range(self) -> None:
        with TestClient(_make_app()) as client:
            response = client.get("/ai/performance")
        for item in response.json()["learning_metrics"]:
            assert 0 <= item["average_confidence"] <= 1


class TestAIPerformanceCacheMetrics:
    """Tests for cache metrics aggregation."""

    def test_cache_metrics_graceful_on_error(self) -> None:
        with patch.object(
            ai_perf_module,
            "_get_cache_metrics_data",
            side_effect=RuntimeError("DB unavailable"),
        ):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        assert response.status_code == 200
        cache = response.json()["cache_metrics"]
        assert cache["cache_hit_rate"] == 0.0
        assert cache["total_requests"] == 0

    def test_cache_metrics_uses_real_data(self) -> None:
        mock_metrics = {
            "cache_hit_rate": 0.75,
            "total_hits": 300,
            "total_misses": 100,
            "total_requests": 400,
        }
        with patch.object(
            ai_perf_module,
            "_get_cache_metrics_data",
            return_value=mock_metrics,
        ):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        cache = response.json()["cache_metrics"]
        assert cache["cache_hit_rate"] == 0.75
        assert cache["total_hits"] == 300
        assert cache["total_misses"] == 100
        assert cache["total_requests"] == 400


class TestAIPerformanceCloudHealth:
    """Tests for cloud health aggregation."""

    def test_cloud_health_graceful_on_error(self) -> None:
        mock_router = ai_perf_module._multi_cloud_router
        with patch.object(mock_router, "health_summary", side_effect=RuntimeError("Cloud unavailable")):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        assert response.status_code == 200
        cloud = response.json()["cloud_health"]
        assert cloud["overall_status"] == "unknown"
        assert cloud["total_providers"] == 0

    def test_cloud_health_with_healthy_providers(self) -> None:
        mock_summary = {
            "providers": {
                "aws": {"status": "healthy"},
                "gcp": {"status": "healthy"},
            }
        }
        mock_router = ai_perf_module._multi_cloud_router
        with patch.object(mock_router, "health_summary", return_value=mock_summary):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        cloud = response.json()["cloud_health"]
        assert cloud["total_providers"] == 2
        assert cloud["healthy_providers"] == 2
        assert cloud["overall_status"] == "healthy"

    def test_cloud_health_with_unhealthy_provider(self) -> None:
        mock_summary = {
            "providers": {
                "aws": {"status": "healthy"},
                "gcp": {"status": "unhealthy"},
            }
        }
        mock_router = ai_perf_module._multi_cloud_router
        with patch.object(mock_router, "health_summary", return_value=mock_summary):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        cloud = response.json()["cloud_health"]
        assert cloud["unhealthy_providers"] == 1
        assert cloud["overall_status"] == "degraded"

    def test_cloud_health_with_degraded_provider(self) -> None:
        mock_summary = {
            "providers": {
                "aws": {"status": "healthy"},
                "gcp": {"status": "degraded"},
            }
        }
        mock_router = ai_perf_module._multi_cloud_router
        with patch.object(mock_router, "health_summary", return_value=mock_summary):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        cloud = response.json()["cloud_health"]
        assert cloud["degraded_providers"] == 1
        assert cloud["overall_status"] == "warning"


class TestAIPerformanceProviders:
    """Tests for provider metrics from AI selector."""

    def _mock_perf(self, model_usage: dict) -> dict:
        return {
            "cache_hit_rate": 0.5,
            "total_requests": 100,
            "total_cost_saved": 5.0,
            "average_response_time": 500.0,
            "cost_optimization_enabled": True,
            "model_usage_stats": model_usage,
            "hardware_constraints": {},
        }

    def test_providers_from_model_usage_stats(self) -> None:
        perf = self._mock_perf(
            {
                "llama3.2:3b": {
                    "count": 50,
                    "success_rate": 95.0,
                    "average_response_time": 800.0,
                    "average_confidence": 0.85,
                },
                "gpt-4o-mini": {
                    "count": 50,
                    "success_rate": 98.0,
                    "average_response_time": 600.0,
                    "average_confidence": 0.92,
                },
            }
        )
        with patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector:
            mock_selector.return_value.get_performance_metrics.return_value = perf
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        providers = response.json()["providers"]
        provider_names = {p["name"] for p in providers}
        assert "Ollama" in provider_names
        assert "OpenAI" in provider_names

    def test_providers_graceful_on_selector_error(self) -> None:
        with patch.object(
            ai_perf_module,
            "EnhancedAISelector",
            side_effect=RuntimeError("Selector unavailable"),
        ):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        assert response.status_code == 200
        data = response.json()
        assert data["providers"] == []
        assert data["ai_selector"]["total_requests"] == 0

    def test_provider_status_healthy_when_high_success_rate(self) -> None:
        perf = self._mock_perf(
            {
                "llama3.2:3b": {
                    "count": 10,
                    "success_rate": 98.0,
                    "average_response_time": 500.0,
                    "average_confidence": 0.9,
                },
            }
        )
        with patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector:
            mock_selector.return_value.get_performance_metrics.return_value = perf
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        providers = response.json()["providers"]
        ollama = next(p for p in providers if p["name"] == "Ollama")
        assert ollama["status"] == "healthy"

    def test_provider_status_warning_when_medium_success_rate(self) -> None:
        perf = self._mock_perf(
            {
                "llama3.2:3b": {
                    "count": 10,
                    "success_rate": 85.0,
                    "average_response_time": 500.0,
                    "average_confidence": 0.8,
                },
            }
        )
        with patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector:
            mock_selector.return_value.get_performance_metrics.return_value = perf
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        providers = response.json()["providers"]
        ollama = next(p for p in providers if p["name"] == "Ollama")
        assert ollama["status"] == "warning"

    def test_provider_status_error_when_low_success_rate(self) -> None:
        perf = self._mock_perf(
            {
                "llama3.2:3b": {
                    "count": 10,
                    "success_rate": 60.0,
                    "average_response_time": 500.0,
                    "average_confidence": 0.6,
                },
            }
        )
        with patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector:
            mock_selector.return_value.get_performance_metrics.return_value = perf
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        providers = response.json()["providers"]
        ollama = next(p for p in providers if p["name"] == "Ollama")
        assert ollama["status"] == "error"

    def test_provider_model_metrics_structure(self) -> None:
        perf = self._mock_perf(
            {
                "claude-haiku": {
                    "count": 20,
                    "success_rate": 96.0,
                    "average_response_time": 700.0,
                    "average_confidence": 0.88,
                },
            }
        )
        with patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector:
            mock_selector.return_value.get_performance_metrics.return_value = perf
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        providers = response.json()["providers"]
        anthropic = next(p for p in providers if p["name"] == "Anthropic")
        assert len(anthropic["models"]) == 1
        model = anthropic["models"][0]
        assert model["model"] == "claude-haiku"
        assert model["total_requests"] == 20
        assert model["success_rate"] == 96.0

    def test_empty_model_usage_stats_gives_empty_providers(self) -> None:
        perf = self._mock_perf({})
        with patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector:
            mock_selector.return_value.get_performance_metrics.return_value = perf
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")
        assert response.json()["providers"] == []


class TestAIPerformanceCoverageGaps:
    """Deterministic tests for remaining ai_performance branches."""

    def test_cloud_health_unknown_when_no_providers(self) -> None:
        mock_router = ai_perf_module._multi_cloud_router
        with patch.object(mock_router, "health_summary", return_value={"providers": {}}):
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")

        cloud = response.json()["cloud_health"]
        assert cloud["overall_status"] == "unknown"
        assert cloud["total_providers"] == 0

    def test_provider_mapping_google_xai_and_unknown(self) -> None:
        perf = {
            "cache_hit_rate": 0.4,
            "total_requests": 30,
            "total_cost_saved": 1.0,
            "average_response_time": 250.0,
            "cost_optimization_enabled": True,
            "model_usage_stats": {
                "gemini-1.5-flash": {
                    "count": 10,
                    "success_rate": 99.0,
                    "average_response_time": 220.0,
                    "average_confidence": 0.92,
                },
                "grok-2-mini": {
                    "count": 10,
                    "success_rate": 98.0,
                    "average_response_time": 260.0,
                    "average_confidence": 0.91,
                },
                "mystery-model": {
                    "count": 10,
                    "success_rate": 90.0,
                    "average_response_time": 300.0,
                    "average_confidence": 0.85,
                },
            },
            "hardware_constraints": {},
        }
        with patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector:
            mock_selector.return_value.get_performance_metrics.return_value = perf
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")

        names = {provider["name"] for provider in response.json()["providers"]}
        assert "Google" in names
        assert "xAI" in names
        assert "Unknown" in names

    def test_system_status_healthy_when_cloud_healthy_and_cache_good(self) -> None:
        mock_router = ai_perf_module._multi_cloud_router
        with (
            patch.object(
                ai_perf_module,
                "_get_cache_metrics_data",
                return_value={
                    "cache_hit_rate": 0.9,
                    "total_hits": 90,
                    "total_misses": 10,
                    "total_requests": 100,
                },
            ),
            patch.object(
                mock_router,
                "health_summary",
                return_value={"providers": {"aws": {"status": "healthy"}}},
            ),
            patch.object(ai_perf_module, "EnhancedAISelector") as mock_selector,
        ):
            mock_selector.return_value.get_performance_metrics.return_value = {
                "cache_hit_rate": 0.0,
                "total_requests": 0,
                "total_cost_saved": 0.0,
                "average_response_time": 0.0,
                "cost_optimization_enabled": False,
                "model_usage_stats": {},
            }
            with TestClient(_make_app()) as client:
                response = client.get("/ai/performance")

        assert response.status_code == 200
        assert response.json()["system_status"] == "healthy"
