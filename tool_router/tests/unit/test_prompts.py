"""Unit tests for AI prompt templates."""

from __future__ import annotations

from tool_router.ai.prompts import PromptTemplates


class TestPromptTemplates:
    """Tests for PromptTemplates class."""

    def test_template_contains_placeholders(self) -> None:
        """Test that the template string contains required placeholders."""
        assert "{task}" in PromptTemplates.TOOL_SELECTION_TEMPLATE
        assert "{tool_list}" in PromptTemplates.TOOL_SELECTION_TEMPLATE

    def test_template_contains_json_instruction(self) -> None:
        """Test that the template instructs JSON response format."""
        assert "JSON" in PromptTemplates.TOOL_SELECTION_TEMPLATE
        assert "tool_name" in PromptTemplates.TOOL_SELECTION_TEMPLATE
        assert "confidence" in PromptTemplates.TOOL_SELECTION_TEMPLATE

    def test_create_prompt_inserts_task(self) -> None:
        """Test that create_tool_selection_prompt inserts the task correctly."""
        prompt = PromptTemplates.create_tool_selection_prompt(
            task="search the web",
            tool_list="- search: Search the web",
        )
        assert "search the web" in prompt

    def test_create_prompt_inserts_tool_list(self) -> None:
        """Test that create_tool_selection_prompt inserts the tool list correctly."""
        tool_list = "- search: Search the web\n- fetch: Fetch a URL"
        prompt = PromptTemplates.create_tool_selection_prompt(
            task="find something",
            tool_list=tool_list,
        )
        assert tool_list in prompt

    def test_create_prompt_returns_string(self) -> None:
        """Test that create_tool_selection_prompt returns a string."""
        result = PromptTemplates.create_tool_selection_prompt(
            task="task",
            tool_list="tools",
        )
        assert isinstance(result, str)

    def test_create_prompt_empty_inputs(self) -> None:
        """Test that create_tool_selection_prompt handles empty strings."""
        prompt = PromptTemplates.create_tool_selection_prompt(task="", tool_list="")
        assert isinstance(prompt, str)
        assert "{task}" not in prompt
        assert "{tool_list}" not in prompt

    def test_create_prompt_special_characters(self) -> None:
        """Test that special characters in task/tool_list are preserved."""
        task = "search for 'hello world' & more"
        tool_list = "- tool: Does <something> special"
        prompt = PromptTemplates.create_tool_selection_prompt(task=task, tool_list=tool_list)
        assert task in prompt
        assert tool_list in prompt
