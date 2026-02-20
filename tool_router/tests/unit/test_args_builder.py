"""Unit tests for tool_router/args/builder.py module."""

from __future__ import annotations

from tool_router.args.builder import build_arguments


class TestBuildArguments:
    """Test the build_arguments function."""

    def test_build_arguments_with_task_param_in_schema(self) -> None:
        """Test build_arguments when schema has a 'task' parameter."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "string"},
                },
                "required": ["task"],
            }
        }
        task = "Search the web"
        result = build_arguments(tool_definition, task)
        assert result == {"task": task}

    def test_build_arguments_with_query_param_in_schema(self) -> None:
        """Test build_arguments when schema has a 'query' parameter."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["query"],
            }
        }
        task = "Find information about Python"
        result = build_arguments(tool_definition, task)
        assert result == {"query": task}

    def test_build_arguments_with_first_required_string_param(self) -> None:
        """Test build_arguments with first required string parameter."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["search_term", "limit"],
            }
        }
        task = "Search for books"
        result = build_arguments(tool_definition, task)
        assert result == {"search_term": task}

    def test_build_arguments_fallback_to_task_param(self) -> None:
        """Test build_arguments falls back to 'task' parameter."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"},
                },
                "required": ["limit"],
            }
        }
        task = "Some task"
        result = build_arguments(tool_definition, task)
        assert result == {"task": task}

    def test_build_arguments_empty_schema(self) -> None:
        """Test build_arguments with empty schema."""
        tool_definition = {"inputSchema": {}}
        task = "Test task"
        result = build_arguments(tool_definition, task)
        assert result == {"task": task}

    def test_build_arguments_no_input_schema(self) -> None:
        """Test build_arguments when inputSchema is missing."""
        tool_definition = {}
        task = "Test task"
        result = build_arguments(tool_definition, task)
        assert result == {"task": task}

    def test_build_arguments_no_properties(self) -> None:
        """Test build_arguments when schema has no properties."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "required": ["something"],
            }
        }
        task = "Test task"
        result = build_arguments(tool_definition, task)
        assert result == {"something": task}

    def test_build_arguments_no_required_params(self) -> None:
        """Test build_arguments when no required parameters."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "optional_param": {"type": "string"},
                },
            }
        }
        task = "Test task"
        result = build_arguments(tool_definition, task)
        assert result == {"task": task}

    def test_build_arguments_non_string_required_param(self) -> None:
        """Test build_arguments when first required param is not a string."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["count", "text"],
            }
        }
        task = "Test task"
        result = build_arguments(tool_definition, task)
        assert result == {"text": task}

    def test_build_arguments_with_multiple_task_params(self) -> None:
        """Test build_arguments prioritizes task parameters."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "prompt": {"type": "string"},
                    "context": {"type": "string"},
                },
                "required": ["query", "prompt"],
            }
        }
        task = "Search query"
        result = build_arguments(tool_definition, task)
        assert result == {"query": task}

    def test_build_arguments_case_sensitivity(self) -> None:
        """Test build_arguments is case sensitive."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "Task": {"type": "string"},  # Capital T
                    "query": {"type": "string"},
                },
                "required": ["Task"],
            }
        }
        task = "Test task"
        result = build_arguments(tool_definition, task)
        assert result == {"query": task}  # Uses query from common list

    def test_build_arguments_with_complex_schema(self) -> None:
        """Test build_arguments with complex nested schema."""
        tool_definition = {
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "max_tokens": {"type": "integer"},
                            "temperature": {"type": "number"},
                        },
                    },
                },
                "required": ["prompt"],
            }
        }
        task = "Generate a story"
        result = build_arguments(tool_definition, task)
        assert result == {"prompt": task}
