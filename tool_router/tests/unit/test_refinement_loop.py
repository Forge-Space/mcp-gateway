"""Tests for generate-review-refine loop."""

import pytest

from tool_router.ai.refinement_loop import (
    RefinementConfig,
    build_refinement_prompt,
    refine_code,
    should_refine,
)
from tool_router.api.quality_gates import QualityReport, GateResult


def _make_report(score: float, passed: bool) -> QualityReport:
    return QualityReport(
        passed=passed,
        score=score,
        results=[
            GateResult(gate="security", passed=passed, issues=[], severity="info"),
        ],
    )


class TestBuildRefinementPrompt:
    def test_includes_task_and_code(self):
        report = _make_report(0.5, False)
        report.results = [
            GateResult(
                gate="security",
                passed=False,
                issues=["Potential XSS: eval"],
                severity="error",
            )
        ]
        prompt = build_refinement_prompt("hello", report, "make a button")
        assert "make a button" in prompt
        assert "hello" in prompt
        assert "eval" in prompt

    def test_includes_score(self):
        report = _make_report(0.67, False)
        prompt = build_refinement_prompt("code", report, "task")
        assert "0.67" in prompt

    def test_no_issues_message(self):
        report = _make_report(1.0, True)
        prompt = build_refinement_prompt("code", report, "task")
        assert "No specific issues" in prompt


class TestShouldRefine:
    def test_no_refine_when_passed(self):
        report = _make_report(1.0, True)
        config = RefinementConfig()
        assert not should_refine(report, config, 0, 0.0)

    def test_no_refine_at_max_iterations(self):
        report = _make_report(0.5, False)
        config = RefinementConfig(max_iterations=3)
        assert not should_refine(report, config, 3, 0.0)

    def test_no_refine_on_plateau(self):
        report = _make_report(0.51, False)
        config = RefinementConfig(min_score_improvement=0.05)
        assert not should_refine(report, config, 1, 0.50)

    def test_refine_when_failing(self):
        report = _make_report(0.5, False)
        config = RefinementConfig()
        assert should_refine(report, config, 0, 0.0)

    def test_refine_when_improving(self):
        report = _make_report(0.7, False)
        config = RefinementConfig(min_score_improvement=0.05)
        assert should_refine(report, config, 1, 0.5)

    def test_no_refine_at_target_score(self):
        report = _make_report(1.0, False)
        config = RefinementConfig(target_score=1.0)
        assert not should_refine(report, config, 0, 0.0)


class TestRefineCode:
    def test_returns_original_when_passing(self):
        code = "export const Button = () => { return <button>Click</button> }"
        result = refine_code(code, "button", lambda p: code)
        assert result.iterations == 0
        assert result.final_code == code

    def test_iterates_on_failing_code(self):
        good_code = "export const Button = () => { return <button>Click</button> }"
        call_count = 0

        def generate(prompt):
            nonlocal call_count
            call_count += 1
            return good_code

        bad_code = "document.write('xss')"
        result = refine_code(bad_code, "button", generate, RefinementConfig(max_iterations=2))
        assert result.iterations >= 1
        assert len(result.history) >= 2

    def test_stops_on_empty_refinement(self):
        result = refine_code("x", "task", lambda p: "", RefinementConfig(max_iterations=3))
        assert result.iterations <= 1

    def test_stops_on_exception(self):
        def failing_gen(prompt):
            raise RuntimeError("AI down")

        result = refine_code("x", "task", failing_gen, RefinementConfig(max_iterations=3))
        assert result.iterations <= 1

    def test_score_delta_calculated(self):
        good_code = "export const Button = () => { return <button>Click</button> }"
        result = refine_code("x", "task", lambda p: good_code)
        assert isinstance(result.score_delta, float)
        assert result.final_score == result.initial_score + result.score_delta
