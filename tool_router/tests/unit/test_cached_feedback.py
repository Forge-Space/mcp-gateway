"""Comprehensive unit tests for cached feedback module."""

import json
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from tool_router.ai.cached_feedback import (
    CachedFeedbackStore,
    FeedbackEntry,
    FeedbackStore,
    TaskPattern,
    ToolStats,
)


class TestFeedbackEntry:
    """Test FeedbackEntry dataclass."""

    def test_feedback_entry_creation(self):
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
        stats = ToolStats(
            tool_name="test_tool",
            success_count=8,
            failure_count=2,
            avg_confidence=0.6,
        )

        assert stats.total == 10
        assert stats.success_rate == 0.8
        assert stats.confidence_score == (0.8 * 0.7 + 0.6 * 0.3)

    def test_tool_stats_empty(self):
        stats = ToolStats(tool_name="empty_tool")

        assert stats.total == 0
        assert stats.success_rate == 0.5
        assert stats.confidence_score == (0.5 * 0.7 + 0.0 * 0.3)
        assert stats.task_types == {}
        assert stats.intent_categories == {}
        assert stats.recent_success_rate == 0.0


class TestTaskPattern:
    """Test TaskPattern dataclass."""

    def test_task_pattern_creation(self):
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
        pattern = TaskPattern(task_type="test_type")

        assert pattern.task_type == "test_type"
        assert pattern.preferred_tools == {}
        assert pattern.common_entities == []
        assert pattern.avg_confidence == 0.0
        assert pattern.total_occurrences == 0


