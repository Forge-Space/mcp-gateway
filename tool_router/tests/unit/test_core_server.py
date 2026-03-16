"""Unit tests for tool_router/core/server.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import tool_router.core.server as server_mod
from tool_router.core.server import (
    execute_specialist_task,
    execute_task,
    execute_tasks,
    get_specialist_stats,
    initialize_ai,
    optimize_prompt,
    record_feedback,
    search_tools,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_tool(name: str = "tool_a", description: str = "A test tool") -> dict:
    return {"name": name, "description": description, "inputSchema": {"properties": {}}}


def _make_security_result(
    allowed: bool = True,
    blocked_reason: str | None = None,
    risk_score: float = 0.0,
    task: str = "do something",
    context: str = "",
    prefs: str = "{}",
) -> MagicMock:
    result = MagicMock()
    result.allowed = allowed
    result.blocked_reason = blocked_reason
    result.risk_score = risk_score
    result.violations = []
    result.sanitized_inputs = {"task": task, "context": context, "user_preferences": prefs}
    return result


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset all module-level globals before and after every test."""
    originals = (
        server_mod._ai_selector,
        server_mod._enhanced_ai_selector,
        server_mod._specialist_coordinator,
        server_mod._feedback_store,
        server_mod._config,
        server_mod._security_middleware,
    )
    yield
    (
        server_mod._ai_selector,
        server_mod._enhanced_ai_selector,
        server_mod._specialist_coordinator,
        server_mod._feedback_store,
        server_mod._config,
        server_mod._security_middleware,
    ) = originals


def _make_config(ai_enabled: bool = True) -> MagicMock:
    cfg = MagicMock()
    cfg.ai.enabled = ai_enabled
    cfg.ai.endpoint = "http://localhost:11434"
    cfg.ai.model = "llama3"
    cfg.ai.timeout_ms = 5000
    cfg.ai.min_confidence = 0.5
    cfg.ai.weight = 0.7
    return cfg


# ---------------------------------------------------------------------------
# initialize_ai tests
# ---------------------------------------------------------------------------


class TestInitializeAi:
    def test_ai_enabled_success_sets_all_globals(self):
        """All three AI globals are set when AI is enabled and no exception occurs."""
        cfg = _make_config(ai_enabled=True)

        mock_selector = MagicMock()
        mock_enhanced = MagicMock()
        mock_coordinator = MagicMock()
        mock_prompt = MagicMock()
        mock_ui = MagicMock()
        mock_feedback = MagicMock()
        mock_security = MagicMock()

        with (
            patch("tool_router.core.server.FeedbackStore", return_value=mock_feedback),
            patch("tool_router.core.server.SecurityMiddleware", return_value=mock_security),
            patch("tool_router.core.server.OllamaSelector", return_value=mock_selector),
            patch("tool_router.core.server.EnhancedAISelector", return_value=mock_enhanced),
            patch("tool_router.core.server.PromptArchitect", return_value=mock_prompt),
            patch("tool_router.core.server.UISpecialist", return_value=mock_ui),
            patch("tool_router.core.server.SpecialistCoordinator", return_value=mock_coordinator),
            patch("pathlib.Path.exists", return_value=False),
        ):
            initialize_ai(cfg)

        assert server_mod._ai_selector is mock_selector
        assert server_mod._enhanced_ai_selector is mock_enhanced
        assert server_mod._specialist_coordinator is mock_coordinator
        assert server_mod._feedback_store is mock_feedback
        assert server_mod._security_middleware is mock_security

    def test_ai_enabled_exception_sets_selectors_to_none(self):
        """When AI initialization raises, all three AI globals are set to None."""
        cfg = _make_config(ai_enabled=True)

        with (
            patch("tool_router.core.server.FeedbackStore", return_value=MagicMock()),
            patch("tool_router.core.server.SecurityMiddleware", return_value=MagicMock()),
            patch("tool_router.core.server.OllamaSelector", side_effect=RuntimeError("boom")),
            patch("pathlib.Path.exists", return_value=False),
        ):
            initialize_ai(cfg)

        assert server_mod._ai_selector is None
        assert server_mod._enhanced_ai_selector is None
        assert server_mod._specialist_coordinator is None

    def test_ai_disabled_sets_selectors_to_none(self):
        """When AI is disabled all three AI globals are None."""
        cfg = _make_config(ai_enabled=False)

        with (
            patch("tool_router.core.server.FeedbackStore", return_value=MagicMock()),
            patch("tool_router.core.server.SecurityMiddleware", return_value=MagicMock()),
            patch("pathlib.Path.exists", return_value=False),
        ):
            initialize_ai(cfg)

        assert server_mod._ai_selector is None
        assert server_mod._enhanced_ai_selector is None
        assert server_mod._specialist_coordinator is None

    def test_security_yaml_oserror_continues(self):
        """OSError while loading security.yaml is handled gracefully."""
        cfg = _make_config(ai_enabled=False)

        with (
            patch("tool_router.core.server.FeedbackStore", return_value=MagicMock()),
            patch("tool_router.core.server.SecurityMiddleware", return_value=MagicMock()),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.open", side_effect=OSError("file locked")),
        ):
            # Should not raise
            initialize_ai(cfg)

        # SecurityMiddleware still created (with empty config)
        assert server_mod._security_middleware is not None


