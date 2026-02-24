"""Comprehensive unit tests for cached feedback module."""

import json
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from tool_router.ai.cached_feedback import (
    CachedFeedbackStore,
    FeedbackEntry,
    FeedbackStore,  # Backward compatibility alias
    TaskPattern,
    ToolStats,
)


class TestFeedbackEntry:
    """Test FeedbackEntry dataclass."""

    def test_feedback_entry_creation(self):
        """Test creating a feedback entry with all fields."""
        entry = FeedbackEntry(
            task="test task",
            selected_tool="test_tool",
            success=True,
            context="test context",
            confidence=0.8,
            task_type="test_type",
            intent_category="create",
            entities=["entity1", "entity2"],
        )

        assert entry.task == "test task"
        assert entry.selected_tool == "test_tool"
        assert entry.success is True
        assert entry.context == "test context"
        assert entry.confidence == 0.8
        assert entry.task_type == "test_type"
        assert entry.intent_category == "create"
        assert entry.entities == ["entity1", "entity2"]
        assert isinstance(entry.timestamp, float)

    def test_feedback_entry_defaults(self):
        """Test feedback entry with default values."""
        entry = FeedbackEntry(task="test task", selected_tool="test_tool", success=False)

        assert entry.task == "test task"
        assert entry.selected_tool == "test_tool"
        assert entry.success is False
        assert entry.context == ""
        assert entry.confidence == 0.0
        assert entry.task_type == ""
        assert entry.intent_category == ""
        assert entry.entities == []
        assert isinstance(entry.timestamp, float)


class TestToolStats:
    """Test ToolStats dataclass."""

    def test_tool_stats_creation(self):
        """Test creating tool stats."""
        stats = ToolStats(
            tool_name="test_tool",
            success_count=10,
            failure_count=5,
            avg_confidence=0.75,
            task_types={"file_ops": 8, "search": 7},
            intent_categories={"create": 6, "read": 9},
            recent_success_rate=0.67,
        )

        assert stats.tool_name == "test_tool"
        assert stats.success_count == 10
        assert stats.failure_count == 5
        assert stats.avg_confidence == 0.75
        assert stats.task_types == {"file_ops": 8, "search": 7}
        assert stats.intent_categories == {"create": 6, "read": 9}
        assert stats.recent_success_rate == 0.67

    def test_tool_stats_properties(self):
        """Test tool stats calculated properties."""
        stats = ToolStats(tool_name="test_tool", success_count=8, failure_count=2, avg_confidence=0.6)

        assert stats.total == 10
        assert stats.success_rate == 0.8
        assert stats.confidence_score == (0.8 * 0.7 + 0.6 * 0.3)  # 0.74

    def test_tool_stats_empty(self):
        """Test tool stats with no data."""
        stats = ToolStats(tool_name="empty_tool")

        assert stats.total == 0
        assert stats.success_rate == 0.5  # neutral prior
        assert stats.confidence_score == (0.5 * 0.7 + 0.0 * 0.3)  # 0.35
        assert stats.task_types == {}
        assert stats.intent_categories == {}
        assert stats.recent_success_rate == 0.0


class TestTaskPattern:
    """Test TaskPattern dataclass."""

    def test_task_pattern_creation(self):
        """Test creating a task pattern."""
        pattern = TaskPattern(
            task_type="file_operations",
            preferred_tools={"tool_a": 0.8, "tool_b": 0.6},
            common_entities=["file.txt", "/path/to/file"],
            avg_confidence=0.7,
            total_occurrences=25,
        )

        assert pattern.task_type == "file_operations"
        assert pattern.preferred_tools == {"tool_a": 0.8, "tool_b": 0.6}
        assert pattern.common_entities == ["file.txt", "/path/to/file"]
        assert pattern.avg_confidence == 0.7
        assert pattern.total_occurrences == 25

    def test_task_pattern_defaults(self):
        """Test task pattern with default values."""
        pattern = TaskPattern(task_type="test_type")

        assert pattern.task_type == "test_type"
        assert pattern.preferred_tools == {}
        assert pattern.common_entities == []
        assert pattern.avg_confidence == 0.0
        assert pattern.total_occurrences == 0


