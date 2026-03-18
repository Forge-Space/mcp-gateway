"""Tests for A/B testing manager."""

import tempfile
from pathlib import Path

import pytest

from tool_router.ai.ab_testing import (
    ABTestManager,
    Experiment,
    ExperimentOutcome,
    Variant,
)


@pytest.fixture
def experiment():
    return Experiment(
        id="model_test",
        variants=[
            Variant(name="balanced", weight=1.0, config={"model": "llama3.2:3b"}),
            Variant(name="efficient", weight=1.0, config={"model": "gemma2:2b"}),
        ],
    )


@pytest.fixture
def manager(experiment):
    return ABTestManager(experiments=[experiment])


class TestVariantAssignment:
    def test_deterministic_assignment(self, manager):
        v1 = manager.assign_variant("user-1", "model_test")
        v2 = manager.assign_variant("user-1", "model_test")
        assert v1 is not None
        assert v1.name == v2.name

    def test_different_users_get_different_variants(self, manager):
        assignments = set()
        for i in range(100):
            v = manager.assign_variant(f"user-{i}", "model_test")
            assignments.add(v.name)
        assert len(assignments) == 2

    def test_returns_none_for_missing_experiment(self, manager):
        assert manager.assign_variant("user-1", "nonexistent") is None

    def test_returns_none_for_inactive(self, manager):
        manager._experiments["model_test"].active = False
        assert manager.assign_variant("user-1", "model_test") is None

    def test_weighted_assignment(self):
        exp = Experiment(
            id="weighted",
            variants=[
                Variant(name="heavy", weight=9.0),
                Variant(name="light", weight=1.0),
            ],
        )
        mgr = ABTestManager(experiments=[exp])
        counts = {"heavy": 0, "light": 0}
        for i in range(1000):
            v = mgr.assign_variant(f"u{i}", "weighted")
            counts[v.name] += 1
        assert counts["heavy"] > counts["light"]


class TestOutcomeTracking:
    def test_record_and_stats(self, manager):
        for i in range(10):
            manager.record_outcome(
                ExperimentOutcome(
                    experiment_id="model_test",
                    variant_name="balanced",
                    user_id=f"user-{i}",
                    quality_score=7.5 + (i * 0.1),
                    latency_ms=1000 + i * 100,
                    success=True,
                )
            )
        stats = manager.get_variant_stats("model_test")
        assert "balanced" in stats
        assert stats["balanced"]["count"] == 10
        assert stats["balanced"]["avg_score"] > 7.0
        assert stats["balanced"]["success_rate"] == pytest.approx(1.0)

    def test_empty_stats(self, manager):
        assert manager.get_variant_stats("model_test") == {}

    def test_winner_detection(self, manager):
        for i in range(25):
            manager.record_outcome(
                ExperimentOutcome(
                    experiment_id="model_test",
                    variant_name="balanced",
                    user_id=f"a{i}",
                    quality_score=8.0,
                    latency_ms=1000,
                    success=True,
                )
            )
            manager.record_outcome(
                ExperimentOutcome(
                    experiment_id="model_test",
                    variant_name="efficient",
                    user_id=f"b{i}",
                    quality_score=6.0,
                    latency_ms=500,
                    success=True,
                )
            )
        winner = manager.get_winner("model_test", min_samples=20)
        assert winner == "balanced"

    def test_no_winner_insufficient_samples(self, manager):
        manager.record_outcome(
            ExperimentOutcome(
                experiment_id="model_test",
                variant_name="balanced",
                user_id="u1",
                quality_score=9.0,
                latency_ms=100,
                success=True,
            )
        )
        assert manager.get_winner("model_test", min_samples=20) is None