class TestCachedFeedbackStore:
    """Test CachedFeedbackStore class."""

    def test_initialization_default(self, tmp_path: Path):
        temp_file = tmp_path / "test_feedback.json"
        store = CachedFeedbackStore(feedback_file=str(temp_file))

        assert store._file.name.endswith("test_feedback.json")
        assert len(store._entries) == 0
        assert len(store._stats) == 0
        assert len(store._patterns) == 0
        assert store._boost_cache.maxsize == 1000
        assert store._stats_cache.maxsize == 1000
        assert store._pattern_cache.maxsize == 1000

    def test_initialization_custom(self, tmp_path: Path):
        custom_file = tmp_path / "custom_feedback.json"
        store = CachedFeedbackStore(feedback_file=str(custom_file), cache_ttl=1800, cache_size=500)

        assert store._file == custom_file
        assert store._boost_cache.maxsize == 500
        assert store._stats_cache.maxsize == 500
        assert store._pattern_cache.maxsize == 500

    def test_classify_task_type(self):
        test_cases = [
            ("read the file.txt", "file_operations"),
            ("create new file", "file_operations"),
            ("delete old data", "file_operations"),
            ("search for information", "search_operations"),
            ("query the database", "search_operations"),
            ("fetch from api", "network_operations"),
            ("run system command", "system_operations"),
            ("edit the code", "code_operations"),
            ("general task", "general_operations"),
        ]

        for task, expected_type in test_cases:
            result = CachedFeedbackStore._classify_task_type(task)
            assert result == expected_type, f"Task '{task}' should be '{expected_type}'"

    def test_classify_intent(self):
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
        # File path extraction
        entities = CachedFeedbackStore._extract_entities("read /path/to/file.txt")
        assert "/path/to/file.txt" in entities

        # URL extraction
        entities = CachedFeedbackStore._extract_entities("visit https://example.com/api")
        assert "https://example.com/api" in entities

        # Quoted string extraction
        entities = CachedFeedbackStore._extract_entities("edit 'important file'")
        assert "important file" in entities

        # Empty input
        entities = CachedFeedbackStore._extract_entities("")
        assert entities == []

        # Short words only (all <= 2 chars) produces no entities
        entities = CachedFeedbackStore._extract_entities("a b")
        assert entities == []

    def test_record_feedback(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record(
            task="do it",
            selected_tool="test_tool",
            success=True,
            context="test context",
            confidence=0.8,
        )

        assert len(store._entries) == 1
        entry = store._entries[0]
        assert entry.selected_tool == "test_tool"
        assert entry.success is True
        assert entry.context == "test context"
        assert entry.confidence == 0.8
        assert entry.task_type == "general_operations"
        assert entry.intent_category == "unknown"

        assert "test_tool" in store._stats
        stats = store._stats["test_tool"]
        assert stats.success_count == 1
        assert stats.failure_count == 0
        assert stats.total == 1
        assert stats.success_rate == 1.0

    def test_record_multiple_feedback(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do a", "tool1", True, confidence=0.9)
        store.record("do b", "tool1", False, confidence=0.3)
        store.record("do c", "tool1", True, confidence=0.7)
        store.record("do d", "tool2", False, confidence=0.4)

        stats1 = store._stats["tool1"]
        assert stats1.success_count == 2
        assert stats1.failure_count == 1
        assert stats1.total == 3
        assert stats1.success_rate == 2 / 3
        assert stats1.avg_confidence == pytest.approx((0.9 + 0.3 + 0.7) / 3)

        stats2 = store._stats["tool2"]
        assert stats2.success_count == 0
        assert stats2.failure_count == 1
        assert stats2.total == 1
        assert stats2.success_rate == 0.0

    def test_record_with_task_classification(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("create new file", "file_tool", True, confidence=0.8)

        entry = store._entries[0]
        assert entry.task_type == "file_operations"
        assert entry.intent_category == "create"

        stats = store._stats["file_tool"]
        assert "file_operations" in stats.task_types
        assert stats.task_types["file_operations"] == 1
        assert "create" in stats.intent_categories
        assert stats.intent_categories["create"] == 1

    def test_pattern_learning(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("create file", "tool_a", True, confidence=0.8)
        store.record("create file", "tool_a", True, confidence=0.9)
        store.record("create file", "tool_b", False, confidence=0.3)
        store.record("create file", "tool_b", True, confidence=0.7)

        assert "file_operations" in store._patterns
        pattern = store._patterns["file_operations"]
        assert pattern.task_type == "file_operations"
        assert pattern.total_occurrences == 4
        assert pattern.avg_confidence == pytest.approx((0.8 + 0.9 + 0.3 + 0.7) / 4)

        assert pattern.preferred_tools["tool_a"] == 2 / 2
        assert pattern.preferred_tools["tool_b"] == 1 / 2

    def test_boost_calculation(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do a", "tool1", True, confidence=0.9)
        store.record("do b", "tool1", True, confidence=0.8)
        store.record("do c", "tool1", False, confidence=0.2)
        store.record("do d", "tool1", False, confidence=0.1)

        boost = store.get_boost("tool1")
        assert boost >= 0.1
        assert boost <= 1.7

    def test_boost_calculation_poor_performer(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do a", "poor_tool", False, confidence=0.1)
        store.record("do b", "poor_tool", False, confidence=0.2)
        store.record("do c", "poor_tool", False, confidence=0.1)

        boost = store.get_boost("poor_tool")
        assert boost < 1.0
        assert boost >= 0.1

    def test_boost_caching(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do a", "cached_tool", True, confidence=0.8)
        store.record("do b", "cached_tool", True, confidence=0.7)
        store.record("do c", "cached_tool", True, confidence=0.9)

        boost1 = store.get_boost("cached_tool")
        metrics1 = store.get_cache_metrics()

        boost2 = store.get_boost("cached_tool")
        metrics2 = store.get_cache_metrics()

        assert boost1 == boost2
        assert metrics2["hits_by_type"].get("boost", 0) > metrics1["hits_by_type"].get("boost", 0)

    def test_task_type_boost(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("create file", "file_tool", True, confidence=0.8)
        store.record("create file", "file_tool", True, confidence=0.9)
        store.record("create file", "other_tool", False, confidence=0.3)

        boost = store.get_task_type_boost("file_tool", "file_operations")
        assert boost > 1.0

    def test_intent_boost(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("create something", "intent_tool", True, confidence=0.8)
        store.record("create something", "intent_tool", True, confidence=0.9)
        store.record("create something", "intent_tool", False, confidence=0.4)

        boost = store.get_intent_boost("intent_tool", "create")
        assert boost > 1.0

    def test_comprehensive_boost(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("create file", "comp_tool", True, confidence=0.9)
        store.record("create file", "comp_tool", True, confidence=0.8)
        store.record("search file", "comp_tool", True, confidence=0.7)
        store.record("read file", "comp_tool", False, confidence=0.3)

        boost = store.get_comprehensive_boost("comp_tool", "create file")

        base_boost = store.get_boost("comp_tool")
        task_type_boost = store.get_task_type_boost("comp_tool", "file_operations")
        intent_boost = store.get_intent_boost("comp_tool", "create")

        expected = base_boost * 0.5 + task_type_boost * 0.3 + intent_boost * 0.2
        assert abs(boost - expected) < 0.001

    def test_learning_insights(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

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
        assert pattern["avg_confidence"] == pytest.approx((0.9 + 0.7 + 0.2) / 3)

        recommended = insights["recommended_tools"]
        assert len(recommended) <= 3
        assert all("tool" in rec and "success_rate" in rec for rec in recommended)

    def test_adaptive_hints(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("create file", "good_tool", True, confidence=0.95)

        hints = store.get_adaptive_hints("create file")

        assert isinstance(hints, list)

    def test_get_stats(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        assert store.get_stats("nonexistent") is None

        store.record("do it", "test_tool", True, confidence=0.8)

        stats = store.get_stats("test_tool")
        assert stats is not None
        assert stats.tool_name == "test_tool"
        assert stats.success_count == 1

    def test_get_stats_caching(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do it", "test_tool", True, confidence=0.8)

        store.get_stats("test_tool")
        metrics1 = store.get_cache_metrics()

        store.get_stats("test_tool")
        metrics2 = store.get_cache_metrics()

        assert metrics2["hits_by_type"].get("stats", 0) > metrics1["hits_by_type"].get("stats", 0)

    def test_get_all_stats(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do a", "tool1", True, confidence=0.8)
        store.record("do b", "tool2", False, confidence=0.3)

        all_stats = store.get_all_stats()
        assert len(all_stats) == 2
        assert "tool1" in all_stats
        assert "tool2" in all_stats

    def test_similar_task_tools(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("create file with content", "file_tool", True, confidence=0.8)
        store.record("create file with data", "file_tool", True, confidence=0.9)
        store.record("edit file content", "file_tool", True, confidence=0.7)
        store.record("delete file", "delete_tool", True, confidence=0.6)

        similar = store.similar_task_tools("create new file")
        assert "file_tool" in similar
        assert len(similar) <= 3

    def test_similar_task_tools_empty(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        similar = store.similar_task_tools("any task")
        assert similar == []

    def test_cache_metrics(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        metrics = store.get_cache_metrics()
        assert metrics["cache_hit_rate"] == 0.0
        assert metrics["total_hits"] == 0
        assert metrics["total_misses"] == 0
        assert metrics["total_requests"] == 0

        store.record("do it", "tool", True, confidence=0.8)
        store.record("do it", "tool", True, confidence=0.7)
        store.record("do it", "tool", True, confidence=0.9)
        store.get_boost("tool")
        store.get_boost("tool")

        metrics = store.get_cache_metrics()
        assert metrics["cache_hit_rate"] > 0.0
        assert metrics["total_hits"] > 0
        assert metrics["total_misses"] > 0
        assert metrics["total_requests"] > 0

    def test_clear_caches(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do it", "tool", True, confidence=0.8)
        store.record("do it", "tool", True, confidence=0.7)
        store.record("do it", "tool", True, confidence=0.9)
        store.get_boost("tool")
        store.get_stats("tool")

        assert len(store._boost_cache) > 0
        assert len(store._stats_cache) > 0

        store.clear_caches()

        assert len(store._boost_cache) == 0
        assert len(store._stats_cache) == 0
        assert len(store._pattern_cache) == 0

    def test_persistence_save(self, tmp_path: Path):
        feedback_file = tmp_path / "test_feedback.json"
        store = CachedFeedbackStore(feedback_file=str(feedback_file))

        store.record("do it", "test_tool", True, confidence=0.8)
        store._persist()

        assert feedback_file.exists()
        data = json.loads(feedback_file.read_text())
        assert "entries" in data
        assert "stats" in data
        assert len(data["entries"]) == 1
        assert "test_tool" in data["stats"]

    def test_persistence_load(self, tmp_path: Path):
        feedback_file = tmp_path / "test_feedback.json"

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

        store = CachedFeedbackStore(feedback_file=str(feedback_file))

        assert len(store._entries) == 1
        assert store._entries[0].task == "loaded task"
        assert "loaded_tool" in store._stats
        assert store._stats["loaded_tool"].success_count == 5

    def test_persistence_error_handling(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        with patch("pathlib.Path.write_text", side_effect=OSError("Write error")):
            store._persist()

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", side_effect=OSError("Read error")):
                store._load()

    def test_max_entries_limit(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        for i in range(1100):
            store.record(f"task_{i}", f"tool_{i % 10}", True)

        assert len(store._entries) <= 1000
        assert len(store._entries) == 1000

        first_entry = store._entries[0]
        last_entry = store._entries[-1]
        assert "task_100" in first_entry.task
        assert "task_1099" in last_entry.task

    def test_thread_safety(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))
        results = []

        def worker(thread_id):
            for i in range(10):
                store.record(
                    f"task_{thread_id}_{i}",
                    f"tool_{thread_id}",
                    i % 2 == 0,
                )
                boost = store.get_boost(f"tool_{thread_id}")
                results.append(boost)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 50

    def test_backward_compatibility(self):
        assert FeedbackStore == CachedFeedbackStore

        old_store = FeedbackStore()
        new_store = CachedFeedbackStore()

        assert type(old_store) == type(new_store)


class TestFeedbackStoreIntegration:
    """Integration tests for feedback store."""

    def test_end_to_end_workflow(self, tmp_path: Path):
        feedback_file = tmp_path / "integration_feedback.json"
        store = CachedFeedbackStore(feedback_file=str(feedback_file))

        store.record("create file", "file_creator", True, confidence=0.8)
        store.record("create file", "file_creator", True, confidence=0.9)
        store.record("create file", "file_creator", False, confidence=0.3)
        store.record("read file", "file_reader", True, confidence=0.7)

        boost = store.get_boost("file_creator")
        assert boost > 1.0

        task_type_boost = store.get_task_type_boost("file_creator", "file_operations")
        assert task_type_boost > 1.0

        insights = store.get_learning_insights("create file")
        assert "pattern" in insights
        assert insights["pattern"]["total_occurrences"] == 4

        store._persist()

        store2 = CachedFeedbackStore(feedback_file=str(feedback_file))

        assert len(store2._entries) == 4
        assert "file_creator" in store2._stats
        assert store2.get_boost("file_creator") > 1.0

    def test_cache_invalidation(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        store.record("do a", "tool1", True, confidence=0.8)
        store.record("do b", "tool1", True, confidence=0.7)
        store.record("do c", "tool1", True, confidence=0.9)

        boost1 = store.get_boost("tool1")
        assert store.get_cache_metrics()["hits_by_type"].get("boost", 0) == 0
        assert store.get_cache_metrics()["misses_by_type"].get("boost", 0) == 1

        boost2 = store.get_boost("tool1")
        assert store.get_cache_metrics()["hits_by_type"].get("boost", 0) == 1
        assert store.get_cache_metrics()["misses_by_type"].get("boost", 0) == 1

        store.record("do d", "tool1", False, confidence=0.2)

        boost3 = store.get_boost("tool1")
        assert store.get_cache_metrics()["hits_by_type"].get("boost", 0) == 1
        assert store.get_cache_metrics()["misses_by_type"].get("boost", 0) == 2

        assert boost3 != boost2

    def test_comprehensive_learning_scenario(self, tmp_path: Path):
        store = CachedFeedbackStore(feedback_file=str(tmp_path / "fb.json"))

        scenarios = [
            ("create markdown file", "markdown_tool", True, 0.9),
            ("create json file", "json_tool", True, 0.8),
            ("create yaml file", "yaml_tool", False, 0.3),
            ("read markdown file", "markdown_tool", True, 0.7),
            ("search in files", "search_tool", True, 0.8),
            ("find patterns", "search_tool", True, 0.6),
            ("grep content", "search_tool", False, 0.4),
            ("refactor code", "code_tool", True, 0.7),
            ("format code", "code_tool", True, 0.9),
            ("lint code", "code_tool", False, 0.2),
            ("run command", "system_tool", True, 0.6),
            ("execute script", "system_tool", True, 0.8),
        ]

        for task, tool, success, confidence in scenarios:
            store.record(task, tool, success, confidence=confidence)

        all_stats = store.get_all_stats()
        assert len(all_stats) == 6

        assert len(store._patterns) > 0
        assert "file_operations" in store._patterns
        assert "search_operations" in store._patterns
        assert "code_operations" in store._patterns

        comprehensive_boost = store.get_comprehensive_boost("markdown_tool", "create markdown file")

        base_boost = store.get_boost("markdown_tool")
        task_type_boost = store.get_task_type_boost("markdown_tool", "file_operations")
        intent_boost = store.get_intent_boost("markdown_tool", "create")

        expected = base_boost * 0.5 + task_type_boost * 0.3 + intent_boost * 0.2
        assert abs(comprehensive_boost - expected) < 0.001

        metrics = store.get_cache_metrics()
        assert metrics["cache_hit_rate"] >= 0.0
        assert metrics["total_requests"] > 0


if __name__ == "__main__":
    pytest.main([__file__])
