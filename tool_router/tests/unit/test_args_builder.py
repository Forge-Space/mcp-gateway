"""Test cases for argument building functionality."""

from __future__ import annotations

from tool_router.args.builder import build_arguments


class TestBuildArguments:
    """Test cases for build_arguments function."""

    def test_build_arguments_with_query_param(self):
        """Test building arguments when tool has 'query' parameter."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "number"}
                },
                "required": ["query"]
            }
        }
        task = "search for files"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_task_param(self):
        """Test building arguments when tool has 'task' parameter."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "task": {"type": "string"},
                    "options": {"type": "object"}
                },
                "required": ["task"]
            }
        }
        task = "process data"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_with_search_param(self):
        """Test building arguments when tool has 'search' parameter."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "search": {"type": "string"}
                },
                "required": ["search"]
            }
        }
        task = "find documents"

        result = build_arguments(tool, task)

        assert result == {"search": task}

    def test_build_arguments_with_multiple_task_params(self):
        """Test building arguments when tool has multiple task-related parameters."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "task": {"type": "string"},
                    "search": {"type": "string"}
                },
                "required": ["query"]
            }
        }
        task = "test task"

        result = build_arguments(tool, task)

        # Should use the first matching parameter (query)
        assert result == {"query": task}

    def test_build_arguments_with_first_required_string_param(self):
        """Test building arguments using first required string parameter."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "filename": {"type": "string"},
                    "max_size": {"type": "number"}
                },
                "required": ["filename", "max_size"]
            }
        }
        task = "test.txt"

        result = build_arguments(tool, task)

        assert result == {"filename": task}

    def test_build_arguments_with_first_required_text_param(self):
        """Test building arguments using first required 'text' parameter."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "content": {"type": "text"},
                    "metadata": {"type": "object"}
                },
                "required": ["content", "metadata"]
            }
        }
        task = "sample content"

        result = build_arguments(tool, task)

        assert result == {"content": task}

    def test_build_arguments_ignores_non_string_required_param(self):
        """Test building arguments ignores non-string required parameters."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "count": {"type": "number"},
                    "size": {"type": "integer"}
                },
                "required": ["count", "size"]
            }
        }
        task = "test task"

        result = build_arguments(tool, task)

        # Should fall back to "task" parameter
        assert result == {"task": task}

    def test_build_arguments_with_no_schema(self):
        """Test building arguments when tool has no input schema."""
        tool = {"name": "test_tool"}
        task = "test task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_with_empty_schema(self):
        """Test building arguments when tool has empty input schema."""
        tool = {
            "name": "test_tool",
            "inputSchema": {}
        }
        task = "test task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_with_no_properties(self):
        """Test building arguments when schema has no properties."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "required": ["unknown_param"]  # Not in COMMON_TASK_PARAMETER_NAMES
            }
        }
        task = "test task"

        result = build_arguments(tool, task)

        # Should use the first required parameter even if not in common names
        assert result == {"unknown_param": task}

    def test_build_arguments_with_no_required(self):
        """Test building arguments when schema has no required parameters."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "optional": {"type": "string"}
                }
            }
        }
        task = "test task"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_input_schema_alt_key(self):
        """Test building arguments when tool uses 'input_schema' instead of 'inputSchema'."""
        tool = {
            "name": "test_tool",
            "input_schema": {
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
        task = "test task"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_untyped_required_param(self):
        """Test building arguments with untyped required parameter."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "data": {}  # No type specified
                },
                "required": ["data"]
            }
        }
        task = "test data"

        result = build_arguments(tool, task)

        assert result == {"data": task}

    def test_build_arguments_with_complex_task(self):
        """Test building arguments with complex task containing special characters."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
        task = "search for files with pattern '*.py' and content 'import pytest'"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_unicode_task(self):
        """Test building arguments with unicode characters in task."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
        task = "buscar archivos con emoji 🚀 y caracteres ñáéíóú"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_empty_task(self):
        """Test building arguments with empty task string."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
        task = ""

        result = build_arguments(tool, task)

        assert result == {"query": ""}

    def test_build_arguments_parameter_priority_order(self):
        """Test that parameters are checked in the correct priority order."""
        # Create a tool with multiple task parameters
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "message": {"type": "string"},  # Later in list
                    "query": {"type": "string"},    # First in list
                    "task": {"type": "string"}     # Middle in list
                },
                "required": ["message", "query", "task"]
            }
        }
        task = "test task"

        result = build_arguments(tool, task)

        # Should use "query" since it's first in TASK_PARAM_NAMES
        assert result == {"query": task}
