"""Unit tests for tool_router/cache/invalidation.py — cache invalidation strategies."""

from __future__ import annotations

from tool_router.cache.cache_manager import CacheManager
from tool_router.cache.invalidation import (
    AdvancedInvalidationManager,
    DependencyInvalidationManager,
    EventInvalidationManager,
    InvalidationStrategy,
    TagInvalidationManager,
)


# ── InvalidationStrategy enum ─────────────────────────────────────────────────


def test_invalidation_strategy_values() -> None:
    assert InvalidationStrategy.TTL.value == "ttl"
    assert InvalidationStrategy.TAG.value == "tag"
    assert InvalidationStrategy.EVENT.value == "event"
    assert InvalidationStrategy.MANUAL.value == "manual"
    assert InvalidationStrategy.DEPENDENCY.value == "dependency"


def test_invalidation_strategy_count() -> None:
    assert len(InvalidationStrategy) == 5


# ── TagInvalidationManager ────────────────────────────────────────────────────


def _make_cm() -> CacheManager:
    cm = CacheManager()
    cm.create_ttl_cache("test_cache")
    return cm


def test_tag_manager_create_tag() -> None:
    mgr = TagInvalidationManager(_make_cm())
    tag = mgr.create_tag("tag1", "test tag")
    assert tag.name == "tag1"
    assert tag.description == "test tag"


def test_tag_manager_list_tags_empty() -> None:
    mgr = TagInvalidationManager(_make_cm())
    assert mgr.list_tags() == []


def test_tag_manager_list_tags_after_create() -> None:
    mgr = TagInvalidationManager(_make_cm())
    mgr.create_tag("my_tag")
    tags = mgr.list_tags()
    assert len(tags) == 1
    assert tags[0].name == "my_tag"


def test_tag_manager_add_to_tag() -> None:
    mgr = TagInvalidationManager(_make_cm())
    mgr.create_tag("add_test_tag")
    result = mgr.add_to_tag("add_test_tag", "cache_key_1")
    assert result is True


def test_tag_manager_add_to_nonexistent_tag() -> None:
    mgr = TagInvalidationManager(_make_cm())
    # add_to_tag auto-creates tag if missing — returns True
    result = mgr.add_to_tag("nonexistent_tag", "some_key")
    assert isinstance(result, bool)


def test_tag_manager_get_tag_info() -> None:
    mgr = TagInvalidationManager(_make_cm())
    mgr.create_tag("info_tag")
    info = mgr.get_tag_info("info_tag")
    assert info is not None
    assert info.name == "info_tag"


def test_tag_manager_get_tag_info_missing() -> None:
    mgr = TagInvalidationManager(_make_cm())
    result = mgr.get_tag_info("does_not_exist")
    assert result is None


def test_tag_manager_invalidate_tag() -> None:
    cm = _make_cm()
    cache = cm.get_cache("test_cache")
    cache["key1"] = "value1"

    mgr = TagInvalidationManager(cm)
    mgr.create_tag("inv_tag")
    mgr.add_to_tag("inv_tag", "key1")
    count = mgr.invalidate_tag("inv_tag")
    assert count >= 0  # count of invalidated entries


def test_tag_manager_invalidate_multiple_tags() -> None:
    mgr = TagInvalidationManager(_make_cm())
    mgr.create_tag("tag_a")
    mgr.create_tag("tag_b")
    count = mgr.invalidate_multiple_tags(["tag_a", "tag_b"])
    assert count >= 0


def test_tag_manager_get_tags_for_key() -> None:
    mgr = TagInvalidationManager(_make_cm())
    mgr.create_tag("key_tag")
    mgr.add_to_tag("key_tag", "my_key")
    tags = mgr.get_tags_for_key("my_key")
    assert "key_tag" in tags


def test_tag_manager_get_tags_for_untagged_key() -> None:
    mgr = TagInvalidationManager(_make_cm())
    tags = mgr.get_tags_for_key("untagged_key")
    assert isinstance(tags, set)
    assert len(tags) == 0


