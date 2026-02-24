"""Test advanced cache invalidation strategies."""

from __future__ import annotations

from unittest.mock import Mock, patch

from tool_router.cache.invalidation import (
    AdvancedInvalidationManager,
    DependencyInvalidationManager,
    EventInvalidationManager,
    TagInvalidationManager,
    invalidate_by_dependency,
    invalidate_by_event,
    invalidate_by_tags,
)


class TestTagInvalidationManager:
    """Test tag-based cache invalidation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock()
        self.mock_cache = Mock()
        self.mock_cache_manager.get_cache.return_value = self.mock_cache
        self.tag_manager = TagInvalidationManager(self.mock_cache_manager)

    def test_create_tag(self):
        """Test tag creation."""
        tag = self.tag_manager.create_tag("test_tag", "Test description")

        assert tag.name == "test_tag"
        assert tag.description == "Test description"
        assert isinstance(tag.created_at, float)
        assert len(tag.cache_keys) == 0
        assert tag.invalidation_count == 0

    def test_create_duplicate_tag(self):
        """Test creating duplicate tag returns existing."""
        tag1 = self.tag_manager.create_tag("test_tag")
        tag2 = self.tag_manager.create_tag("test_tag")

        assert tag1 is tag2

    def test_add_to_tag(self):
        """Test adding cache key to tag."""
        result = self.tag_manager.add_to_tag("test_tag", "cache:key1")

        assert result is True
        tag = self.tag_manager.get_tag_info("test_tag")
        assert "cache:key1" in tag.cache_keys

    def test_invalidate_tag(self):
        """Test tag invalidation."""
        # Setup
        self.tag_manager.add_to_tag("test_tag", "cache:key1")
        self.tag_manager.add_to_tag("test_tag", "cache:key2")

        # Mock cache delete method
        self.mock_cache.delete.return_value = True

        # Invalidate
        count = self.tag_manager.invalidate_tag("test_tag", "Test reason")

        assert count == 2
        assert self.mock_cache.delete.call_count == 2
        assert self.mock_cache.delete.call_args_list[0][0][0] == "cache:key1"
        assert self.mock_cache.delete.call_args_list[1][0][0] == "cache:key2"

        # Verify tag is cleaned up
        tag = self.tag_manager.get_tag_info("test_tag")
        assert len(tag.cache_keys) == 0
        assert tag.invalidation_count == 1

    def test_invalidate_nonexistent_tag(self):
        """Test invalidating non-existent tag."""
        count = self.tag_manager.invalidate_tag("nonexistent")
        assert count == 0

    def test_get_tags_for_key(self):
        """Test getting tags for a cache key."""
        self.tag_manager.add_to_tag("tag1", "cache:key1")
        self.tag_manager.add_to_tag("tag2", "cache:key1")

        tags = self.tag_manager.get_tags_for_key("cache:key1")
        assert tags == {"tag1", "tag2"}

    def test_list_tags(self):
        """Test listing all tags."""
        self.tag_manager.create_tag("tag1")
        self.tag_manager.create_tag("tag2")

        tags = self.tag_manager.list_tags()
        assert len(tags) == 2
        tag_names = {tag.name for tag in tags}
        assert tag_names == {"tag1", "tag2"}


class TestEventInvalidationManager:
    """Test event-driven cache invalidation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock()
        self.mock_cache = Mock()
        self.mock_cache_manager.get_cache.return_value = self.mock_cache
        self.event_manager = EventInvalidationManager(self.mock_cache_manager)

    def test_register_handler(self):
        """Test registering event handlers."""
        handler = Mock()
        self.event_manager.register_handler("test_event", handler)

        assert "test_event" in self.event_manager._event_handlers
        assert handler in self.event_manager._event_handlers["test_event"]

    def test_trigger_invalidation(self):
        """Test triggering invalidation event."""
        # Setup handler
        handler = Mock()
        self.event_manager.register_handler("test_event", handler)

        # Mock cache delete
        self.mock_cache.delete.return_value = True

        # Trigger event
        count = self.event_manager.trigger_invalidation(
            "test_event",
            {"cache:key1", "cache:key2"},
            {"tag1"},
            "test_source",
            {"meta": "data"},
        )

        assert count == 2
        handler.assert_called_once()

        # Verify event structure
        event = handler.call_args[0][0]
        assert event.event_type == "test_event"
        assert event.cache_keys == {"cache:key1", "cache:key2"}
        assert event.tags == {"tag1"}
        assert event.source == "test_source"
        assert event.metadata == {"meta": "data"}

        # Verify cache deletion
        assert self.mock_cache.delete.call_count == 2

    def test_get_event_history(self):
        """Test getting event history."""
        # Trigger some events
        self.event_manager.trigger_invalidation("event1", {"key1"})
        self.event_manager.trigger_invalidation("event2", {"key2"})

        # Get all history
        history = self.event_manager.get_event_history()
        assert len(history) == 2

        # Get filtered history
        event1_history = self.event_manager.get_event_history("event1")
        assert len(event1_history) == 1
        assert event1_history[0].event_type == "event1"


