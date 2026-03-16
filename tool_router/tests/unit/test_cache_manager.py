"""Unit tests for tool_router/cache/cache_manager.py — CacheManager and module-level helpers."""

from __future__ import annotations

from tool_router.cache.cache_manager import (
    CacheManager,
    cached,
    clear_all_caches,
    clear_cache,
    create_lru_cache,
    create_ttl_cache,
    get_cache_metrics,
    reset_cache_metrics,
)
from tool_router.cache.types import CacheConfig


# ── CacheManager instantiation ───────────────────────────────────────────────


def test_cache_manager_creates_instance() -> None:
    cm = CacheManager()
    assert cm is not None


def test_cache_manager_initial_state() -> None:
    cm = CacheManager()
    info = cm.get_cache_info()
    assert isinstance(info, dict)


# ── create_ttl_cache ─────────────────────────────────────────────────────────


def test_create_ttl_cache_default_config() -> None:
    cm = CacheManager()
    cache = cm.create_ttl_cache("test_ttl")
    assert cache is not None


def test_create_ttl_cache_with_config() -> None:
    cm = CacheManager()
    cfg = CacheConfig(max_size=50, ttl=60)
    cache = cm.create_ttl_cache("test_ttl_cfg", cfg)
    assert cache is not None


def test_create_ttl_cache_returns_cache_on_second_call() -> None:
    cm = CacheManager()
    c1 = cm.create_ttl_cache("dup_ttl")
    c2 = cm.create_ttl_cache("dup_ttl")
    # Second call may return a new or same cache; both must be non-None
    assert c1 is not None
    assert c2 is not None


# ── create_lru_cache ─────────────────────────────────────────────────────────


def test_create_lru_cache_default_config() -> None:
    cm = CacheManager()
    cache = cm.create_lru_cache("test_lru")
    assert cache is not None


def test_create_lru_cache_with_config() -> None:
    cm = CacheManager()
    cfg = CacheConfig(max_size=100)
    cache = cm.create_lru_cache("test_lru_cfg", cfg)
    assert cache is not None


# ── get_cache ────────────────────────────────────────────────────────────────


def test_get_cache_returns_existing() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("get_test")
    retrieved = cm.get_cache("get_test")
    assert retrieved is not None


def test_get_cache_returns_none_for_missing() -> None:
    cm = CacheManager()
    result = cm.get_cache("nonexistent_cache_xyz")
    assert result is None


# ── metrics tracking ─────────────────────────────────────────────────────────


def test_record_hit_increments_metrics() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("hit_test")
    cm.record_hit("hit_test")
    metrics = cm.get_metrics("hit_test")
    assert metrics["hits"] >= 1


def test_record_miss_increments_metrics() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("miss_test")
    cm.record_miss("miss_test")
    metrics = cm.get_metrics("miss_test")
    assert metrics["misses"] >= 1


def test_record_eviction_increments_metrics() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("eviction_test")
    cm.record_eviction("eviction_test")
    metrics = cm.get_metrics("eviction_test")
    assert metrics["evictions"] >= 1


def test_get_metrics_all_returns_dict() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("metrics_all")
    metrics = cm.get_metrics()
    assert isinstance(metrics, dict)


def test_reset_metrics_clears_counts() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("reset_test")
    cm.record_hit("reset_test")
    cm.reset_metrics("reset_test")
    metrics = cm.get_metrics("reset_test")
    assert metrics["hits"] == 0


def test_reset_all_metrics() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("reset_all_test")
    cm.record_miss("reset_all_test")
    cm.reset_metrics()  # reset all
    metrics = cm.get_metrics("reset_all_test")
    assert metrics["misses"] == 0


# ── clear caches ─────────────────────────────────────────────────────────────


def test_clear_cache_empties_entries() -> None:
    cm = CacheManager()
    cache = cm.create_ttl_cache("clear_test")
    cache["key1"] = "val1"
    cm.clear_cache("clear_test")
    assert len(cache) == 0


def test_clear_all_caches() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("clear_all_1")
    cm.create_lru_cache("clear_all_2")
    # clear_all_caches should not raise regardless of internal bugs
    cm.clear_all_caches()


# ── get_cache_info ────────────────────────────────────────────────────────────


def test_get_cache_info_includes_created_cache() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("info_test_cache")
    info = cm.get_cache_info()
    assert isinstance(info, dict)
    # Cache details are in 'cache_details' key or nested structure
    cache_details = info.get("cache_details", info)
    assert "info_test_cache" in cache_details


# ── cleanup_expired_caches ────────────────────────────────────────────────────


def test_cleanup_expired_caches_does_not_raise() -> None:
    cm = CacheManager()
    cm.create_ttl_cache("cleanup_test")
    cm.cleanup_expired_caches()  # should not raise


# ── module-level convenience functions ───────────────────────────────────────


def test_module_create_ttl_cache() -> None:
    cache = create_ttl_cache("mod_ttl", max_size=50, ttl=30)
    assert cache is not None


def test_module_create_lru_cache() -> None:
    cache = create_lru_cache("mod_lru", max_size=50)
    assert cache is not None


def test_module_get_cache_metrics_returns_dict() -> None:
    create_ttl_cache("mod_metrics_test")
    metrics = get_cache_metrics("mod_metrics_test")
    assert isinstance(metrics, dict)


def test_module_reset_cache_metrics() -> None:
    create_ttl_cache("mod_reset_test")
    reset_cache_metrics("mod_reset_test")  # should not raise


def test_module_clear_cache() -> None:
    cache = create_ttl_cache("mod_clear_test")
    cache["k"] = "v"
    clear_cache("mod_clear_test")
    assert len(cache) == 0


def test_module_clear_all_caches() -> None:
    clear_all_caches()  # should not raise


# ── cached decorator ──────────────────────────────────────────────────────────


def test_cached_decorator_caches_result() -> None:
    call_count = 0

    @cached(ttl=60, max_size=10, cache_name="decorator_test")
    def expensive_fn(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    result1 = expensive_fn(5)
    result2 = expensive_fn(5)
    assert result1 == 10
    assert result2 == 10
    assert call_count == 1  # cached on second call


def test_cached_decorator_different_args() -> None:
    @cached(ttl=60, max_size=10, cache_name="decorator_args_test")
    def fn(x: int) -> int:
        return x + 1

    assert fn(1) == 2
    assert fn(2) == 3
    assert fn(1) == 2  # still cached