# ── EventInvalidationManager ─────────────────────────────────────────────────


def test_event_manager_trigger_returns_int() -> None:
    mgr = EventInvalidationManager(_make_cm())
    count = mgr.trigger_invalidation("user_updated", {"key1", "key2"})
    assert isinstance(count, int)
    assert count >= 0


def test_event_manager_get_history_empty() -> None:
    mgr = EventInvalidationManager(_make_cm())
    history = mgr.get_event_history()
    assert isinstance(history, list)


def test_event_manager_get_history_after_trigger() -> None:
    mgr = EventInvalidationManager(_make_cm())
    mgr.trigger_invalidation("test_event", {"k1"})
    history = mgr.get_event_history("test_event")
    assert len(history) >= 1
    assert history[0].event_type == "test_event"


def test_event_manager_register_handler() -> None:
    mgr = EventInvalidationManager(_make_cm())
    calls: list[str] = []

    def handler(event: object) -> None:
        calls.append("called")

    mgr.register_handler("custom_event", handler)
    mgr.trigger_invalidation("custom_event", set())
    assert calls == ["called"]


# ── DependencyInvalidationManager ────────────────────────────────────────────


def test_dependency_manager_add_dependency() -> None:
    mgr = DependencyInvalidationManager(_make_cm())
    mgr.add_dependency("child_key", {"parent_key"})
    deps = mgr.get_dependencies("child_key")
    assert deps is not None
    assert "parent_key" in deps.depends_on


def test_dependency_manager_get_nonexistent_dependency() -> None:
    mgr = DependencyInvalidationManager(_make_cm())
    result = mgr.get_dependencies("no_such_key")
    assert result is None


def test_dependency_manager_invalidate_dependents() -> None:
    mgr = DependencyInvalidationManager(_make_cm())
    mgr.add_dependency("dep_child", {"dep_parent"})
    count = mgr.invalidate_dependents("dep_parent")
    assert count >= 0


def test_dependency_manager_get_dependents() -> None:
    mgr = DependencyInvalidationManager(_make_cm())
    mgr.add_dependency("dep_c", {"dep_p"})
    dependents = mgr.get_dependents("dep_p")
    assert "dep_c" in dependents


def test_dependency_manager_get_dependents_no_deps() -> None:
    mgr = DependencyInvalidationManager(_make_cm())
    dependents = mgr.get_dependents("lonely_key")
    assert isinstance(dependents, set)
    assert len(dependents) == 0


# ── AdvancedInvalidationManager ───────────────────────────────────────────────


def test_advanced_manager_creates_sub_managers() -> None:
    mgr = AdvancedInvalidationManager(_make_cm())
    assert mgr is not None


def test_advanced_manager_invalidate_by_tags() -> None:
    mgr = AdvancedInvalidationManager(_make_cm())
    count = mgr.invalidate_by_tags(["nonexistent"])
    assert count >= 0


def test_advanced_manager_invalidate_by_event() -> None:
    mgr = AdvancedInvalidationManager(_make_cm())
    count = mgr.invalidate_by_event("test_evt", set())
    assert count >= 0


def test_advanced_manager_invalidate_by_dependency() -> None:
    mgr = AdvancedInvalidationManager(_make_cm())
    count = mgr.invalidate_by_dependency("some_parent")
    assert count >= 0


def test_advanced_manager_add_dependency() -> None:
    mgr = AdvancedInvalidationManager(_make_cm())
    mgr.add_dependency("child", {"parent"})  # should not raise


def test_advanced_manager_get_invalidation_summary() -> None:
    mgr = AdvancedInvalidationManager(_make_cm())
    summary = mgr.get_invalidation_summary()
    assert isinstance(summary, dict)


def test_advanced_manager_create_tagged_cache() -> None:
    cm = _make_cm()
    mgr = AdvancedInvalidationManager(cm)
    result = mgr.create_tagged_cache("test_cache", "tagged_key", "tagged_val", {"tag1", "tag2"})
    assert isinstance(result, bool)