class TestDependencyInvalidationManager:
    """Test dependency-based cache invalidation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock()
        self.mock_cache = Mock()
        self.mock_cache_manager.get_cache.return_value = self.mock_cache
        self.dependency_manager = DependencyInvalidationManager(self.mock_cache_manager)

    def test_add_dependency(self):
        """Test adding cache dependency."""
        self.dependency_manager.add_dependency(
            "cache:key1", {"cache:key2", "cache:key3"}
        )

        dep = self.dependency_manager.get_dependencies("cache:key1")
        assert dep is not None
        assert dep.cache_key == "cache:key1"
        assert dep.depends_on == {"cache:key2", "cache:key3"}

        # Check reverse dependencies
        dependents = self.dependency_manager.get_dependents("cache:key2")
        assert "cache:key1" in dependents

    def test_invalidate_dependents(self):
        """Test invalidating dependent cache entries."""
        # Setup dependencies
        self.dependency_manager.add_dependency("cache:key1", {"cache:key2"})
        self.dependency_manager.add_dependency("cache:key3", {"cache:key2"})

        # Mock cache delete
        self.mock_cache.delete.return_value = True

        # Invalidate dependents of key2
        count = self.dependency_manager.invalidate_dependents(
            "cache:key2", "Test reason"
        )

        assert count == 2
        assert self.mock_cache.delete.call_count == 2

        # Verify correct keys were invalidated
        deleted_keys = {call[0][0] for call in self.mock_cache.delete.call_args_list}
        assert deleted_keys == {"cache:key1", "cache:key3"}

    def test_get_dependents_empty(self):
        """Test getting dependents for key with no dependents."""
        dependents = self.dependency_manager.get_dependents("cache:nonexistent")
        assert dependents == set()


class TestAdvancedInvalidationManager:
    """Test advanced invalidation manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock()
        self.mock_cache = Mock()
        self.mock_cache_manager.get_cache.return_value = self.mock_cache
        self.manager = AdvancedInvalidationManager(self.mock_cache_manager)

    def test_invalidate_by_tags(self):
        """Test invalidating by tags through advanced manager."""
        # Mock tag manager
        self.manager.tag_manager.invalidate_multiple_tags = Mock(return_value=5)

        count = self.manager.invalidate_by_tags(["tag1", "tag2"], "Test reason")

        assert count == 5
        self.manager.tag_manager.invalidate_multiple_tags.assert_called_once_with(
            ["tag1", "tag2"], "Test reason"
        )

    def test_invalidate_by_event(self):
        """Test invalidating by event through advanced manager."""
        # Mock event manager
        self.manager.event_manager.trigger_invalidation = Mock(return_value=3)

        count = self.manager.invalidate_by_event(
            "test_event", {"key1", "key2"}, {"tag1"}, "test_source", {"meta": "data"}
        )

        assert count == 3
        self.manager.event_manager.trigger_invalidation.assert_called_once()

    def test_invalidate_by_dependency(self):
        """Test invalidating by dependency through advanced manager."""
        # Mock dependency manager
        self.manager.dependency_manager.invalidate_dependents = Mock(return_value=2)

        count = self.manager.invalidate_by_dependency("cache:key2", "Test reason")

        assert count == 2
        self.manager.dependency_manager.invalidate_dependents.assert_called_once_with(
            "cache:key2", "Test reason"
        )

    def test_create_tagged_cache(self):
        """Test creating tagged cache entries."""
        # Mock cache set
        self.mock_cache.set.return_value = True

        result = self.manager.create_tagged_cache(
            "test_cache", "key1", "value1", {"tag1", "tag2"}, 3600
        )

        assert result is True
        self.mock_cache.set.assert_called_once_with("test_cache:key1", "value1", 3600)

        # Verify tags were added
        assert self.manager.tag_manager.add_to_tag.call_count == 2

    def test_add_dependency(self):
        """Test adding cache dependency."""
        self.manager.add_dependency("cache:key1", {"cache:key2"})

        self.manager.dependency_manager.add_dependency.assert_called_once_with(
            "cache:key1", {"cache:key2"}
        )

    def test_get_invalidation_summary(self):
        """Test getting invalidation summary."""
        # Mock managers
        self.manager.tag_manager.list_tags.return_value = [
            Mock(invalidation_count=5),
            Mock(invalidation_count=3),
        ]
        self.manager.event_manager.get_event_history.return_value = [
            Mock(event_type="event1"),
            Mock(event_type="event2"),
            Mock(event_type="event1"),
        ]
        self.manager.dependency_manager._dependencies = {"key1": Mock(), "key2": Mock()}
        self.manager.dependency_manager._reverse_deps = {"key3": {"key1"}}

        summary = self.manager.get_invalidation_summary()

        assert summary["tags"]["total"] == 2
        assert summary["tags"]["invalidations"] == 8
        assert summary["events"]["total"] == 3
        assert set(summary["events"]["types"]) == {"event1", "event2"}
        assert summary["dependencies"]["total"] == 2
        assert summary["dependencies"]["reverse_deps"] == 1


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("tool_router.cache.invalidation.get_advanced_invalidation_manager")
    def test_invalidate_by_tags_convenience(self, mock_get_manager):
        """Test invalidate_by_tags convenience function."""
        mock_manager = Mock()
        mock_manager.invalidate_by_tags.return_value = 5
        mock_get_manager.return_value = mock_manager

        count = invalidate_by_tags(["tag1"], "reason")

        assert count == 5
        mock_manager.invalidate_by_tags.assert_called_once_with(["tag1"], "reason")

    @patch("tool_router.cache.invalidation.get_advanced_invalidation_manager")
    def test_invalidate_by_event_convenience(self, mock_get_manager):
        """Test invalidate_by_event convenience function."""
        mock_manager = Mock()
        mock_manager.invalidate_by_event.return_value = 3
        mock_get_manager.return_value = mock_manager

        count = invalidate_by_event("event", {"key1"})

        assert count == 3
        mock_manager.invalidate_by_event.assert_called_once_with(
            "event", {"key1"}, None, None, None
        )

    @patch("tool_router.cache.invalidation.get_advanced_invalidation_manager")
    def test_invalidate_by_dependency_convenience(self, mock_get_manager):
        """Test invalidate_by_dependency convenience function."""
        mock_manager = Mock()
        mock_manager.invalidate_by_dependency.return_value = 2
        mock_get_manager.return_value = mock_manager

        count = invalidate_by_dependency("key1", "reason")

        assert count == 2
        mock_manager.invalidate_by_dependency.assert_called_once_with("key1", "reason")