# ---------------------------------------------------------------------------
# execute_task tests
# ---------------------------------------------------------------------------


class TestExecuteTask:
    def test_no_tools_returns_message(self):
        """Returns the 'no tools' message when the gateway has no tools."""
        with patch("tool_router.core.server.get_tools", return_value=[]):
            result = execute_task("do something")
        assert result == "No tools registered in the gateway."

    def test_no_ai_selector_uses_keyword_matching(self):
        """Keyword matching is used when _ai_selector is None."""
        tool = _make_tool()
        server_mod._ai_selector = None

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool]),
            patch(
                "tool_router.core.server.select_top_matching_tools",
                return_value=[tool],
            ) as mock_keyword,
            patch("tool_router.core.server.build_arguments", return_value={}),
            patch("tool_router.core.server.call_tool", return_value="ok"),
        ):
            result = execute_task("do something")

        mock_keyword.assert_called_once()
        assert result == "ok"

    def test_ai_selector_uses_hybrid_selection(self):
        """Hybrid selection is used when _ai_selector and _config are set."""
        tool = _make_tool()
        server_mod._ai_selector = MagicMock()
        server_mod._config = _make_config()

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool]),
            patch(
                "tool_router.core.server.select_top_matching_tools_hybrid",
                return_value=[tool],
            ) as mock_hybrid,
            patch("tool_router.core.server.build_arguments", return_value={}),
            patch("tool_router.core.server.call_tool", return_value="result"),
        ):
            result = execute_task("do something")

        mock_hybrid.assert_called_once()
        assert result == "result"

    def test_get_tools_value_error_returns_error_string(self):
        """ValueError from get_tools surfaces as an error string."""
        with patch("tool_router.core.server.get_tools", side_effect=ValueError("bad")):
            result = execute_task("task")
        assert "Failed to list tools" in result

    def test_call_tool_result_returned_as_string(self):
        """The raw string from call_tool is returned to the caller."""
        tool = _make_tool()
        server_mod._ai_selector = None

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool]),
            patch("tool_router.core.server.select_top_matching_tools", return_value=[tool]),
            patch("tool_router.core.server.build_arguments", return_value={}),
            patch("tool_router.core.server.call_tool", return_value="the-result-string"),
        ):
            result = execute_task("task")

        assert result == "the-result-string"

    def test_feedback_recorded_when_store_set(self):
        """_feedback_store.record is called after a successful tool invocation."""
        tool = _make_tool()
        mock_store = MagicMock()
        server_mod._feedback_store = mock_store
        server_mod._ai_selector = None

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool]),
            patch("tool_router.core.server.select_top_matching_tools", return_value=[tool]),
            patch("tool_router.core.server.build_arguments", return_value={}),
            patch("tool_router.core.server.call_tool", return_value="done"),
        ):
            execute_task("task", context="ctx")

        mock_store.record.assert_called_once_with(
            task="task",
            selected_tool="tool_a",
            success=True,
            context="ctx",
        )

    def test_get_tools_unexpected_error_returns_error_string(self):
        """An unexpected exception from get_tools returns an error string."""
        with patch("tool_router.core.server.get_tools", side_effect=RuntimeError("oops")):
            result = execute_task("task")
        assert "Unexpected error listing tools" in result

    def test_no_matching_tool_returns_message(self):
        """Returns a descriptive message when no tool matches the task."""
        tool = _make_tool()
        server_mod._ai_selector = None

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool]),
            patch("tool_router.core.server.select_top_matching_tools", return_value=[]),
        ):
            result = execute_task("unmatchable task")

        assert "No matching tool found" in result


# ---------------------------------------------------------------------------
# execute_tasks tests
# ---------------------------------------------------------------------------