class TestCachedFeedbackStore:
    """Test CachedFeedbackStore class."""

    def test_initialization_default(self):
        """Test store initialization with default parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test_feedback.json"
            store = CachedFeedbackStore(feedback_file=str(temp_file))

            assert store._file.name.endswith("test_feedback.json")
            assert len(store._entries) == 0
            assert len(store._stats) == 0
            assert len(store._patterns) == 0
            assert store._boost_cache.maxsize == 1000
            assert store._stats_cache.maxsize == 1000
            assert store._pattern_cache.maxsize == 1000

    def test_initialization_custom(self):
        """Test store initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_file = Path(temp_dir) / "custom_feedback.json"
            store = CachedFeedbackStore(feedback_file=str(custom_file), cache_ttl=1800, cache_size=500)

        assert store._file == custom_file
        assert store._boost_cache.maxsize == 500
        assert store._stats_cache.maxsize == 500
        assert store._pattern_cache.maxsize == 500

    def test_classify_task_type(self):
        """Test task type classification."""
        test_cases = [
            ("read the file.txt", "file_operations"),
            ("create new file", "file_operations"),
            ("delete old data", "file_operations"),
            ("search for information", "search_operations"),
            (
                "query the database",
                "search_operations",
            ),  # Search comes before database and "query" matches search
            ("fetch from api", "network_operations"),
            ("run system command", "system_operations"),
            ("edit the code", "code_operations"),
            ("general task", "general_operations"),
        ]

        for task, expected_type in test_cases:
            result = CachedFeedbackStore._classify_task_type(task)
            assert result == expected_type, f"Task '{task}' should be '{expected_type}'"

    def test_classify_intent(self):
        """Test intent classification."""
        test_cases = [
            ("create new file", "create"),
            ("make something", "create"),
            ("read the data", "read"),
            ("get information", "read"),
            ("update the file", "update"),
            ("modify the code", "update"),
            ("delete old data", "delete"),
            ("remove the file", "delete"),
            ("search for pattern", "search"),
            ("find the item", "search"),
            ("unknown action", "unknown"),
        ]

        for task, expected_intent in test_cases:
            result = CachedFeedbackStore._classify_intent(task)
            assert result == expected_intent, f"Task '{task}' should be '{expected_intent}'"

    def test_extract_entities(self):
        """Test entity extraction from tasks."""
        test_cases = [
            (
                "read /path/to/file.txt",
                ["/path/to/file.txt", "read"],
            ),  # The regex is broad and matches "read"
            (
                "edit 'important file'",
                ["important file", "edit", "important", "file"],
            ),  # Multiple matches
            ("visit https://example.com", ["https://example.com", "visit"]),
            ('use "quoted string" here', ["quoted string", "use"]),
            ("no entities here", []),  # No matches over 2 chars
            (
                'mixed /path/file.txt and "quoted"',
                ["/path/file.txt", "quoted", "mixed"],
            ),
        ]

        for task, expected_entities in test_cases:
            result = CachedFeedbackStore._extract_entities(task)
            assert set(result) == set(expected_entities), f"Task '{task}' entities mismatch"

    def test_record_feedback(self):
        """Test recording feedback entry."""
        store = CachedFeedbackStore()

        # Record initial feedback
        store.record(
            task="test task",
            selected_tool="test_tool",
            success=True,
            context="test context",
            confidence=0.8,
        )

        # Verify entry was created
        assert len(store._entries) == 1
        entry = store._entries[0]
        assert entry.task == "test task"
        assert entry.selected_tool == "test_tool"
        assert entry.success is True
        assert entry.context == "test context"
        assert entry.confidence == 0.8
        assert entry.task_type == "general_operations"
        assert entry.intent_category == "unknown"
        assert entry.entities == []

        # Verify stats were created
        assert "test_tool" in store._stats
        stats = store._stats["test_tool"]
        assert stats.success_count == 1
        assert stats.failure_count == 0
        assert stats.total == 1
        assert stats.success_rate == 1.0

    def test_record_multiple_feedback(self):
        """Test recording multiple feedback entries."""
        store = CachedFeedbackStore()

        # Record multiple entries
        store.record("task1", "tool1", True, confidence=0.9)
        store.record("task1", "tool1", False, confidence=0.3)
        store.record("task2", "tool1", True, confidence=0.7)
        store.record("task2", "tool2", False, confidence=0.4)

        # Verify aggregated stats for tool1
        stats1 = store._stats["tool1"]
        assert stats1.success_count == 2
        assert stats1.failure_count == 1
        assert stats1.total == 3
        assert stats1.success_rate == 2 / 3
        assert stats1.avg_confidence == (0.9 + 0.3 + 0.7) / 3

        # Verify stats for tool2
        stats2 = store._stats["tool2"]
        assert stats2.success_count == 0
        assert stats2.failure_count == 1
        assert stats2.total == 1
        assert stats2.success_rate == 0.0

    def test_record_with_task_classification(self):
        """Test recording feedback with automatic task classification."""
        store = CachedFeedbackStore()

        store.record("create new file", "file_tool", True, confidence=0.8)

        # Verify task type and intent were classified
        entry = store._entries[0]
        assert entry.task_type == "file_operations"
        assert entry.intent_category == "create"

        # Verify stats tracking
        stats = store._stats["file_tool"]
        assert "file_operations" in stats.task_types
        assert stats.task_types["file_operations"] == 1
        assert "create" in stats.intent_categories
        assert stats.intent_categories["create"] == 1

    def test_pattern_learning(self):
        """Test pattern learning from feedback."""
        store = CachedFeedbackStore()

        # Record multiple similar tasks
        store.record("create file", "tool_a", True, confidence=0.8)
        store.record("create file", "tool_a", True, confidence=0.9)
        store.record("create file", "tool_b", False, confidence=0.3)
        store.record("create file", "tool_b", True, confidence=0.7)

        # Verify pattern was created and updated
        assert "file_operations" in store._patterns
        pattern = store._patterns["file_operations"]
        assert pattern.task_type == "file_operations"
        assert pattern.total_occurrences == 4
        assert pattern.avg_confidence == (0.8 + 0.9 + 0.3 + 0.7) / 4

        # Verify tool preferences in pattern
        assert pattern.preferred_tools["tool_a"] == 2 / 2  # 100% success rate
        assert pattern.preferred_tools["tool_b"] == 1 / 2  # 50% success rate

    def test_boost_calculation(self):
        """Test boost calculation based on performance."""
        store = CachedFeedbackStore()

        # Record some performance data
        store.record("task1", "tool1", True, confidence=0.9)
        store.record("task2", "tool1", True, confidence=0.8)
        store.record("task3", "tool1", False, confidence=0.2)
        store.record("task4", "tool1", False, confidence=0.1)

        # Calculate boost
        boost = store.get_boost("tool1")

        # Should be > 1.0 due to good performance
        assert boost > 1.0
        assert boost < 2.0  # Should be clamped

    def test_boost_calculation_poor_performer(self):
        """Test boost calculation for poor performing tool."""
        store = CachedFeedbackStore()

        # Record poor performance
        store.record("task1", "poor_tool", False, confidence=0.1)
        store.record("task2", "poor_tool", False, confidence=0.2)
        store.record("task3", "poor_tool", False, confidence=0.1)

        # Calculate boost
        boost = store.get_boost("poor_tool")

        # Should be < 1.0 due to poor performance
        assert boost < 1.0
        assert boost > 0.1  # Should be clamped to minimum

    def test_boost_caching(self):
        """Test that boost results are cached."""
        store = CachedFeedbackStore()

        # Record some data
        store.record("test task", "cached_tool", True, confidence=0.8)

        # First call should calculate and cache
        boost1 = store.get_boost("cached_tool")
        cache_metrics1 = store.get_cache_metrics()

        # Second call should use cache
        boost2 = store.get_boost("cached_tool")
        cache_metrics2 = store.get_cache_metrics()

        assert boost1 == boost2
        assert cache_metrics2["cache_hits"]["boost"] > cache_metrics1["cache_hits"]["boost"]

    def test_task_type_boost(self):
        """Test task type specific boost calculation."""
        store = CachedFeedbackStore()

        # Record task type specific performance
        store.record("create file", "file_tool", True, confidence=0.8)
        store.record("create file", "file_tool", True, confidence=0.9)
        store.record("create file", "other_tool", False, confidence=0.3)

        boost = store.get_task_type_boost("file_tool", "file_operations")

        # Should be > 1.0 for good performer in this task type
        assert boost > 1.0

    def test_intent_boost(self):
        """Test intent specific boost calculation."""
        store = CachedFeedbackStore()

        # Record intent specific performance
        store.record("create something", "intent_tool", True, confidence=0.8)
        store.record("create something", "intent_tool", True, confidence=0.9)
        store.record("create something", "intent_tool", False, confidence=0.4)

        boost = store.get_intent_boost("intent_tool", "create")

        # Should be > 1.0 for good performer for this intent
        assert boost > 1.0

    def test_comprehensive_boost(self):
        """Test comprehensive boost combining all factors."""
        store = CachedFeedbackStore()

        # Record data for all factors
        store.record("create file", "comprehensive_tool", True, confidence=0.9)
        store.record("create file", "comprehensive_tool", True, confidence=0.8)
        store.record("search file", "comprehensive_tool", True, confidence=0.7)
        store.record("read file", "comprehensive_tool", False, confidence=0.3)

        boost = store.get_comprehensive_boost("comprehensive_tool", "create file")

        # Should be a weighted combination of all factors
        base_boost = store.get_boost("comprehensive_tool")
        task_type_boost = store.get_task_type_boost("comprehensive_tool", "file_operations")
        intent_boost = store.get_intent_boost("comprehensive_tool", "create")

        expected = base_boost * 0.5 + task_type_boost * 0.3 + intent_boost * 0.2
        assert abs(boost - expected) < 0.001

    def test_learning_insights(self):
        """Test learning insights generation."""
        store = CachedFeedbackStore()

        # Record some learning data
        store.record("create file", "tool_a", True, confidence=0.9)
        store.record("create file", "tool_b", True, confidence=0.7)
        store.record("create file", "tool_c", False, confidence=0.2)

        insights = store.get_learning_insights("create file")

        assert insights["task_type"] == "file_operations"
        assert insights["intent_category"] == "create"
        assert "pattern" in insights
        assert "recommended_tools" in insights
        assert "confidence_factors" in insights

        pattern = insights["pattern"]
        assert pattern["total_occurrences"] == 3
        assert pattern["avg_confidence"] == (0.9 + 0.7 + 0.2) / 3

        recommended = insights["recommended_tools"]
        assert len(recommended) <= 3
        assert all("tool" in rec and "success_rate" in rec for rec in recommended)

    def test_adaptive_hints(self):
        """Test adaptive hints generation."""
        store = CachedFeedbackStore()

        # Record some learning data
        store.record("create file", "good_tool", True, confidence=0.95)

        hints = store.get_adaptive_hints("create file")

        assert isinstance(hints, list)
        assert len(hints) > 0
        assert any("High confidence" in hint for hint in hints if "confidence" in hint)

    def test_get_stats(self):
        """Test getting stats for a tool."""
        store = CachedFeedbackStore()

        # No data yet
        assert store.get_stats("nonexistent") is None

        # Add some data
        store.record("test task", "test_tool", True, confidence=0.8)

        stats = store.get_stats("test_tool")
        assert stats is not None
        assert stats.tool_name == "test_tool"
        assert stats.success_count == 1

    def test_get_stats_caching(self):
        """Test stats caching."""
        store = CachedFeedbackStore()

        store.record("test task", "test_tool", True, confidence=0.8)

        # First call
        stats1 = store.get_stats("test_tool")
        cache_metrics1 = store.get_cache_metrics()

        # Second call should use cache
        stats2 = store.get_stats("test_tool")
        cache_metrics2 = store.get_cache_metrics()

        assert stats1 == stats2
        assert cache_metrics2["cache_hits"]["stats"] > cache_metrics1["cache_hits"]["stats"]

    def test_get_all_stats(self):
        """Test getting all stats."""
        store = CachedFeedbackStore()

        store.record("task1", "tool1", True, confidence=0.8)
        store.record("task2", "tool2", False, confidence=0.3)

        all_stats = store.get_all_stats()
        assert len(all_stats) == 2
        assert "tool1" in all_stats
        assert "tool2" in all_stats

    def test_similar_task_tools(self):
        """Test finding tools for similar tasks."""
        store = CachedFeedbackStore()

        # Record some similar successful tasks
        store.record("create file with content", "file_tool", True, confidence=0.8)
        store.record("create file with data", "file_tool", True, confidence=0.9)
        store.record("edit file content", "file_tool", True, confidence=0.7)
        store.record("delete file", "delete_tool", True, confidence=0.6)
        store.record("create file", "file_tool", False, confidence=0.2)  # Failed, shouldn't be included

        similar = store.similar_task_tools("create new file")

        assert "file_tool" in similar
        assert len(similar) <= 3

    def test_similar_task_tools_empty(self):
        """Test similar task tools with no data."""
        store = CachedFeedbackStore()

        similar = store.similar_task_tools("any task")
        assert similar == []

    def test_cache_metrics(self):
        """Test cache performance metrics."""
        store = CachedFeedbackStore()

        # Initially no cache activity
        metrics = store.get_cache_metrics()
        assert metrics["cache_hit_rate"] == 0.0
        assert metrics["total_hits"] == 0
        assert metrics["total_misses"] == 0
        assert metrics["total_requests"] == 0

        # Add some cache activity
        store.record("test", "tool", True, confidence=0.8)
        store.get_boost("tool")  # Cache miss, then hit
        store.get_boost("tool")  # Cache hit

        metrics = store.get_cache_metrics()
        assert metrics["cache_hit_rate"] > 0.0
        assert metrics["total_hits"] > 0
        assert metrics["total_misses"] > 0
        assert metrics["total_requests"] > 0

    def test_clear_caches(self):
        """Test clearing all caches."""
        store = CachedFeedbackStore()

        # Add some data to caches
        store.record("test", "tool", True, confidence=0.8)
        store.get_boost("tool")
        store.get_stats("tool")

        # Verify caches have data
        assert len(store._boost_cache) > 0
        assert len(store._stats_cache) > 0

        # Clear caches
        store.clear_caches()

        # Verify caches are empty
        assert len(store._boost_cache) == 0
        assert len(store._stats_cache) == 0
        assert len(store._pattern_cache) == 0

    def test_persistence_save(self):
        """Test saving feedback to disk."""
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_file = Path(temp_dir) / "test_feedback.json"
            store = CachedFeedbackStore(feedback_file=str(feedback_file))

            # Add some data
            store.record("test task", "test_tool", True, confidence=0.8)

            # Trigger persistence
            store._persist()

            # Verify file was created and has data
            assert feedback_file.exists()
            data = json.loads(feedback_file.read_text())
            assert "entries" in data
            assert "stats" in data
            assert len(data["entries"]) == 1
            assert "test_tool" in data["stats"]

    def test_persistence_load(self):
        """Test loading feedback from disk."""
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_file = Path(temp_dir) / "test_feedback.json"

            # Create test data file
            test_data = {
                "entries": [
                    {
                        "task": "loaded task",
                        "selected_tool": "loaded_tool",
                        "success": True,
                        "context": "loaded context",
                        "confidence": 0.7,
                        "timestamp": 1234567890.0,
                        "task_type": "loaded_type",
                        "intent_category": "loaded_intent",
                        "entities": ["loaded_entity"],
                    }
                ],
                "stats": {
                    "loaded_tool": {
                        "tool_name": "loaded_tool",
                        "success_count": 5,
                        "failure_count": 2,
                        "avg_confidence": 0.75,
                        "task_types": {"loaded_type": 3},
                        "intent_categories": {"loaded_intent": 4},
                        "recent_success_rate": 0.6,
                    }
                },
            }
            feedback_file.write_text(json.dumps(test_data, indent=2))

            # Load store from file
            store = CachedFeedbackStore(feedback_file=str(feedback_file))

            # Verify data was loaded
            assert len(store._entries) == 1
            assert store._entries[0].task == "loaded task"
            assert "loaded_tool" in store._stats
            assert store._stats["loaded_tool"].success_count == 5

    def test_persistence_error_handling(self):
        """Test persistence error handling."""
        store = CachedFeedbackStore()

        # Mock file operations to raise exception
        with patch.object(store._file, "write_text", side_effect=OSError("Write error")):
            # Should not raise exception
            store._persist()

        with patch.object(store._file, "exists", return_value=True):
            with patch.object(store._file, "read_text", side_effect=OSError("Read error")):
                # Should not raise exception
                store._load()

    def test_max_entries_limit(self):
        """Test that entries are trimmed when exceeding max limit."""
        store = CachedFeedbackStore()

        # Add more entries than the limit
        for i in range(1100):  # Exceeds _MAX_ENTRIES (1000)
            store.record(f"task_{i}", "tool_{i % 10}", True)

        # Should be trimmed to max entries
        assert len(store._entries) <= 1000
        assert len(store._entries) == 1000

        # Should keep the most recent entries
        first_entry = store._entries[0]
        last_entry = store._entries[-1]
        assert "task_100" in last_entry.task  # Most recent
        assert "task_0" not in first_entry.task  # Oldest was trimmed

    def test_thread_safety(self):
        """Test thread safety of cache operations."""
        store = CachedFeedbackStore()
        results = []

        def worker(thread_id):
            for i in range(10):
                store.record(f"task_{thread_id}_{i}", f"tool_{thread_id}", i % 2 == 0)
                boost = store.get_boost(f"tool_{thread_id}")
                results.append(boost)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all operations completed without errors
        assert len(results) == 50  # 5 threads * 10 operations each

    def test_backward_compatibility(self):
        """Test backward compatibility alias."""
        # Test that FeedbackStore is the same as CachedFeedbackStore
        assert FeedbackStore == CachedFeedbackStore

        # Test that we can create using the old name
        old_store = FeedbackStore()
        new_store = CachedFeedbackStore()

        assert type(old_store) == type(new_store)


