"""Tests for the FeedbackStore context learning mechanism."""

from __future__ import annotations

from pathlib import Path

import pytest

from tool_router.ai.feedback import FeedbackStore, ToolStats


class TestToolStats:
    def test_total(self) -> None:
        s = ToolStats("mytool", success_count=3, failure_count=1)
        assert s.total == 4

    def test_success_rate_no_data(self) -> None:
        s = ToolStats("mytool")
        assert s.success_rate == 0.5  # neutral prior

    def test_success_rate_all_success(self) -> None:
        s = ToolStats("mytool", success_count=5, failure_count=0)
        assert s.success_rate == 1.0

    def test_success_rate_all_failure(self) -> None:
        s = ToolStats("mytool", success_count=0, failure_count=4)
        assert s.success_rate == 0.0

    def test_success_rate_mixed(self) -> None:
        s = ToolStats("mytool", success_count=3, failure_count=1)
        assert s.success_rate == pytest.approx(0.75)


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
