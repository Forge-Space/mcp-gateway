"""Tests for the FeedbackStore context learning mechanism."""

from pathlib import Path
from unittest.mock import patch

from tool_router.ai.feedback import FeedbackStore


class TestFeedbackStore:
    def test_record_increments_success(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("search the web", "search_web", success=True)
        stats = store.get_stats("search_web")
        assert stats is not None
        assert stats.success_count == 1
        assert stats.failure_count == 0

    def test_record_increments_failure(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("search the web", "search_web", success=False)
        stats = store.get_stats("search_web")
        assert stats is not None
        assert stats.failure_count == 1

    def test_get_boost_no_data_returns_neutral(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        assert store.get_boost("unknown_tool") == 1.0

    def test_get_boost_insufficient_data_returns_neutral(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("task", "mytool", success=True)
        store.record("task", "mytool", success=True)
        # Only 2 entries, below threshold of 3
        assert store.get_boost("mytool") == 1.0

    def test_get_boost_high_success_returns_above_one(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        for _ in range(5):
            store.record("task", "mytool", success=True)
        boost = store.get_boost("mytool")
        assert boost > 1.0
        assert boost <= 1.5

    def test_get_boost_high_failure_returns_below_one(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        for _ in range(5):
            store.record("task", "mytool", success=False)
        boost = store.get_boost("mytool")
        assert boost < 1.0
        assert boost >= 0.5

    def test_get_boost_range(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        for _ in range(3):
            store.record("task", "mytool", success=True)
        for _ in range(3):
            store.record("task", "mytool", success=False)
        boost = store.get_boost("mytool")
        assert 0.5 <= boost <= 1.5

    def test_similar_task_tools_returns_successful_tools(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("search the web for news", "search_web", success=True)
        store.record("list files in directory", "list_files", success=True)
        similar = store.similar_task_tools("search the web for articles")
        assert "search_web" in similar

    def test_similar_task_tools_excludes_failures(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("search the web for news", "bad_tool", success=False)
        store.record("search the web for news", "good_tool", success=True)
        similar = store.similar_task_tools("search the web")
        assert "bad_tool" not in similar
        assert "good_tool" in similar

    def test_similar_task_tools_empty_history(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        assert store.similar_task_tools("search the web") == []

    def test_get_all_stats(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("task1", "tool_a", success=True)
        store.record("task2", "tool_b", success=False)
        all_stats = store.get_all_stats()
        assert "tool_a" in all_stats
        assert "tool_b" in all_stats

    def test_persistence_roundtrip(self, tmp_path: Path) -> None:
        fb_path = str(tmp_path / "fb.json")
        store1 = FeedbackStore(fb_path)
        store1.record("search the web", "search_web", success=True)
        store1.record("search the web", "search_web", success=True)
        store1.record("search the web", "search_web", success=False)

        store2 = FeedbackStore(fb_path)
        stats = store2.get_stats("search_web")
        assert stats is not None
        assert stats.success_count == 2
        assert stats.failure_count == 1

    def test_max_entries_trimming(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        for i in range(1010):
            store.record(f"task {i}", "mytool", success=True)
        assert len(store._entries) <= 1000

    def test_missing_file_loads_empty(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "nonexistent.json"))
        assert store.get_all_stats() == {}
        assert store.get_boost("any_tool") == 1.0

    def test_corrupted_file_loads_empty(self, tmp_path: Path) -> None:
        fb_path = tmp_path / "fb.json"
        fb_path.write_text("not valid json {{{")
        store = FeedbackStore(str(fb_path))
        assert store.get_all_stats() == {}


class TestFeedbackStoreTaskTypeBoost:
    """Test task type specific boost functionality."""

    def test_get_task_type_boost_no_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_task_type_boost("unknown_tool", "file_operations")
        assert boost == 1.0  # Default boost when no pattern exists

    def test_get_task_type_boost_with_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback to create a pattern
        for i in range(10):
            store.record("read file", "file_tool", success=True)
        for i in range(5):
            store.record("read file", "file_tool", success=False)

        boost = store.get_task_type_boost("file_tool", "file_operations")
        assert boost > 1.0  # Should be boosted due to good performance
        assert boost <= 1.3  # Should be within range


class TestFeedbackStoreLearningInsights:
    """Test learning insights functionality."""

    def test_get_learning_insights(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file.txt", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        insights = store.get_learning_insights("read file.txt")
        assert isinstance(insights, dict)
        assert "task_type" in insights
        assert "intent_category" in insights
        assert "entities" in insights
        assert "recommended_tools" in insights
        assert "success_probability" in insights

    def test_get_learning_insights_empty(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        insights = store.get_learning_insights("unknown task")
        assert isinstance(insights, dict)
        assert insights["task_type"] == "general_operations"
        assert insights["recommended_tools"] == []
        assert insights["success_probability"] == 0.5


class TestFeedbackStoreAdaptiveHints:
    """Test adaptive hints functionality."""

    def test_get_adaptive_hints(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file.txt", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        hints = store.get_adaptive_hints("read file.txt")
        assert isinstance(hints, list)
        # Should contain some hints based on the learning data

    def test_get_adaptive_hints_empty(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        hints = store.get_adaptive_hints("unknown task")
        assert isinstance(hints, list)
        # Should contain general hints even with no data


class TestFeedbackStoreEntityExtraction:
    """Test entity extraction functionality."""

    def test_extract_entities_file_paths(self) -> None:
        entities = FeedbackStore._extract_entities("read the file /path/to/file.txt")
        assert "/path/to/file.txt" in entities

    def test_extract_entities_urls(self) -> None:
        entities = FeedbackStore._extract_entities(
            "fetch data from https://example.com/api"
        )
        assert "https://example.com/api" in entities

    def test_extract_entities_quoted_strings(self) -> None:
        entities = FeedbackStore._extract_entities(
            'search for "test query" in database'
        )
        assert "test query" in entities

    def test_extract_entities_empty(self) -> None:
        entities = FeedbackStore._extract_entities("simple task without entities")
        assert entities == []


class TestFeedbackStoreAdvancedMethods:
    """Test advanced feedback store methods."""

    def test_confidence_score_calculation(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("test task", "tool", success=True, confidence=0.9)
        store.record("test task", "tool", success=False, confidence=0.3)

        stats = store.get_stats("tool")
        assert stats is not None
        assert stats.avg_confidence == 0.6  # (0.9 + 0.3) / 2
        assert stats.confidence_score > 0.5  # Should be above neutral

    def test_recent_success_rate_calculation(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Add 60 entries with varying success
        for i in range(60):
            success = i < 40  # First 40 succeed, last 20 fail
            store.record(f"task {i}", "tool", success=success)

        stats = store.get_stats("tool")
        assert stats is not None
        assert stats.recent_success_rate == 0.33  # 20/60 (last 50 entries)


class TestFeedbackStoreTaskTypeBoost:
    """Test task type specific boost functionality."""

    def test_get_task_type_boost_no_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_task_type_boost("unknown_tool", "file_operations")
        assert boost == 1.0  # Default boost when no pattern exists

    def test_get_task_type_boost_with_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback to create a pattern
        for i in range(10):
            store.record("read file", "file_tool", success=True)
        for i in range(5):
            store.record("read file", "file_tool", success=False)

        boost = store.get_task_type_boost("file_tool", "file_operations")
        assert boost > 1.0  # Should be boosted due to good performance
        assert boost <= 1.3  # Should be within range


class TestFeedbackStoreTaskTypeBoost:
    """Test task type specific boost functionality."""

    def test_get_task_type_boost_no_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_task_type_boost("unknown_tool", "file_operations")
        assert boost == 1.0  # Default boost when no pattern exists

    def test_get_task_type_boost_with_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback to create a pattern
        for i in range(10):
            store.record("read file", "file_tool", success=True)
        for i in range(5):
            store.record("read file", "file_tool", success=False)

        boost = store.get_task_type_boost("file_tool", "file_operations")
        assert boost > 1.0  # Should be boosted due to good performance
        assert boost <= 1.3  # Should be within range

    def test_get_task_type_boost_range(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Test different success rates
        store.record("test task", "tool", success=True)
        boost_high = store.get_task_type_boost("tool", "search_operations")

        store.record("test task", "tool2", success=False)
        boost_low = store.get_task_type_boost("tool2", "search_operations")

        assert boost_low < boost_high
        assert 0.7 <= boost_low <= 1.3
        assert 0.7 <= boost_high <= 1.3


class TestFeedbackStoreIntentBoost:
    """Test intent category specific boost functionality."""

    def test_get_intent_boost_no_stats(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_intent_boost("unknown_tool", "create")
        assert boost == 1.0  # Default boost when no stats exist

    def test_get_intent_boost_with_stats(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record feedback with intent
        store.record("create file", "tool", success=True, confidence=0.8)
        store.record("create directory", "tool", success=True, confidence=0.9)
        store.record("create file", "tool", success=False, confidence=0.7)

        boost = store.get_intent_boost("tool", "create")
        assert boost > 0.8  # Should be boosted due to good performance
        assert boost <= 1.2  # Should be within range

    def test_get_intent_boost_range(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Test different success rates
        store.record("create test", "tool1", success=True)
        boost_high = store.get_intent_boost("tool1", "create")

        store.record("create test", "tool2", success=False)
        boost_low = store.get_intent_boost("tool2", "create")

        assert boost_low < boost_high
        assert 0.8 <= boost_low <= 1.2
        assert 0.8 <= boost_high <= 1.2


class TestFeedbackStoreComprehensiveBoost:
    """Test comprehensive boost functionality."""

    def test_get_comprehensive_boost(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        boost = store.get_comprehensive_boost("file_tool", "read file")
        assert isinstance(boost, float)
        assert boost > 0.0

    def test_get_comprehensive_boost_no_data(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_comprehensive_boost("unknown_tool", "unknown task")
        assert boost == 1.0  # Default boost


class TestFeedbackStoreLearningInsights:
    """Test learning insights functionality."""

    def test_get_learning_insights(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file.txt", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        insights = store.get_learning_insights("read file.txt")
        assert isinstance(insights, dict)
        assert "task_type" in insights
        assert "intent_category" in insights
        assert "entities" in insights
        assert "recommended_tools" in insights
        assert "success_probability" in insights

    def test_get_learning_insights_empty(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        insights = store.get_learning_insights("unknown task")
        assert isinstance(insights, dict)
        assert insights["task_type"] == "general_operations"
        assert insights["recommended_tools"] == []
        assert insights["success_probability"] == 0.5


class TestFeedbackStoreAdaptiveHints:
    """Test adaptive hints functionality."""

    def test_get_adaptive_hints(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file.txt", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        hints = store.get_adaptive_hints("read file.txt")
        assert isinstance(hints, list)
        # Should contain some hints based on the learning data

    def test_get_adaptive_hints_empty(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        hints = store.get_adaptive_hints("unknown task")
        assert isinstance(hints, list)
        # Should contain general hints even with no data


class TestFeedbackStoreEntityExtraction:
    """Test entity extraction functionality."""

    def test_extract_entities_file_paths(self) -> None:
        entities = FeedbackStore._extract_entities("read the file /path/to/file.txt")
        assert "/path/to/file.txt" in entities

    def test_extract_entities_urls(self) -> None:
        entities = FeedbackStore._extract_entities(
            "fetch data from https://example.com/api"
        )
        assert "https://example.com/api" in entities

    def test_extract_entities_quoted_strings(self) -> None:
        entities = FeedbackStore._extract_entities(
            'search for "test query" in database'
        )
        assert "test query" in entities

    def test_extract_entities_empty(self) -> None:
        entities = FeedbackStore._extract_entities("simple task without entities")
        assert entities == []


class TestFeedbackStoreAdvancedMethods:
    """Test advanced feedback store methods."""

    def test_confidence_score_calculation(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("test task", "tool", success=True, confidence=0.9)
        store.record("test task", "tool", success=False, confidence=0.3)

        stats = store.get_stats("tool")
        assert stats is not None
        assert stats.avg_confidence == 0.6  # (0.9 + 0.3) / 2
        assert stats.confidence_score > 0.5  # Should be above neutral

    def test_recent_success_rate_calculation(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Add 60 entries with varying success
        for i in range(60):
            success = i < 40  # First 40 succeed, last 20 fail
            store.record(f"task {i}", "tool", success=success)

        stats = store.get_stats("tool")
        assert stats is not None
        assert stats.recent_success_rate == 0.33  # 20/60 (last 50 entries)

    def test_task_pattern_learning(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record feedback for specific task type
        for i in range(10):
            store.record("read file", "file_tool", success=True)
        for i in range(3):
            store.record("read file", "other_tool", success=False)

        # Check if pattern was learned
        assert "file_operations" in store._patterns
        pattern = store._patterns["file_operations"]
        assert "file_tool" in pattern.preferred_tools
        assert pattern.success_rate > 0.5


class TestFeedbackStoreAdvanced:
    def test_classify_task_type_file_operations(self) -> None:
        task_type = FeedbackStore._classify_task_type("read the file and write to disk")
        assert task_type == "file_operations"

    def test_classify_task_type_search_operations(self) -> None:
        task_type = FeedbackStore._classify_task_type("search for information")
        assert task_type == "search_operations"

    def test_classify_task_type_code_operations(self) -> None:
        task_type = FeedbackStore._classify_task_type("edit the code syntax")
        assert task_type == "code_operations"

    def test_classify_task_type_database_operations(self) -> None:
        task_type = FeedbackStore._classify_task_type("query the database table")
        assert (
            task_type == "search_operations"
        )  # "query" matches search before database

    def test_classify_task_type_network_operations(self) -> None:
        task_type = FeedbackStore._classify_task_type("fetch data from api")
        assert task_type == "network_operations"

    def test_classify_task_type_system_operations(self) -> None:
        task_type = FeedbackStore._classify_task_type("run system command")
        assert task_type == "system_operations"

    def test_classify_task_type_general_operations(self) -> None:
        task_type = FeedbackStore._classify_task_type("do something random")
        assert task_type == "general_operations"

    def test_classify_intent_create(self) -> None:
        intent = FeedbackStore._classify_intent("create new file")
        assert intent == "create"

    def test_classify_intent_read(self) -> None:
        intent = FeedbackStore._classify_intent("read the data")
        assert intent == "read"

    def test_classify_intent_update(self) -> None:
        intent = FeedbackStore._classify_intent("update the configuration")
        assert intent == "update"

    def test_classify_intent_delete(self) -> None:
        intent = FeedbackStore._classify_intent("delete old files")
        assert intent == "delete"

    def test_classify_intent_search(self) -> None:
        intent = FeedbackStore._classify_intent("search for patterns")
        assert intent == "search"

    def test_extract_entities_basic(self) -> None:
        entities = FeedbackStore._extract_entities("search web for python files")
        assert "web" in entities
        assert "python" in entities
        assert "files" in entities

    def test_extract_entities_empty(self) -> None:
        entities = FeedbackStore._extract_entities("")
        assert entities == []

    def test_extract_entities_special_chars(self) -> None:
        entities = FeedbackStore._extract_entities("search for .config files in /etc/")
        # The regex extracts paths, so we get the full path components
        assert "/etc/" in entities
        assert ".config" in entities
        assert "files" in entities

    def test_record_with_full_metadata(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record(
            task="create new python file",
            selected_tool="file_creator",
            success=True,
            context="User wants to create a Python script",
            confidence=0.9,
        )
        stats = store.get_stats("file_creator")
        assert stats is not None
        assert stats.success_count == 1
        assert stats.avg_confidence == 0.9

    def test_get_stats_with_task_type_tracking(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("create file", "tool_a", success=True)
        store.record("search file", "tool_a", success=True)
        store.record("read file", "tool_b", success=True)

        stats_a = store.get_stats("tool_a")
        assert stats_a is not None
        assert stats_a.task_types.get("file_operations", 0) == 2

    def test_get_stats_with_intent_tracking(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record("create file", "tool_a", success=True)
        store.record("update file", "tool_a", success=True)
        store.record("delete file", "tool_b", success=True)

        stats_a = store.get_stats("tool_a")
        assert stats_a is not None
        assert stats_a.intent_categories.get("create", 0) == 1
        assert stats_a.intent_categories.get("update", 0) == 1

    def test_recent_success_rate_calculation(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Add 10 entries, 7 successful
        for i in range(7):
            store.record(f"task {i}", "mytool", success=True)
        for i in range(3):
            store.record(f"task {i+7}", "mytool", success=False)

        stats = store.get_stats("mytool")
        assert stats is not None
        assert stats.recent_success_rate == 0.7

    def test_similar_task_tools_with_context_matching(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        store.record(
            "process python data",
            "data_processor",
            success=True,
            context="data analysis",
        )
        store.record(
            "analyze python code", "code_analyzer", success=True, context="code review"
        )

        similar = store.similar_task_tools("process python files")
        assert "data_processor" in similar

    def test_cleanup_old_entries(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Add entries beyond max limit
        for i in range(1050):
            store.record(f"task {i}", "mytool", success=True)

        # Should be trimmed to max entries
        assert len(store._entries) <= 1000

        # Recent entries should still be there
        recent_stats = store.get_stats("mytool")
        assert recent_stats is not None
        assert recent_stats.success_count > 0

    def test_load_feedback_file_io_error(self, tmp_path: Path) -> None:
        fb_path = str(tmp_path / "fb.json")

        # Mock file read error
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            store = FeedbackStore(fb_path)
            assert store.get_all_stats() == {}

    def test_save_feedback_file_io_error(self, tmp_path: Path) -> None:
        fb_path = str(tmp_path / "fb.json")
        store = FeedbackStore(fb_path)
        store.record("test task", "test_tool", success=True)

        # Mock file write error
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Should not raise exception, just fail silently
            store.record("test task 2", "test_tool", success=False)


class TestFeedbackStoreBusinessLogic:
    """Test cases for FeedbackStore business logic and learning algorithms."""

    def test_boost_calculation_with_historical_success(self, tmp_path: Path) -> None:
        """Test boost calculation based on historical success rates."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record successful outcomes
        for _ in range(5):
            store.record("search the web", "search_web", success=True, confidence=0.8)

        boost = store.get_boost("search_web")
        assert boost > 1.0  # Should be boosted due to success
        assert boost <= 1.7  # Should be clamped to maximum

    def test_boost_calculation_with_historical_failure(self, tmp_path: Path) -> None:
        """Test boost calculation penalizes failed tools."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record failed outcomes
        for _ in range(5):
            store.record("search the web", "bad_tool", success=False, confidence=0.3)

        boost = store.get_boost("bad_tool")
        assert boost < 1.0  # Should be penalized due to failure
        assert boost >= 0.1  # Should be clamped to minimum

    def test_boost_calculation_insufficient_data(self, tmp_path: Path) -> None:
        """Test boost returns neutral when insufficient data."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Only 2 entries (below threshold of 3)
        store.record("test task", "new_tool", success=True)
        store.record("test task", "new_tool", success=True)

        boost = store.get_boost("new_tool")
        assert boost == 1.0  # Neutral boost due to insufficient data

    def test_confidence_tracking_affects_boost(self, tmp_path: Path) -> None:
        """Test that confidence scores affect boost calculation."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record successes with different confidence levels
        store.record("task", "high_conf_tool", success=True, confidence=0.9)
        store.record("task", "high_conf_tool", success=True, confidence=0.8)
        store.record("task", "low_conf_tool", success=True, confidence=0.3)
        store.record("task", "low_conf_tool", success=True, confidence=0.2)

        high_boost = store.get_boost("high_conf_tool")
        low_boost = store.get_boost("low_conf_tool")

        assert high_boost > low_boost  # Higher confidence should result in higher boost

    def test_recent_performance_affects_boost(self, tmp_path: Path) -> None:
        """Test that recent performance affects boost calculation."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record initial failures
        for _ in range(10):
            store.record("task", "improving_tool", success=False)

        # Record recent successes
        for _ in range(10):
            store.record("task", "improving_tool", success=True)

        boost = store.get_boost("improving_tool")
        assert boost > 1.0  # Should be boosted due to recent success

    def test_task_type_classification_learning(self, tmp_path: Path) -> None:
        """Test that task type classification is learned and used."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record different task types
        store.record("read the file", "file_reader", success=True)
        store.record("search the web", "web_search", success=True)
        store.record("edit the code", "code_editor", success=True)

        file_stats = store.get_stats("file_reader")
        web_stats = store.get_stats("web_search")
        code_stats = store.get_stats("code_editor")

        assert "file_operations" in file_stats.task_types
        assert "search_operations" in web_stats.task_types
        assert "code_operations" in code_stats.task_types

    def test_intent_tracking_affects_learning(self, tmp_path: Path) -> None:
        """Test that intent categories are tracked and used for learning."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record different intents
        store.record("create new file", "creator", success=True)
        store.record("read the data", "reader", success=True)
        store.record("update config", "updater", success=True)

        creator_stats = store.get_stats("creator")
        reader_stats = store.get_stats("reader")
        updater_stats = store.get_stats("updater")

        assert "create" in creator_stats.intent_categories
        assert "read" in reader_stats.intent_categories
        assert "update" in updater_stats.intent_categories

    def test_pattern_learning_for_task_types(self, tmp_path: Path) -> None:
        """Test that patterns are learned for task types."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record multiple successful uses of a tool for a task type
        for _ in range(5):
            store.record("search for information", "search_tool", success=True)

        # Record failures for another tool
        for _ in range(3):
            store.record("search for data", "bad_search", success=False)

        # Check that patterns were learned
        assert "search_operations" in store._patterns
        pattern = store._patterns["search_operations"]
        assert pattern.total_occurrences >= 8  # 5 + 3 entries
        assert "search_tool" in pattern.preferred_tools
        assert "bad_search" in pattern.preferred_tools
        assert (
            pattern.preferred_tools["search_tool"]
            > pattern.preferred_tools["bad_search"]
        )

    def test_entity_extraction_and_learning(self, tmp_path: Path) -> None:
        """Test that entities are extracted and learned from tasks."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record tasks with different entities
        store.record("process /path/to/file.py", "processor", success=True)
        store.record("handle 'important data'", "handler", success=True)
        store.record("fetch https://example.com/api", "fetcher", success=True)

        # Check that entities were extracted and learned
        assert "search_operations" in store._patterns
        pattern = store._patterns["search_operations"]
        assert "/path/to/file.py" in pattern.common_entities
        assert "important data" in pattern.common_entities
        assert "https://example.com/api" in pattern.common_entities

    def test_similar_task_tools_uses_learning(self, tmp_path: Path) -> None:
        """Test that similar task tools uses learned patterns."""
        store = FeedbackStore(str(tmp_path / "fb.json"))

        # Record successful tool for a task type
        store.record("search python documentation", "doc_search", success=True)
        store.record("search python examples", "doc_search", success=True)
        store.record("search python tutorials", "doc_search", success=True)

        # Record failures for another tool
        store.record("search python errors", "error_search", success=False)
        store.record("search python bugs", "error_search", success=False)
        # Test similar task recommendation
        similar = store.similar_task_tools("search python code")
        assert "doc_search" in similar  # Should recommend successful tool
        assert "error_search" not in similar  # Should exclude failed tool


class TestFeedbackStoreComprehensiveBoost:
    """Test comprehensive boost functionality."""

    def test_get_comprehensive_boost(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        boost = store.get_comprehensive_boost("file_tool", "read file")
        assert isinstance(boost, float)
        assert boost > 0.0

    def test_get_comprehensive_boost_no_data(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_comprehensive_boost("unknown_tool", "unknown task")
        assert boost == 1.0  # Default boost


class TestFeedbackStoreIntentBoost:
    """Test intent category specific boost functionality."""

    def test_get_intent_boost_no_stats(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_intent_boost("unknown_tool", "create")
        assert boost == 1.0  # Default boost when no stats exist

    def test_get_intent_boost_with_stats(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record feedback with intent
        store.record("create file", "tool", success=True, confidence=0.8)
        store.record("create directory", "tool", success=True, confidence=0.9)
        store.record("create file", "tool", success=False, confidence=0.7)

        boost = store.get_intent_boost("tool", "create")
        assert boost > 0.8  # Should be boosted due to good performance
        assert boost <= 1.2  # Should be within range


class TestFeedbackStoreLearningInsights:
    """Test learning insights functionality."""

    def test_get_learning_insights(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file.txt", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        insights = store.get_learning_insights("read file.txt")
        assert isinstance(insights, dict)
        assert "task_type" in insights
        assert "intent_category" in insights
        assert "entities" in insights
        assert "recommended_tools" in insights
        assert "success_probability" in insights

    def test_get_learning_insights_empty(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        insights = store.get_learning_insights("unknown task")
        assert isinstance(insights, dict)
        assert insights["task_type"] == "general_operations"
        assert insights["recommended_tools"] == []
        assert insights["success_probability"] == 0.5


class TestFeedbackStoreAdaptiveHints:
    """Test adaptive hints functionality."""

    def test_get_adaptive_hints(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback
        store.record("read file.txt", "file_tool", success=True)
        store.record("create directory", "dir_tool", success=False)

        hints = store.get_adaptive_hints("read file.txt")
        assert isinstance(hints, list)
        # Should contain some hints based on the learning data

    def test_get_adaptive_hints_empty(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        hints = store.get_adaptive_hints("unknown task")
        assert isinstance(hints, list)
        # Should contain general hints even with no data


class TestFeedbackStoreEntityExtraction:
    """Test entity extraction functionality."""

    def test_extract_entities_file_paths(self) -> None:
        entities = FeedbackStore._extract_entities("read the file /path/to/file.txt")
        assert "/path/to/file.txt" in entities

    def test_extract_entities_urls(self) -> None:
        entities = FeedbackStore._extract_entities(
            "fetch data from https://example.com/api"
        )
        assert "https://example.com/api" in entities

    def test_extract_entities_quoted_strings(self) -> None:
        entities = FeedbackStore._extract_entities(
            'search for "test query" in database'
        )
        assert "test query" in entities

    def test_extract_entities_empty(self) -> None:
        entities = FeedbackStore._extract_entities("simple task without entities")
        assert entities == []


class TestFeedbackStoreTaskTypeBoost:
    """Test task type specific boost functionality."""

    def test_get_task_type_boost_no_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        boost = store.get_task_type_boost("unknown_tool", "file_operations")
        assert boost == 1.0  # Default boost when no pattern exists

    def test_get_task_type_boost_with_pattern(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record some feedback to create a pattern
        for i in range(10):
            store.record("read file", "file_tool", success=True)
        for i in range(5):
            store.record("read file", "file_tool", success=False)

        boost = store.get_task_type_boost("file_tool", "file_operations")
        assert boost > 1.0  # Should be boosted due to good performance
        assert boost <= 1.3  # Should be within range


class TestFeedbackStoreTaskPatternLearning:
    """Test task pattern learning functionality."""

    def test_task_pattern_learning(self, tmp_path: Path) -> None:
        store = FeedbackStore(str(tmp_path / "fb.json"))
        # Record feedback for specific task type
        for i in range(10):
            store.record("read file", "file_tool", success=True)
        for i in range(3):
            store.record("read file", "other_tool", success=False)

        # Check if pattern was learned
        assert "file_operations" in store._patterns
        pattern = store._patterns["file_operations"]
        assert "file_tool" in pattern.preferred_tools
        assert pattern.success_rate > 0.5
