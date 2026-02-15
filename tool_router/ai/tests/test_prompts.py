"""Unit tests for prompt templates."""

from tool_router.ai.prompts import build_selection_prompt, format_tool_list


class TestPrompts:
    """Test prompt template functions."""

    def test_format_tool_list_basic(self):
        """Test basic tool list formatting."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
        ]

        result = format_tool_list(tools)

        assert "1. tool1: First tool" in result
        assert "2. tool2: Second tool" in result

    def test_format_tool_list_truncate_long_description(self):
        """Test truncation of long descriptions."""
        tools = [
            {
                "name": "tool1",
                "description": "A" * 200,  # Very long description
            }
        ]

        result = format_tool_list(tools)

        # format_tool_list truncates at 150 chars, replacing last 3 with "..."
        # Expected format: "1. tool1: " + 147 'A's + "..."
        assert "..." in result
        # The description part should be exactly 150 chars (147 'A's + "...")
        description_part = result.split(": ", 1)[1]
        assert len(description_part) == 150
        assert description_part == "A" * 147 + "..."

    def test_format_tool_list_missing_fields(self):
        """Test handling of missing name/description."""
        tools = [
            {},
            {"name": "tool2"},
            {"description": "desc"},
        ]

        result = format_tool_list(tools)

        assert "unknown" in result
        assert "No description" in result

    def test_build_selection_prompt(self):
        """Test complete prompt building."""
        task = "Search for Python tutorials"
        tools = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "read_file", "description": "Read a file"},
        ]

        prompt = build_selection_prompt(task, tools)

        assert "Search for Python tutorials" in prompt
        assert "web_search" in prompt
        assert "read_file" in prompt
        assert "tool_name" in prompt
        assert "confidence" in prompt
        assert "reasoning" in prompt

    def test_build_selection_prompt_json_format(self):
        """Test that prompt instructs JSON format."""
        tools = [{"name": "test", "description": "test tool"}]
        prompt = build_selection_prompt("test task", tools)

        assert "JSON" in prompt or "json" in prompt
        assert "{" in prompt
        assert "}" in prompt
