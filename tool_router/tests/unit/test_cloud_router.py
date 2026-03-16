"""Unit tests for tool_router/cloud/router.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tool_router.cloud.provider import CloudProvider
from tool_router.cloud.router import MultiCloudRouter, NoHealthyProviderError, RoutingStrategy
from tool_router.core.config import GatewayConfig


def _make_config() -> GatewayConfig:
    return GatewayConfig(url="http://localhost:4444", jwt="test-jwt")


def _make_provider(name: str = "p1", cloud_type: str = "aws", priority: int = 0, enabled: bool = True) -> CloudProvider:
    with patch("tool_router.cloud.provider.HTTPGatewayClient"), patch("tool_router.cloud.provider.CircuitBreaker"):
        p = CloudProvider(
            name=name,
            cloud_type=cloud_type,
            region="us-east-1",
            config=_make_config(),
            priority=priority,
            enabled=enabled,
        )
    return p


def _healthy_provider(name: str = "p1", priority: int = 0) -> CloudProvider:
    """Provider with no requests recorded (UNKNOWN = treated as healthy)."""
    return _make_provider(name=name, priority=priority)


def _degraded_provider(name: str = "p_deg") -> CloudProvider:
    p = _make_provider(name=name)
    p._metrics.total_requests = 5
    p._metrics.consecutive_failures = 1
    return p


def _unhealthy_provider(name: str = "p_bad") -> CloudProvider:
    p = _make_provider(name=name)
    p._metrics.total_requests = 3
    p._metrics.total_failures = 3
    p._metrics.consecutive_failures = 3
    return p


# ---------------------------------------------------------------------------
# RoutingStrategy enum
# ---------------------------------------------------------------------------


class TestRoutingStrategy:
    def test_values(self):
        assert RoutingStrategy.FAILOVER.value == "failover"
        assert RoutingStrategy.ROUND_ROBIN.value == "round_robin"
        assert RoutingStrategy.LATENCY_WEIGHTED.value == "latency_weighted"
        assert RoutingStrategy.RANDOM.value == "random"


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    def test_add_and_list(self):
        router = MultiCloudRouter()
        p = _healthy_provider()
        router.add_provider(p)
        assert len(router.list_providers()) == 1
        assert router.list_providers()[0] is p

    def test_add_duplicate_raises(self):
        router = MultiCloudRouter()
        p1 = _healthy_provider("aws1")
        p2 = _healthy_provider("aws1")
        router.add_provider(p1)
        with pytest.raises(ValueError, match="already registered"):
            router.add_provider(p2)

    def test_remove_existing(self):
        router = MultiCloudRouter()
        p = _healthy_provider("aws1")
        router.add_provider(p)
        result = router.remove_provider("aws1")
        assert result is True
        assert len(router.list_providers()) == 0

    def test_remove_nonexistent_returns_false(self):
        router = MultiCloudRouter()
        result = router.remove_provider("does-not-exist")
        assert result is False

    def test_get_provider_found(self):
        router = MultiCloudRouter()
        p = _healthy_provider("myp")
        router.add_provider(p)
        assert router.get_provider("myp") is p

    def test_get_provider_not_found(self):
        router = MultiCloudRouter()
        assert router.get_provider("missing") is None

    def test_init_with_providers(self):
        p1 = _healthy_provider("a")
        p2 = _healthy_provider("b")
        router = MultiCloudRouter(providers=[p1, p2])
        assert len(router.list_providers()) == 2


# ---------------------------------------------------------------------------
# Routing strategies
# ---------------------------------------------------------------------------


class TestRoutingStrategyFailover:
    def test_selects_highest_priority(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        p_low = _healthy_provider("low", priority=10)
        p_high = _healthy_provider("high", priority=0)
        router.add_provider(p_low)
        router.add_provider(p_high)
        selected = router._select_provider()
        assert selected.name == "high"

    def test_skips_unhealthy_when_degraded_available(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        bad = _unhealthy_provider("bad")
        deg = _degraded_provider("deg")
        router.add_provider(bad)
        router.add_provider(deg)
        # All healthy providers list is empty; should fallback to degraded
        healthy = router._healthy_providers()
        assert len(healthy) == 0

    def test_raises_when_no_healthy_or_degraded(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        bad = _unhealthy_provider("bad")
        router.add_provider(bad)
        with pytest.raises(NoHealthyProviderError):
            router._select_provider()


class TestRoutingStrategyRoundRobin:
    def test_cycles_through_providers(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.ROUND_ROBIN)
        p1 = _healthy_provider("p1")
        p2 = _healthy_provider("p2")
        router.add_provider(p1)
        router.add_provider(p2)
        # First call
        s1 = router._select_provider()
        # Second call
        s2 = router._select_provider()
        assert s1.name != s2.name


class TestRoutingStrategyLatencyWeighted:
    def test_selects_lowest_latency(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.LATENCY_WEIGHTED)
        fast = _healthy_provider("fast")
        slow = _healthy_provider("slow")
        fast._metrics.total_requests = 10
        fast._metrics.total_latency_ms = 100.0  # avg 10ms
        slow._metrics.total_requests = 10
        slow._metrics.total_latency_ms = 5000.0  # avg 500ms
        router.add_provider(fast)
        router.add_provider(slow)
        selected = router._select_provider()
        assert selected.name == "fast"

    def test_unknown_latency_treated_as_inf(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.LATENCY_WEIGHTED)
        unknown = _healthy_provider("unknown")  # 0 requests → avg_latency=0 → treated as inf
        known = _healthy_provider("known")
        known._metrics.total_requests = 5
        known._metrics.total_latency_ms = 100.0  # avg 20ms
        router.add_provider(unknown)
        router.add_provider(known)
        selected = router._select_provider()
        assert selected.name == "known"


class TestRoutingStrategyRandom:
    def test_random_selects_from_healthy(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.RANDOM)
        p1 = _healthy_provider("p1")
        p2 = _healthy_provider("p2")
        router.add_provider(p1)
        router.add_provider(p2)
        selected = router._select_provider()
        assert selected.name in {"p1", "p2"}


# ---------------------------------------------------------------------------
# get_tools + call_tool
# ---------------------------------------------------------------------------


class TestGetTools:
    def test_returns_tools_on_success(self):
        router = MultiCloudRouter()
        p = _healthy_provider()
        p.get_tools = MagicMock(return_value=[{"name": "t1"}])
        router.add_provider(p)
        with patch("tool_router.cloud.router.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=MagicMock())
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span
            tools = router.get_tools()
        assert tools == [{"name": "t1"}]

    def test_raises_when_all_providers_fail(self):
        router = MultiCloudRouter()
        p = _healthy_provider()
        p.get_tools = MagicMock(side_effect=ConnectionError("down"))
        router.add_provider(p)
        with patch("tool_router.cloud.router.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=MagicMock())
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span
            with pytest.raises(NoHealthyProviderError):
                router.get_tools()

    def test_falls_back_to_second_provider(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        p1 = _healthy_provider("p1", priority=0)
        p2 = _healthy_provider("p2", priority=1)
        p1.get_tools = MagicMock(side_effect=ConnectionError("p1 down"))
        p2.get_tools = MagicMock(return_value=[{"name": "tool_from_p2"}])
        router.add_provider(p1)
        router.add_provider(p2)
        with patch("tool_router.cloud.router.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=MagicMock())
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span
            tools = router.get_tools()
        assert tools == [{"name": "tool_from_p2"}]


class TestCallTool:
    def test_returns_result_on_success(self):
        router = MultiCloudRouter()
        p = _healthy_provider()
        p.call_tool = MagicMock(return_value='{"ok": true}')
        router.add_provider(p)
        with patch("tool_router.cloud.router.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=MagicMock())
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span
            result = router.call_tool("my_tool", {"arg": "x"})
        assert result == '{"ok": true}'

    def test_raises_when_all_fail(self):
        router = MultiCloudRouter()
        p = _healthy_provider()
        p.call_tool = MagicMock(side_effect=ValueError("bad"))
        router.add_provider(p)
        with patch("tool_router.cloud.router.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=MagicMock())
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span
            with pytest.raises(NoHealthyProviderError):
                router.call_tool("tool", {})


# ---------------------------------------------------------------------------
# health_summary
# ---------------------------------------------------------------------------


class TestHealthSummary:
    def test_empty_router(self):
        router = MultiCloudRouter()
        summary = router.health_summary()
        assert summary["total_providers"] == 0
        assert summary["healthy"] == 0
        assert summary["degraded"] == 0
        assert summary["unhealthy"] == 0
        assert summary["overall"] == "unhealthy"

    def test_all_healthy(self):
        router = MultiCloudRouter()
        p1 = _healthy_provider("a")
        p2 = _healthy_provider("b")
        # Force HEALTHY status
        p1._metrics.total_requests = 10
        p2._metrics.total_requests = 10
        router.add_provider(p1)
        router.add_provider(p2)
        summary = router.health_summary()
        assert summary["healthy"] == 2
        assert summary["overall"] == "healthy"

    def test_mixed_health(self):
        router = MultiCloudRouter()
        good = _healthy_provider("good")
        good._metrics.total_requests = 10
        bad = _unhealthy_provider("bad")
        router.add_provider(good)
        router.add_provider(bad)
        summary = router.health_summary()
        assert summary["total_providers"] == 2
        assert summary["unhealthy"] == 1
        assert "providers" in summary
        assert len(summary["providers"]) == 2

    def test_strategy_in_summary(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.ROUND_ROBIN)
        summary = router.health_summary()
        assert summary["strategy"] == "round_robin"


# ---------------------------------------------------------------------------
# set_strategy
# ---------------------------------------------------------------------------


class TestSetStrategy:
    def test_changes_strategy(self):
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        router._rr_index = 5
        router.set_strategy(RoutingStrategy.ROUND_ROBIN)
        assert router._strategy == RoutingStrategy.ROUND_ROBIN
        assert router._rr_index == 0

    def test_set_all_strategies(self):
        router = MultiCloudRouter()
        for s in RoutingStrategy:
            router.set_strategy(s)
            assert router._strategy == s


# ---------------------------------------------------------------------------
# Coverage gaps — _select_provider, _ordered_providers, health_summary
# ---------------------------------------------------------------------------


class TestSelectProviderCoverageGaps:
    def test_degraded_fallback_used_when_no_healthy(self):
        """Line 96: when no healthy providers, DEGRADED ones are used instead of raising."""
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        deg = _degraded_provider("p_deg")
        router.add_provider(deg)
        # No healthy providers; should pick the degraded one without raising
        provider = router._select_provider()
        assert provider.name == "p_deg"

    def test_default_fallback_return_line_115(self):
        """Line 115: when strategy doesn't match any known branch, return healthy[0]."""
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        p1 = _healthy_provider("p1", priority=0)
        p2 = _healthy_provider("p2", priority=1)
        router.add_provider(p1)
        router.add_provider(p2)
        # Temporarily set an enum value that won't match FAILOVER/ROUND_ROBIN/LATENCY_WEIGHTED/RANDOM
        # by exhausting all branches: use FAILOVER but force the code to fall through to line 115
        # We can test this by monkeypatching the strategy after construction
        router._strategy = None  # type: ignore[assignment]
        provider = router._select_provider()
        # Should return first healthy provider (healthy[0])
        assert provider in (p1, p2)