class TestIntegrationScenarios:
    """Test integration scenarios for invalidation strategies."""

    def test_tag_and_event_integration(self):
        """Test integration between tag and event invalidation."""
        mock_cache_manager = Mock()
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        mock_cache.delete.return_value = True

        manager = AdvancedInvalidationManager(mock_cache_manager)

        # Create tagged cache entries
        manager.create_tagged_cache(
            "cache1", "key1", "value1", {"user_data", "session"}
        )
        manager.create_tagged_cache("cache2", "key2", "value2", {"user_data"})

        # Invalidate by event with tags
        count = manager.invalidate_by_event(
            "user_update", {"cache1:key1"}, {"user_data"}
        )

        assert count == 1
        assert mock_cache.delete.call_count == 2  # Once for event, once for tag

    def test_dependency_cascade(self):
        """Test dependency cascade invalidation."""
        mock_cache_manager = Mock()
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        mock_cache.delete.return_value = True

        manager = AdvancedInvalidationManager(mock_cache_manager)

        # Setup dependency chain: A -> B -> C
        manager.add_dependency("cache:A", {"cache:B"})
        manager.add_dependency("cache:B", {"cache:C"})

        # Invalidate C (should invalidate B and A)
        count = manager.invalidate_by_dependency("cache:C")

        assert count == 2
        assert mock_cache.delete.call_count == 2


if __name__ == "__main__":
    # Simple manual test
    print("Testing advanced cache invalidation strategies...")

    from tool_router.cache.cache_manager import CacheManager

    cache_manager = CacheManager()
    manager = AdvancedInvalidationManager(cache_manager)

    # Test tag-based invalidation
    print("Testing tag-based invalidation...")
    manager.create_tagged_cache("test_cache", "key1", "value1", {"test_tag"})
    count = manager.invalidate_by_tags(["test_tag"])
    print(f"Invalidated {count} entries by tag")

    # Test event-based invalidation
    print("Testing event-based invalidation...")
    manager.create_tagged_cache("test_cache", "key2", "value2", {"event_tag"})
    count = manager.invalidate_by_event("test_event", {"test_cache:key2"})
    print(f"Invalidated {count} entries by event")

    # Test dependency-based invalidation
    print("Testing dependency-based invalidation...")
    manager.add_dependency("test_cache:key3", {"test_cache:key4"})
    count = manager.invalidate_by_dependency("test_cache:key4")
    print(f"Invalidated {count} entries by dependency")

    # Get summary
    summary = manager.get_invalidation_summary()
    print(f"Invalidation summary: {summary}")

    print("Advanced invalidation tests completed successfully!")
