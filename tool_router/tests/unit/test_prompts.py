"""Test cases for AI prompt templates."""

from __future__ import annotations

from tool_router.ai.prompts import PromptTemplates


class TestPromptTemplates:
    """Test cases for PromptTemplates class."""

    def test_tool_selection_template_format(self) -> None:
        template = PromptTemplates.TOOL_SELECTION_TEMPLATE
        assert "{task}" in template
        assert "{tool_list}" in template
        assert "tool_name" in template
        assert "confidence" in template
        assert "reasoning" in template

    def test_create_tool_selection_prompt_basic(self) -> None:
        task = "Search the web"
        tool_list = "- search_web: Search the web"
        result = PromptTemplates.create_tool_selection_prompt(task, tool_list)
        assert task in result
        assert tool_list in result
        assert "tool_name" in result
        assert "confidence" in result
        assert "reasoning" in result

    def test_create_tool_selection_prompt_with_context(self) -> None:
        task = "Search the web"
        tool_list = "- search_web: Search the web"
        context = "User is looking for recent news"
        result = PromptTemplates.create_tool_selection_prompt(task, tool_list, context=context)
        assert task in result
        assert tool_list in result
        assert context in result
        assert "Context:" in result

    def test_create_tool_selection_prompt_no_context_section_when_empty(self) -> None:
        result = PromptTemplates.create_tool_selection_prompt("task", "- tool: desc", context="")
        assert "Context:" not in result

    def test_create_tool_selection_prompt_with_similar_tools(self) -> None:
        task = "Search the web"
        tool_list = "- search_web: Search the web"
        similar_tools = ["search_web", "find_info"]
        result = PromptTemplates.create_tool_selection_prompt(task, tool_list, similar_tools=similar_tools)
        assert "search_web" in result
        assert "find_info" in result
        assert "Historically successful tools" in result

    def test_create_tool_selection_prompt_no_history_when_none(self) -> None:
        result = PromptTemplates.create_tool_selection_prompt("task", "- tool: desc", similar_tools=None)
        assert "Historically successful tools" not in result

    def test_create_tool_selection_prompt_with_all_parameters(self) -> None:
        task = "Search the web"
        tool_list = "- search_web: Search the web"
        context = "User is looking for recent news"
        similar_tools = ["search_web", "find_info"]
        result = PromptTemplates.create_tool_selection_prompt(
            task, tool_list, context=context, similar_tools=similar_tools
        )
        assert task in result
        assert tool_list in result
        assert context in result
        assert "search_web" in result
        assert "find_info" in result

    def test_create_tool_selection_prompt_empty_task(self) -> None:
        result = PromptTemplates.create_tool_selection_prompt("", "- test_tool: Test tool")
        assert "- test_tool: Test tool" in result

    def test_create_tool_selection_prompt_empty_tool_list(self) -> None:
        result = PromptTemplates.create_tool_selection_prompt("Test task", "")
        assert "Test task" in result

    def test_create_tool_selection_prompt_complex_task(self) -> None:
        task = "Search for files with pattern '*.py' and content 'import pytest'"
        tool_list = "1. file_search - Search files\n2. content_search - Search content"
        result = PromptTemplates.create_tool_selection_prompt(task, tool_list)
        assert task in result
        assert "*.py" in result
        assert "import pytest" in result

    def test_create_tool_selection_prompt_unicode_content(self) -> None:
        task = "Search for files with emoji \U0001f680 and unicode \xf1\xe1\xe9\xed\xf3\xfa"
        result = PromptTemplates.create_tool_selection_prompt(task, "- tool: desc")
        assert "\U0001f680" in result

    def test_create_tool_selection_prompt_long_content(self) -> None:
        task = "A" * 1000
        tool_list = "B" * 500
        result = PromptTemplates.create_tool_selection_prompt(task, tool_list)
        assert task in result
        assert tool_list in result
        assert len(result) > 1500

    def test_create_tool_selection_prompt_json_structure(self) -> None:
        result = PromptTemplates.create_tool_selection_prompt("Test task", "- test_tool: Test tool")
        assert '"tool_name"' in result
        assert '"confidence"' in result
        assert '"reasoning"' in result

    def test_create_tool_selection_prompt_is_deterministic(self) -> None:
        task = "Test task"
        tool_list = "1. test_tool - Test tool"
        assert (
            PromptTemplates.create_tool_selection_prompt(task, tool_list)
            == PromptTemplates.create_tool_selection_prompt(task, tool_list)
        )

    def test_create_tool_selection_prompt_different_inputs(self) -> None:
        tool_list = "1. test_tool - Test tool"
        result1 = PromptTemplates.create_tool_selection_prompt("Task 1", tool_list)
        result2 = PromptTemplates.create_tool_selection_prompt("Task 2", tool_list)
        assert result1 != result2
        assert "Task 1" in result1
        assert "Task 2" in result2

    def test_create_multi_tool_selection_prompt_basic(self) -> None:
        task = "Search then save results"
        tool_list = "- search_web: Search\n- save_file: Save to file"
        result = PromptTemplates.create_multi_tool_selection_prompt(task, tool_list)
        assert task in result
        assert tool_list in result
        assert '"tools"' in result
        assert '"confidence"' in result
        assert '"reasoning"' in result

    def test_create_multi_tool_selection_prompt_max_tools(self) -> None:
        result = PromptTemplates.create_multi_tool_selection_prompt(
            "task", "- tool: desc", max_tools=5
        )
        assert "5" in result

    def test_create_multi_tool_selection_prompt_with_context(self) -> None:
        result = PromptTemplates.create_multi_tool_selection_prompt(
            "task", "- tool: desc", context="some context"
        )
        assert "some context" in result
        assert "Context:" in result

    def test_create_multi_tool_selection_prompt_no_context_when_empty(self) -> None:
        result = PromptTemplates.create_multi_tool_selection_prompt("task", "- tool: desc", context="")
        assert "Context:" not in result