class TestExecuteTasks:
    def test_no_tools_returns_message(self):
        """Returns the 'no tools' message when gateway has no tools."""
        with patch("tool_router.core.server.get_tools", return_value=[]):
            result = execute_tasks("task")
        assert result == "No tools registered in the gateway."

    def test_multi_tool_chaining_returns_combined_results(self):
        """Results from multiple tools are combined into a single output string."""
        tool_a = _make_tool("tool_a", "desc a")
        tool_b = _make_tool("tool_b", "desc b")
        server_mod._ai_selector = None

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool_a, tool_b]),
            patch(
                "tool_router.core.server.select_top_matching_tools",
                return_value=[tool_a, tool_b],
            ),
            patch("tool_router.core.server.build_arguments", return_value={}),
            patch("tool_router.core.server.call_tool", side_effect=["result_a", "result_b"]),
        ):
            result = execute_tasks("complex task", max_tools=2)

        assert "[tool_a] result_a" in result
        assert "[tool_b] result_b" in result

    def test_get_tools_error_returns_error_string(self):
        """An exception from get_tools surfaces as an error string."""
        with patch("tool_router.core.server.get_tools", side_effect=ConnectionError("down")):
            result = execute_tasks("task")
        assert "Failed to list tools" in result


# ---------------------------------------------------------------------------
# record_feedback tests
# ---------------------------------------------------------------------------


class TestRecordFeedback:
    def test_no_store_returns_error_string(self):
        """Returns an error message when _feedback_store is None."""
        server_mod._feedback_store = None
        result = record_feedback("tool_a", "task", success=True)
        assert "not initialized" in result.lower()

    def test_with_store_records_and_returns_rate(self):
        """Records feedback and returns a success-rate string."""
        mock_store = MagicMock()
        mock_stats = MagicMock()
        mock_stats.success_rate = 0.8
        mock_store.get_stats.return_value = mock_stats
        server_mod._feedback_store = mock_store

        result = record_feedback("tool_a", "task", success=True)

        mock_store.record.assert_called_once()
        assert "80%" in result
        assert "tool_a" in result


# ---------------------------------------------------------------------------
# search_tools tests
# ---------------------------------------------------------------------------


class TestSearchTools:
    def test_matching_tools_returns_formatted_list(self):
        """Returns a numbered list of matching tools."""
        tool = _make_tool("my_tool", "Does something cool")

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool]),
            patch(
                "tool_router.core.server.select_top_matching_tools",
                return_value=[tool],
            ),
        ):
            result = search_tools("something")

        assert "my_tool" in result
        assert "Does something cool" in result
        assert "1." in result

    def test_no_tools_returns_no_tools_message(self):
        """Returns 'no tools registered' when gateway is empty."""
        with patch("tool_router.core.server.get_tools", return_value=[]):
            result = search_tools("query")
        assert "No tools registered" in result

    def test_no_matching_tools_returns_not_found_message(self):
        """Returns a 'no tools found' message when nothing matches."""
        tool = _make_tool()

        with (
            patch("tool_router.core.server.get_tools", return_value=[tool]),
            patch("tool_router.core.server.select_top_matching_tools", return_value=[]),
        ):
            result = search_tools("unrelated query")

        assert "No tools found matching" in result

    def test_get_tools_error_returns_error_string(self):
        """A ValueError from get_tools surfaces as an error string."""
        with patch("tool_router.core.server.get_tools", side_effect=ValueError("fail")):
            result = search_tools("query")
        assert "Failed to list tools" in result

    def test_get_tools_unexpected_error_returns_error_string(self):
        """An unexpected exception from get_tools returns an error string."""
        with patch("tool_router.core.server.get_tools", side_effect=KeyError("bad")):
            result = search_tools("query")
        assert "Unexpected error listing tools" in result


# ---------------------------------------------------------------------------
# execute_specialist_task tests
# ---------------------------------------------------------------------------


