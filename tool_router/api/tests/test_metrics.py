"""Tests for metrics API endpoints."""

from __future__ import annotations

from unittest.mock import Mock, patch

from tool_router.api.metrics import get_ai_router_metrics


class TestMetricsAPI:
    """Test metrics API endpoints."""

    @patch("tool_router.api.metrics.get_metrics")
    def test_get_ai_router_metrics_success(self, mock_get_metrics):
        """Test successful metrics retrieval."""
        mock_metrics = Mock()
        mock_metrics.get_counter.side_effect = lambda key: {
            "execute_task.ai_selection.success": 100,
            "execute_task.ai_selection.low_confidence": 10,
            "execute_task.ai_selection.error": 5,
            "execute_task.keyword_selection": 20,
            "ai_selector.initialized": 1,
            "ai_selector.unavailable": 0,
            "ai_selector.init_error": 0,
            "ai_selector.disabled": 0,
        }.get(key, 0)
        mock_metrics.get_gauge.return_value = 0.85
        mock_get_metrics.return_value = mock_metrics

        result = get_ai_router_metrics()

        assert "selection_methods" in result
        assert result["selection_methods"]["ai_success"] == 100
        assert result["selection_methods"]["keyword_fallback"] == 20
        assert "ai_selector_status" in result
        assert result["ai_selector_status"]["initialized"] == 1
        assert "performance" in result
        assert result["performance"]["avg_ai_confidence"] == 0.85
        assert "statistics" in result
        # Exact calculation: 100 / (100 + 20) = 0.833333...
        expected_rate = 100.0 / (100.0 + 20.0) * 100.0
        assert abs(result["statistics"]["ai_usage_rate"] - expected_rate) < 0.01

    @patch("tool_router.api.metrics.get_metrics")
    def test_get_ai_router_metrics_no_selections(self, mock_get_metrics):
        """Test metrics with no selections yet."""
        mock_metrics = Mock()
        mock_metrics.get_counter.return_value = 0
        mock_metrics.get_gauge.return_value = 0.0
        mock_get_metrics.return_value = mock_metrics

        result = get_ai_router_metrics()

        assert result["statistics"]["ai_usage_rate"] == 0.0
        assert result["statistics"]["fallback_rate"] == 0.0

    @patch("tool_router.api.metrics.get_metrics")
    def test_get_ai_router_metrics_calculation(self, mock_get_metrics):
        """Test usage rate calculation."""
        mock_metrics = Mock()
        mock_metrics.get_counter.side_effect = lambda key: {
            "execute_task.ai_selection.success": 70,
            "execute_task.keyword_selection": 30,
        }.get(key, 0)
        mock_metrics.get_gauge.return_value = 0.75
        mock_get_metrics.return_value = mock_metrics

        result = get_ai_router_metrics()

        assert result["statistics"]["ai_usage_rate"] == 70.0
        assert result["statistics"]["fallback_rate"] == 30.0