class TestPersistence:
    def test_save_and_load(self, experiment):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        mgr1 = ABTestManager(experiments=[experiment], storage_path=path)
        for i in range(55):
            mgr1.record_outcome(
                ExperimentOutcome(
                    experiment_id="model_test",
                    variant_name="balanced",
                    user_id=f"u{i}",
                    quality_score=7.0,
                    latency_ms=1000,
                    success=True,
                )
            )

        mgr2 = ABTestManager(experiments=[experiment], storage_path=path)
        assert len(mgr2._outcomes) > 0


class TestABTestingCoverageGaps:
    """Cover missing lines 79, 88, 145-146, 150 in ab_testing.py."""

    def test_assign_variant_zero_weight_returns_first(self):
        """Line 79: total_weight <= 0 returns variants[0]."""
        exp = Experiment(
            id="w_test",
            variants=[
                Variant(name="a", weight=0.0),
                Variant(name="b", weight=0.0),
            ],
        )
        mgr = ABTestManager(experiments=[exp])
        result = mgr.assign_variant("user1", "w_test")
        assert result is not None
        assert result.name == "a"

    def test_assign_variant_cumulative_fallback(self):
        """Line 88: cumulative loop exhausted, return variants[-1]."""
        exp = Experiment(
            id="c_test",
            variants=[
                Variant(name="a", weight=0.001),
                Variant(name="b", weight=0.001),
            ],
        )
        mgr = ABTestManager(experiments=[exp])
        # Try many users to find one where target >= cumulative
        found = False
        for i in range(1000):
            r = mgr.assign_variant(f"u{i}", "c_test")
            if r and r.name == "b":
                found = True
                break
        assert found

    def test_persist_outcomes_oserror(self):
        """Lines 145-146: OSError during _persist_outcomes."""
        from pathlib import Path

        exp = Experiment(
            id="p_test",
            variants=[Variant(name="a", weight=1.0)],
        )
        mgr = ABTestManager(
            experiments=[exp],
            storage_path=Path("/nonexistent/dir/file.json"),
        )
        mgr._storage = Path("/nonexistent/dir/file.json")
        for i in range(50):
            mgr.record_outcome(
                ExperimentOutcome(
                    experiment_id="p_test",
                    variant_name="a",
                    user_id=f"u{i}",
                    quality_score=7.0,
                    latency_ms=100,
                    success=True,
                )
            )
        # No exception raised; warning logged

    def test_load_outcomes_storage_not_exists(self):
        """Line 150: storage set but file doesn't exist."""
        exp = Experiment(
            id="l_test",
            variants=[Variant(name="a", weight=1.0)],
        )
        mgr = ABTestManager(
            experiments=[exp],
            storage_path=Path("/tmp/nonexistent_ab_test_xyz.json"),
        )
        # _load_outcomes called in __init__ with non-existent file -> returns early
        assert mgr._outcomes == []

    def test_assign_variant_fallback_returns_last_variant_deterministically(self):
        """Line 88: fallback return when NaN comparisons bypass loop return."""
        exp = Experiment(
            id="nan_test",
            variants=[Variant(name="first", weight=float("nan")), Variant(name="last", weight=1.0)],
        )
        mgr = ABTestManager(experiments=[exp])

        result = mgr.assign_variant("user-1", "nan_test")
        assert result is not None
        assert result.name == "last"

    def test_load_outcomes_direct_call_missing_storage_returns_early(self):
        """Line 150: direct _load_outcomes early-return when file does not exist."""
        exp = Experiment(
            id="direct_load_test",
            variants=[Variant(name="a", weight=1.0)],
        )
        missing_path = Path("/tmp/nonexistent_ab_test_direct_call_xyz.json")
        mgr = ABTestManager(experiments=[exp], storage_path=str(missing_path))

        mgr._outcomes.append(
            ExperimentOutcome(
                experiment_id="direct_load_test",
                variant_name="a",
                user_id="u1",
                quality_score=1.0,
                latency_ms=1,
                success=True,
            )
        )

        mgr._load_outcomes()
        assert len(mgr._outcomes) == 1