class TestExecuteSpecialistTask:
    def test_coordinator_none_returns_error(self):
        """Returns an error string when _specialist_coordinator is None."""
        server_mod._specialist_coordinator = None
        result = execute_specialist_task("task")
        assert "not initialized" in result.lower()

    def test_middleware_none_returns_error(self):
        """Returns an error string when _security_middleware is None."""
        server_mod._specialist_coordinator = MagicMock()
        server_mod._security_middleware = None
        result = execute_specialist_task("task")
        assert "not initialized" in result.lower()

    def test_security_blocked_returns_blocked_message(self):
        """Returns a 'blocked' message when the security check fails."""
        mock_coordinator = MagicMock()
        mock_middleware = MagicMock()
        security_result = _make_security_result(allowed=False, blocked_reason="injection detected")
        mock_middleware.check_request_security.return_value = security_result

        server_mod._specialist_coordinator = mock_coordinator
        server_mod._security_middleware = mock_middleware

        result = execute_specialist_task("malicious task")
        assert "blocked" in result.lower()
        assert "injection detected" in result

    def test_valid_request_returns_formatted_result(self):
        """A successful specialist task returns formatted output."""
        mock_coordinator = MagicMock()
        mock_middleware = MagicMock()
        mock_middleware.check_request_security.return_value = _make_security_result(task="do something")

        specialist_result = MagicMock()
        specialist_result.specialist_type.value = "router"
        specialist_result.confidence = 0.9
        specialist_result.processing_time_ms = 42.0
        specialist_result.cost_estimate = 0.001
        specialist_result.metadata = {"model_used": "llama3", "model_tier": "fast", "task_complexity": "low"}
        # Use the real SpecialistType so isinstance checks work
        from tool_router.specialist_coordinator import SpecialistType

        specialist_result.specialist_type = SpecialistType.ROUTER
        specialist_result.metadata = {"model_used": "llama3", "model_tier": "fast", "task_complexity": "low"}

        mock_coordinator.process_task.return_value = [specialist_result]

        server_mod._specialist_coordinator = mock_coordinator
        server_mod._security_middleware = mock_middleware

        result = execute_specialist_task("do something")
        assert "specialist" in result.lower() or "Processed" in result

    def test_exception_in_coordinator_returns_error_string(self):
        """An exception inside process_task returns an error string."""
        mock_coordinator = MagicMock()
        mock_middleware = MagicMock()
        mock_middleware.check_request_security.return_value = _make_security_result()
        mock_coordinator.process_task.side_effect = RuntimeError("crash")

        server_mod._specialist_coordinator = mock_coordinator
        server_mod._security_middleware = mock_middleware

        result = execute_specialist_task("task")
        assert "Error executing specialist task" in result


# ---------------------------------------------------------------------------
# get_specialist_stats tests
# ---------------------------------------------------------------------------


class TestGetSpecialistStats:
    def test_coordinator_none_returns_error(self):
        """Returns an error string when _specialist_coordinator is None."""
        server_mod._specialist_coordinator = None
        result = get_specialist_stats()
        assert "not initialized" in result.lower()

    def test_success_returns_stats_string(self):
        """Returns a formatted statistics string on success."""
        mock_coordinator = MagicMock()
        mock_coordinator.get_routing_stats.return_value = {
            "total_requests": 10,
            "average_processing_time": 50.5,
            "total_cost_saved": 0.025,
            "cache_size": 5,
            "specialist_distribution": {
                "router": 6,
                "prompt_architect": 2,
                "ui_specialist": 1,
                "multi_specialist": 1,
            },
        }
        mock_coordinator.get_specialist_capabilities.return_value = {
            "router": {"hardware_aware_routing": True, "cost_optimization": True},
        }
        server_mod._specialist_coordinator = mock_coordinator

        result = get_specialist_stats()
        assert "10" in result  # total_requests
        assert "Router Agent" in result or "router" in result.lower()

    def test_exception_returns_error_string(self):
        """An exception from get_routing_stats returns an error string."""
        mock_coordinator = MagicMock()
        mock_coordinator.get_routing_stats.side_effect = RuntimeError("db failure")
        server_mod._specialist_coordinator = mock_coordinator

        result = get_specialist_stats()
        assert "Error getting specialist stats" in result


# ---------------------------------------------------------------------------
# optimize_prompt tests
# ---------------------------------------------------------------------------


class TestOptimizePrompt:
    def test_coordinator_none_returns_error(self):
        """Returns an error string when _specialist_coordinator is None."""
        server_mod._specialist_coordinator = None
        result = optimize_prompt("my prompt")
        assert "not initialized" in result.lower()

    def test_success_returns_optimization_result(self):
        """Returns the formatted optimization output on success."""
        from tool_router.specialist_coordinator import SpecialistType

        mock_coordinator = MagicMock()

        specialist_result = MagicMock()
        specialist_result.specialist_type = SpecialistType.PROMPT_ARCHITECT
        specialist_result.result = {
            "optimized_prompt": "better prompt",
            "token_metrics": {
                "original_tokens": 100,
                "optimized_tokens": 70,
                "token_reduction_percent": 30.0,
                "cost_savings": 0.0003,
            },
            "quality_score": {
                "overall_score": 0.85,
                "clarity": 0.9,
                "completeness": 0.8,
                "specificity": 0.85,
                "token_efficiency": 0.87,
            },
            "task_type": "analysis",
            "requirements": [
                {"type": "clarity", "priority": "high"},
            ],
        }
        mock_coordinator.process_task.return_value = [specialist_result]
        server_mod._specialist_coordinator = mock_coordinator

        result = optimize_prompt("my long prompt", cost_preference="efficient")
        assert "better prompt" in result
        assert "Token reduction" in result or "token" in result.lower()

    def test_exception_returns_error_string(self):
        """An exception inside process_task returns an error string."""
        mock_coordinator = MagicMock()
        mock_coordinator.process_task.side_effect = ValueError("bad input")
        server_mod._specialist_coordinator = mock_coordinator

        result = optimize_prompt("prompt")
        assert "Error optimizing prompt" in result
