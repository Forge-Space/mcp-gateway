"""Coverage tests for enhanced_selector.py — targets uncovered branches."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tool_router.ai.enhanced_selector import (
    AIModel,
    CostTracker,
    EnhancedAISelector,
    OllamaSelector,
)


def _make_ollama(endpoint: str = "http://localhost:11434", **kw) -> OllamaSelector:
    return OllamaSelector(endpoint=endpoint, model="llama3.2:3b", **kw)


def _make_httpx_response(body: dict) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = body
    mock.raise_for_status = MagicMock()
    return mock


class TestOllamaSelectorParsing:
    """Cover _parse_response and _parse_multi_response error branches."""

    def test_select_tool_returns_none_when_ollama_returns_empty(self) -> None:
        sel = _make_ollama()
        resp = _make_httpx_response({"response": ""})
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            assert sel.select_tool("t", [{"name": "a", "description": "a"}]) is None

    def test_parse_response_missing_fields(self) -> None:
        sel = _make_ollama()
        resp = _make_httpx_response({"response": '{"confidence": 0.9}'})
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            assert sel.select_tool("t", [{"name": "a", "description": "a"}]) is None

    def test_parse_response_invalid_confidence(self) -> None:
        sel = _make_ollama()
        resp = _make_httpx_response(
            {"response": '{"tool_name": "a", "confidence": 5, "reasoning": "x"}'}
        )
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            assert sel.select_tool("t", [{"name": "a", "description": "a"}]) is None

    def test_parse_response_json_decode_error(self) -> None:
        sel = _make_ollama()
        resp = _make_httpx_response({"response": "not {json at all"})
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            assert sel.select_tool("t", [{"name": "a", "description": "a"}]) is None

    def test_parse_response_generic_exception(self) -> None:
        sel = _make_ollama()
        resp = _make_httpx_response({"response": '{"tool_name": 1, "confidence": "bad", "reasoning": "x"}'})
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            result = sel.select_tool("t", [{"name": "a", "description": "a"}])
            assert result is None

    def test_select_tool_low_confidence_discarded(self) -> None:
        sel = _make_ollama(min_confidence=0.9)
        resp = _make_httpx_response(
            {"response": '{"tool_name": "a", "confidence": 0.5, "reasoning": "x"}'}
        )
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            assert sel.select_tool("t", [{"name": "a", "description": "a"}]) is None


class TestOllamaMultiToolParsing:
    """Cover _parse_multi_response branches."""

    def _multi_call(self, sel, response_text):
        resp = _make_httpx_response({"response": response_text})
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            return sel.select_tools_multi(
                "task", [{"name": "search", "description": "s"}, {"name": "calc", "description": "c"}]
            )

    def test_no_json_in_response(self) -> None:
        assert self._multi_call(_make_ollama(), "no json here") is None

    def test_missing_required_fields(self) -> None:
        assert self._multi_call(_make_ollama(), '{"tools": ["a"]}') is None

    def test_empty_tools_list(self) -> None:
        assert self._multi_call(
            _make_ollama(),
            '{"tools": [], "confidence": 0.8, "reasoning": "x"}',
        ) is None

    def test_invalid_confidence(self) -> None:
        assert self._multi_call(
            _make_ollama(),
            '{"tools": ["search"], "confidence": 2.0, "reasoning": "x"}',
        ) is None

    def test_no_valid_tool_names(self) -> None:
        assert self._multi_call(
            _make_ollama(),
            '{"tools": ["nonexistent"], "confidence": 0.8, "reasoning": "x"}',
        ) is None

    def test_json_decode_error(self) -> None:
        assert self._multi_call(_make_ollama(), "{invalid json}") is None

    def test_valid_multi_response_filters_tools(self) -> None:
        result = self._multi_call(
            _make_ollama(),
            '{"tools": ["search", "nonexistent", "calc"], "confidence": 0.8, "reasoning": "x"}',
        )
        assert result is not None
        assert result["tools"] == ["search", "calc"]

    def test_multi_low_confidence_discarded(self) -> None:
        sel = _make_ollama(min_confidence=0.9)
        result = self._multi_call(
            sel, '{"tools": ["search"], "confidence": 0.5, "reasoning": "x"}'
        )
        assert result is None


class TestEnhancedAISelectorCostOptimization:
    """Cover cost optimization paths in select_tool_with_cost_optimization."""

    def _make_selector(self) -> EnhancedAISelector:
        ollama = _make_ollama()
        return EnhancedAISelector(providers=[ollama])

    def test_empty_tools_returns_none(self) -> None:
        sel = self._make_selector()
        assert sel.select_tool_with_cost_optimization("task", []) is None

    def test_no_providers_returns_none(self) -> None:
        sel = EnhancedAISelector(providers=[])
        assert sel.select_tool_with_cost_optimization("task", [{"name": "a"}]) is None

    def test_cost_constraint_triggers_cheaper_model(self) -> None:
        sel = self._make_selector()
        resp = _make_httpx_response(
            {"response": '{"tool_name": "a", "confidence": 0.8, "reasoning": "x"}'}
        )
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            result = sel.select_tool_with_cost_optimization(
                "task", [{"name": "a", "description": "a"}], max_cost_per_request=0.0001
            )
            assert result is not None
            assert "model_used" in result

    def test_no_matching_provider_falls_through(self) -> None:
        ollama = _make_ollama()
        ollama.model = "different-model"
        sel = EnhancedAISelector(providers=[ollama])
        resp = _make_httpx_response(
            {"response": '{"tool_name": "a", "confidence": 0.8, "reasoning": "x"}'}
        )
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            result = sel.select_tool_with_cost_optimization(
                "task", [{"name": "a", "description": "a"}]
            )
            assert result is not None

    def test_no_provider_available_returns_none(self) -> None:
        non_ollama = MagicMock()
        non_ollama.model = "some-other-model"
        sel = EnhancedAISelector(providers=[non_ollama])
        result = sel.select_tool_with_cost_optimization(
            "task", [{"name": "a", "description": "a"}]
        )
        assert result is None

    def test_multi_cost_optimization_empty_tools(self) -> None:
        sel = self._make_selector()
        assert sel.select_tools_multi_with_cost_optimization("task", []) is None

    def test_multi_cost_constraint(self) -> None:
        sel = self._make_selector()
        resp = _make_httpx_response(
            {"response": '{"tools": ["a"], "confidence": 0.8, "reasoning": "x"}'}
        )
        with patch("httpx.Client") as mc:
            mc.return_value.__enter__.return_value.post.return_value = resp
            result = sel.select_tools_multi_with_cost_optimization(
                "task",
                [{"name": "a", "description": "a"}],
                max_cost_per_request=0.0001,
            )

    def test_multi_no_provider_returns_none(self) -> None:
        non_ollama = MagicMock()
        non_ollama.model = "other"
        sel = EnhancedAISelector(providers=[non_ollama])
        result = sel.select_tools_multi_with_cost_optimization(
            "task", [{"name": "a", "description": "a"}]
        )
        assert result is None


class TestTaskComplexity:
    """Cover _analyze_task_complexity branches."""

    def _complexity(self, task: str) -> str:
        sel = EnhancedAISelector(providers=[_make_ollama()])
        return sel._analyze_task_complexity(task)

    def test_simple_short_task(self) -> None:
        assert self._complexity("what is this?") == "simple"

    def test_simple_keyword(self) -> None:
        assert self._complexity("explain " + "x " * 30) == "simple"

    def test_complex_keyword(self) -> None:
        assert self._complexity("create " + "x " * 30) == "complex"

    def test_moderate_keyword(self) -> None:
        assert self._complexity("analyze " + "x " * 30) == "moderate"

    def test_unknown_fallback(self) -> None:
        assert self._complexity("something " + "y " * 30) == "unknown"


class TestSelectOptimalModelFallback:
    """Cover select_optimal_model when no suitable models fit hardware."""

    def test_fallback_to_tinyllama(self) -> None:
        sel = EnhancedAISelector(providers=[_make_ollama()])
        sel.hardware_constraints = {"max_model_ram_gb": 0.1}
        result = sel.select_optimal_model("complex", "balanced")
        assert result == AIModel.TINYLLAMA.value
