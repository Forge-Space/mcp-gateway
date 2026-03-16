"""Tests for prompt optimizer."""

import pytest

from tool_router.ai.prompt_optimizer import OptimizationResult, PromptOptimizer


@pytest.fixture
def optimizer():
    return PromptOptimizer(feedback_store=None, enable_learning=False)


class TestVagueTermExpansion:
    @pytest.mark.parametrize(
        ("prompt", "expected_substrings"),
        [
            ("Make a nice button", ["polished and visually refined"]),
            ("A cool dashboard", ["modern with subtle animations"]),
            ("A nice and nice card", ["polished and visually refined"]),
            ("", []),
        ],
    )
    def test_parametrized_expansions(self, optimizer, prompt, expected_substrings):
        result = optimizer.optimize(prompt)
        for expected in expected_substrings:
            assert expected in result.optimized_prompt

    def test_no_expansion_for_specific_prompts(self, optimizer):
        prompt = "A button with ARIA labels and responsive layout"
        result = optimizer.optimize(prompt)
        assert not any("Expanded" in a for a in result.additions)

    def test_multiple_expansions(self, optimizer):
        result = optimizer.optimize("A nice and simple form")
        assert "polished" in result.optimized_prompt
        assert "minimal" in result.optimized_prompt


class TestComponentHints:
    def test_adds_form_hint(self, optimizer):
        result = optimizer.optimize("Create a form component")
        assert any("validation" in a.lower() for a in result.additions)

    def test_adds_modal_hint(self, optimizer):
        result = optimizer.optimize("Build a modal dialog")
        assert any("focus" in a.lower() for a in result.additions)

    def test_adds_table_hint(self, optimizer):
        result = optimizer.optimize("Generate a data table")
        assert any("sorting" in a.lower() or "pagination" in a.lower() for a in result.additions)

    def test_no_hint_for_unknown_component(self, optimizer):
        result = optimizer.optimize("Generate a widget")
        assert not any("Component hint" in a for a in result.additions)


class TestAccessibility:
    def test_adds_a11y_when_missing(self, optimizer):
        result = optimizer.optimize("Make a paragraph component")
        assert any("ARIA" in a for a in result.additions)

    def test_skips_when_aria_present(self, optimizer):
        result = optimizer.optimize("Make a button with aria labels")
        assert not any("A11y" in a for a in result.additions)

    def test_skips_when_accessible_present(self, optimizer):
        result = optimizer.optimize("Make an accessible form")
        assert not any("A11y" in a for a in result.additions)


class TestResponsive:
    def test_adds_responsive_when_missing(self, optimizer):
        result = optimizer.optimize("Make a card component")
        assert any("Responsive" in a for a in result.additions)

    def test_skips_when_responsive_present(self, optimizer):
        result = optimizer.optimize("A responsive card with breakpoints")
        assert not any("Responsive" in a for a in result.additions)

    def test_skips_when_mobile_mentioned(self, optimizer):
        result = optimizer.optimize("A card optimized for mobile")
        assert not any("Responsive" in a for a in result.additions)


class TestStrategy:
    def test_none_strategy_for_complete_prompt(self, optimizer):
        result = optimizer.optimize("An accessible responsive form with ARIA labels and mobile breakpoints")
        hint_additions = [a for a in result.additions if "Component hint" in a]
        if not hint_additions:
            assert result.strategy == "none" or "+" not in result.strategy

    def test_combined_strategy(self, optimizer):
        result = optimizer.optimize("A nice paragraph component")
        assert "vague_expansion" in result.strategy
        assert "a11y" in result.strategy

    def test_result_type(self, optimizer):
        result = optimizer.optimize("test")
        assert isinstance(result, OptimizationResult)
        assert result.original_prompt == "test"


class TestLearningIntegration:
    def test_with_mock_feedback_store(self):
        class MockFeedback:
            def get_learning_insights(self, prompt):
                return {
                    "recommended_tools": [
                        {"tool": "generate_component", "success_rate": 0.9},
                        {"tool": "style_matcher", "success_rate": 0.8},
                    ]
                }

        optimizer = PromptOptimizer(feedback_store=MockFeedback(), enable_learning=True)
        result = optimizer.optimize("Generate a dashboard")
        assert any("Recommended" in a for a in result.additions)

    def test_handles_missing_feedback(self):
        optimizer = PromptOptimizer(feedback_store=None, enable_learning=True)
        result = optimizer.optimize("test")
        assert isinstance(result, OptimizationResult)


# ---------------------------------------------------------------------------
# Coverage gap: _apply_learning_insights Exception path (lines 150-151)
# ---------------------------------------------------------------------------


class TestPromptOptimizerLearningException:
    """Cover the except Exception path in _apply_learning_insights."""

    def test_exception_in_get_learning_insights_is_swallowed(self) -> None:
        from tool_router.ai.prompt_optimizer import PromptOptimizer

        class FailingFeedback:
            def get_learning_insights(self, prompt: str) -> dict:
                raise RuntimeError("DB gone")

        optimizer = PromptOptimizer(feedback_store=FailingFeedback(), enable_learning=True)
        result = optimizer.optimize("Build a form")
        # Should not raise; learning just silently skipped
        assert result is not None
        assert result.original_prompt == "Build a form"