class TestFeedbackStoreIntegration:
    """Integration tests for feedback store."""

    def test_end_to_end_workflow(self):
        """Test complete feedback learning workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_file = Path(temp_dir) / "integration_feedback.json"
            store = CachedFeedbackStore(feedback_file=str(feedback_file))

            # Phase 1: Initial learning
            store.record("create file", "file_creator", True, confidence=0.8)
            store.record("create file", "file_creator", True, confidence=0.9)
            store.record("create file", "file_creator", False, confidence=0.3)
            store.record("read file", "file_reader", True, confidence=0.7)

            # Phase 2: Learning application
            boost = store.get_boost("file_creator")
            assert boost > 1.0  # Should be boosted due to good performance

            task_type_boost = store.get_task_type_boost("file_creator", "file_operations")
            assert task_type_boost > 1.0

            insights = store.get_learning_insights("create file")
            assert "pattern" in insights
            assert insights["pattern"]["total_occurrences"] == 3

            # Phase 3: Persistence and recovery
            store._persist()

            # Create new store instance (simulating restart)
            store2 = CachedFeedbackStore(feedback_file=str(feedback_file))

            # Verify data was recovered
            assert len(store2._entries) == 4
            assert "file_creator" in store2._stats
            assert store2.get_boost("file_creator") > 1.0

    def test_cache_invalidation(self):
        """Test that caches are properly invalidated."""
        store = CachedFeedbackStore()

        # Record initial data
        store.record("task1", "tool1", True, confidence=0.8)

        # Cache the result
        boost1 = store.get_boost("tool1")
        assert store.get_cache_metrics()["cache_hits"]["boost"] == 0
        assert store.get_cache_metrics()["cache_misses"]["boost"] == 1

        # Second call should hit cache
        boost2 = store.get_boost("tool1")
        assert store.get_cache_metrics()["cache_hits"]["boost"] == 1
        assert store.get_cache_metrics()["cache_misses"]["boost"] == 1

        # Record new data should invalidate cache
        store.record("task2", "tool1", False, confidence=0.2)

        # Next call should miss cache
        boost3 = store.get_boost("tool1")
        assert store.get_cache_metrics()["cache_hits"]["boost"] == 1
        assert store.get_cache_metrics()["cache_misses"]["boost"] == 2

        # Boost should be different due to new data
        assert boost3 != boost2

    def test_comprehensive_learning_scenario(self):
        """Test comprehensive learning scenario with multiple tools and tasks."""
        store = CachedFeedbackStore()

        # Simulate realistic usage pattern
        scenarios = [
            # File operations
            ("create markdown file", "markdown_tool", True, 0.9),
            ("create json file", "json_tool", True, 0.8),
            ("create yaml file", "yaml_tool", False, 0.3),
            ("read markdown file", "markdown_tool", True, 0.7),
            # Search operations
            ("search in files", "search_tool", True, 0.8),
            ("find patterns", "search_tool", True, 0.6),
            ("grep content", "search_tool", False, 0.4),
            # Code operations
            ("refactor code", "code_tool", True, 0.7),
            ("format code", "code_tool", True, 0.9),
            ("lint code", "code_tool", False, 0.2),
            # System operations
            ("run command", "system_tool", True, 0.6),
            ("execute script", "system_tool", True, 0.8),
        ]

        # Record all scenarios
        for task, tool, success, confidence in scenarios:
            store.record(task, tool, success, confidence=confidence)

        # Verify learning occurred
        all_stats = store.get_all_stats()
        assert len(all_stats) == 6  # 6 unique tools

        # Verify patterns were learned
        assert len(store._patterns) > 0
        assert "file_operations" in store._patterns
        assert "search_operations" in store._patterns
        assert "code_operations" in store._patterns

        # Test comprehensive boost calculation
        comprehensive_boost = store.get_comprehensive_boost("markdown_tool", "create markdown file")

        # Should consider all learning factors
        base_boost = store.get_boost("markdown_tool")
        task_type_boost = store.get_task_type_boost("markdown_tool", "file_operations")
        intent_boost = store.get_intent_boost("markdown_tool", "create")

        expected = base_boost * 0.5 + task_type_boost * 0.3 + intent_boost * 0.2
        assert abs(comprehensive_boost - expected) < 0.001

        # Verify cache metrics show good performance
        metrics = store.get_cache_metrics()
        assert metrics["cache_hit_rate"] > 0.5  # Should have some cache hits
        assert metrics["total_requests"] > 0


if __name__ == "__main__":
    pytest.main([__file__])
