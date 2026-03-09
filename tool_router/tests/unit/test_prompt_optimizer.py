"""Tests for prompt optimizer."""

import pytest

from tool_router.ai.prompt_optimizer import PromptOptimizer, OptimizationResult


@pytest.fixture
def optimizer():
    return PromptOptimizer(feedback_store=None, enable_learning=False)


class TestVagueTermExpansion:
    def test_expands_nice(self, optimizer):
        result = optimizer.optimize("Make a nice button")
        assert "polished and visually refined" in result.optimized_prompt
        assert any("nice" in a for a in result.additions)

    def test_expands_cool(self, optimizer):
        result = optimizer.optimize("A cool dashboard")
        assert "modern with subtle animations" in result.optimized_prompt

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
                        {"tool": "generate_component", "score": 0.9},
                        {"tool": "style_matcher", "score": 0.8},
                    ]
                }

        optimizer = PromptOptimizer(feedback_store=MockFeedback(), enable_learning=True)
        result = optimizer.optimize("Generate a dashboard")
        assert any("Recommended" in a for a in result.additions)

    def test_handles_missing_feedback(self):
        optimizer = PromptOptimizer(feedback_store=None, enable_learning=True)
        result = optimizer.optimize("test")
        assert isinstance(result, OptimizationResult)
