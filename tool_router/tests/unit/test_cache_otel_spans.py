"""Tests for OTel spans in cache_manager.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tool_router.cache.cache_manager import CacheManager, cached


class TestCacheHitSpan:
    """Tests for cache.hit span in record_hit."""

    def test_record_hit_creates_span(self):
        """record_hit creates a cache.hit span."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx) as mock_sc:
            manager.record_hit("test_cache")
            mock_sc.assert_called_once_with("cache.hit")

    def test_record_hit_sets_cache_name_attr(self):
        """record_hit sets cache.name span attribute."""
        manager = CacheManager()
        manager.create_ttl_cache("my_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            manager.record_hit("my_cache")
            mock_span.set_attribute.assert_any_call("cache.name", "my_cache")

    def test_record_hit_sets_outcome_attr(self):
        """record_hit sets cache.outcome=hit span attribute."""
        manager = CacheManager()
        manager.create_ttl_cache("my_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            manager.record_hit("my_cache")
            mock_span.set_attribute.assert_any_call("cache.outcome", "hit")

    def test_record_hit_updates_metrics(self):
        """record_hit still updates metrics when span is active."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            manager.record_hit("test_cache")

        metrics = manager.get_metrics("test_cache")
        assert metrics["hits"] == 1
        assert metrics["total_requests"] == 1

    def test_record_hit_no_span_context(self):
        """record_hit works when SpanContext is None (no OTel)."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        with patch("tool_router.cache.cache_manager.SpanContext", None):
            manager.record_hit("test_cache")

        metrics = manager.get_metrics("test_cache")
        assert metrics["hits"] == 1


class TestCacheMissSpan:
    """Tests for cache.miss span in record_miss."""

    def test_record_miss_creates_span(self):
        """record_miss creates a cache.miss span."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx) as mock_sc:
            manager.record_miss("test_cache")
            mock_sc.assert_called_once_with("cache.miss")

    def test_record_miss_sets_outcome_attr(self):
        """record_miss sets cache.outcome=miss span attribute."""
        manager = CacheManager()
        manager.create_ttl_cache("my_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            manager.record_miss("my_cache")
            mock_span.set_attribute.assert_any_call("cache.outcome", "miss")

    def test_record_miss_updates_metrics(self):
        """record_miss still updates metrics when span is active."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            manager.record_miss("test_cache")

        metrics = manager.get_metrics("test_cache")
        assert metrics["misses"] == 1
        assert metrics["total_requests"] == 1

    def test_record_miss_no_span_context(self):
        """record_miss works when SpanContext is None."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        with patch("tool_router.cache.cache_manager.SpanContext", None):
            manager.record_miss("test_cache")

        metrics = manager.get_metrics("test_cache")
        assert metrics["misses"] == 1


class TestCacheEvictionSpan:
    """Tests for cache.eviction span in record_eviction."""

    def test_record_eviction_creates_span(self):
        """record_eviction creates a cache.eviction span."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx) as mock_sc:
            manager.record_eviction("test_cache")
            mock_sc.assert_called_once_with("cache.eviction")

    def test_record_eviction_sets_cache_name_attr(self):
        """record_eviction sets cache.name span attribute."""
        manager = CacheManager()
        manager.create_ttl_cache("evict_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            manager.record_eviction("evict_cache")
            mock_span.set_attribute.assert_any_call("cache.name", "evict_cache")

    def test_record_eviction_updates_metrics(self):
        """record_eviction still updates metrics when span is active."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            manager.record_eviction("test_cache")

        metrics = manager.get_metrics("test_cache")
        assert metrics["evictions"] == 1

    def test_record_eviction_no_span_context(self):
        """record_eviction works when SpanContext is None."""
        manager = CacheManager()
        manager.create_ttl_cache("test_cache")

        with patch("tool_router.cache.cache_manager.SpanContext", None):
            manager.record_eviction("test_cache")

        metrics = manager.get_metrics("test_cache")
        assert metrics["evictions"] == 1


class TestCachedDecoratorSpan:
    """Tests for cache.lookup span in cached decorator."""

    def test_cached_decorator_hit_creates_span(self):
        """cached decorator creates cache.lookup span on cache hit."""
        call_count = 0

        @cached(ttl=60, max_size=10, cache_name="test_fn_cache")
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Prime the cache
        with patch("tool_router.cache.cache_manager.SpanContext", None):
            my_func(5)

        # Now test with span
        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx) as mock_sc:
            result = my_func(5)
            assert result == 10
            mock_sc.assert_any_call("cache.lookup")

    def test_cached_decorator_hit_sets_outcome(self):
        """cached decorator sets cache.outcome=hit on cache hit."""

        @cached(ttl=60, max_size=10, cache_name="test_fn_hit_cache")
        def my_func(x):
            return x + 1

        # Prime the cache
        with patch("tool_router.cache.cache_manager.SpanContext", None):
            my_func(3)

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            my_func(3)
            mock_span.set_attribute.assert_any_call("cache.outcome", "hit")

    def test_cached_decorator_miss_sets_outcome(self):
        """cached decorator sets cache.outcome=miss on cache miss."""

        @cached(ttl=60, max_size=10, cache_name="test_fn_miss_cache")
        def my_func(x):
            return x + 1

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            my_func(99)
            mock_span.set_attribute.assert_any_call("cache.outcome", "miss")

    def test_cached_decorator_sets_function_attr(self):
        """cached decorator sets cache.function span attribute."""

        @cached(ttl=60, max_size=10, cache_name="test_fn_attr_cache")
        def my_special_func(x):
            return x

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            my_special_func(1)
            mock_span.set_attribute.assert_any_call("cache.function", "my_special_func")

    def test_cached_decorator_no_span_context(self):
        """cached decorator works when SpanContext is None."""

        @cached(ttl=60, max_size=10, cache_name="test_fn_no_span")
        def my_func(x):
            return x * 3

        with patch("tool_router.cache.cache_manager.SpanContext", None):
            result = my_func(4)
            assert result == 12
            result2 = my_func(4)
            assert result2 == 12

    def test_cached_decorator_span_closed_on_exception(self):
        """cached decorator closes span even if function raises."""

        @cached(ttl=60, max_size=10, cache_name="test_fn_exc_cache")
        def my_func(x):
            raise ValueError("oops")

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("tool_router.cache.cache_manager.SpanContext", return_value=mock_ctx):
            with pytest.raises(ValueError):
                my_func(1)
            # __exit__ must be called at least once (cache.lookup span + cache.miss span)
            assert mock_ctx.__exit__.call_count >= 1