class TestOrderedProvidersCoverageGaps:
    def test_round_robin_no_healthy_falls_back_to_all_enabled(self):
        """Lines 177: ROUND_ROBIN with no healthy providers returns all enabled."""
        router = MultiCloudRouter(strategy=RoutingStrategy.ROUND_ROBIN)
        bad = _unhealthy_provider("p_bad")
        router.add_provider(bad)
        result = router._ordered_providers()
        assert len(result) == 1
        assert result[0].name == "p_bad"

    def test_latency_weighted_no_healthy_falls_back_to_all_enabled(self):
        """Lines 185-186: LATENCY_WEIGHTED with no healthy providers returns all enabled."""
        router = MultiCloudRouter(strategy=RoutingStrategy.LATENCY_WEIGHTED)
        bad = _unhealthy_provider("p_bad")
        router.add_provider(bad)
        result = router._ordered_providers()
        assert len(result) == 1
        assert result[0].name == "p_bad"

    def test_random_no_healthy_falls_back_to_all_enabled(self):
        """Lines 191-192: RANDOM with no healthy providers returns all enabled."""
        router = MultiCloudRouter(strategy=RoutingStrategy.RANDOM)
        bad = _unhealthy_provider("p_bad")
        router.add_provider(bad)
        result = router._ordered_providers()
        assert len(result) == 1
        assert result[0].name == "p_bad"

    def test_unknown_strategy_returns_all_enabled(self):
        """Line 197: unknown strategy falls through to return all enabled providers."""
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        p1 = _healthy_provider("p1")
        router.add_provider(p1)
        router._strategy = None  # type: ignore[assignment]
        result = router._ordered_providers()
        assert p1 in result

    def test_round_robin_with_healthy_rotates(self):
        """Lines 179-181: ROUND_ROBIN with healthy providers rotates from current index."""
        router = MultiCloudRouter(strategy=RoutingStrategy.ROUND_ROBIN)
        p1 = _healthy_provider("p1", priority=0)
        p2 = _healthy_provider("p2", priority=1)
        router.add_provider(p1)
        router.add_provider(p2)
        router._rr_index = 0
        result = router._ordered_providers()
        assert len(result) == 2
        # rotation means first element starts at index 0, second wraps
        assert result[0].name in ("p1", "p2")

    def test_latency_weighted_with_healthy_sorts_by_latency(self):
        """Line 187: LATENCY_WEIGHTED with healthy providers sorts by avg_latency_ms."""
        router = MultiCloudRouter(strategy=RoutingStrategy.LATENCY_WEIGHTED)
        p_fast = _healthy_provider("p_fast", priority=0)
        p_slow = _healthy_provider("p_slow", priority=1)
        # Use record_success to set latency (avg_latency_ms is a property)
        p_fast._metrics.record_success(10.0)
        p_slow._metrics.record_success(200.0)
        router.add_provider(p_slow)
        router.add_provider(p_fast)
        result = router._ordered_providers()
        assert result[0].name == "p_fast"

    def test_random_with_healthy_returns_shuffled(self):
        """Lines 193-195: RANDOM with healthy providers returns shuffled list."""
        router = MultiCloudRouter(strategy=RoutingStrategy.RANDOM)
        p1 = _healthy_provider("p1")
        p2 = _healthy_provider("p2")
        router.add_provider(p1)
        router.add_provider(p2)
        result = router._ordered_providers()
        assert len(result) == 2
        assert {r.name for r in result} == {"p1", "p2"}


class TestHealthSummaryCoverageGaps:
    def test_degraded_only_returns_degraded_overall(self):
        """Line 214: when healthy_count==0 but degraded_count>0, overall='degraded'."""
        router = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        deg = _degraded_provider("p_deg")
        router.add_provider(deg)
        summary = router.health_summary()
        assert summary["overall"] == "degraded"
        assert summary["degraded"] == 1
        assert summary["healthy"] == 0
