"""Tests for tool_router.args module."""

from __future__ import annotations

from tool_router.args.builder import COMMON_TASK_PARAMETER_NAMES, build_arguments


class TestBuildArguments:
    """Test cases for the build_arguments function."""

    def test_task_param_names_list(self):
        """Test that COMMON_TASK_PARAMETER_NAMES is properly defined."""
        assert isinstance(COMMON_TASK_PARAMETER_NAMES, list)
        assert len(COMMON_TASK_PARAMETER_NAMES) > 0
        assert all(isinstance(name, str) for name in COMMON_TASK_PARAMETER_NAMES)
        assert "query" in COMMON_TASK_PARAMETER_NAMES
        assert "task" in COMMON_TASK_PARAMETER_NAMES

    def test_build_arguments_with_query_param(self):
        """Test building arguments when tool has 'query' parameter."""
        tool = {
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["query"],
            }
        }
        task = "find information about Python"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_q_param(self):
        """Test building arguments when tool has 'q' parameter."""
        tool = {
            "input_schema": {
                "properties": {
                    "q": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["q"],
            }
        }
        task = "search for React components"

        result = build_arguments(tool, task)

        assert result == {"q": task}

    def test_build_arguments_with_task_param(self):
        """Test building arguments when tool has 'task' parameter."""
        tool = {
            "inputSchema": {
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "string"},
                },
                "required": ["task"],
            }
        }
        task = "generate a button component"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_with_search_param(self):
        """Test building arguments when tool has 'search' parameter."""
        tool = {
            "inputSchema": {
                "properties": {
                    "search": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["search"],
            }
        }
        task = "search for documentation"

        result = build_arguments(tool, task)

        assert result == {"search": task}

    def test_build_arguments_prefer_query_over_q(self):
        """Test that 'query' is preferred over 'q' when both exist."""
        tool = {
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "q": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query", "q"],
            }
        }
        task = "test query preference"

        result = build_arguments(tool, task)

        # Should prefer the first matching param (query)
        assert result == {"query": task}

    def test_build_arguments_with_first_required_string_param(self):
        """Test building arguments using first required string parameter."""
        tool = {
            "inputSchema": {
                "properties": {
                    "description": {"type": "string"},
                    "count": {"type": "integer"},
                },
                "required": ["description"],
            }
        }
        task = "describe the functionality"

        result = build_arguments(tool, task)

        assert result == {"description": task}

    def test_build_arguments_with_first_required_text_param(self):
        """Test building arguments using first required text parameter."""
        tool = {
            "inputSchema": {
                "properties": {
                    "content": {"type": "text"},
                    "metadata": {"type": "object"},
                },
                "required": ["content"],
            }
        }
        task = "process this content"

        result = build_arguments(tool, task)

        assert result == {"content": task}

    def test_build_arguments_with_first_required_non_string_param(self):
        """Test building arguments when first required param is not string."""
        tool = {
            "inputSchema": {
                "properties": {
                    "count": {"type": "integer"},
                    "description": {"type": "string"},
                },
                "required": ["count", "description"],
            }
        }
        task = "process 5 items"

        result = build_arguments(tool, task)

        # Should fall back to 'task' since first required param is not string
        assert result == {"task": task}

    def test_build_arguments_fallback_to_task(self):
        """Test building arguments falls back to 'task' when no suitable param found."""
        tool = {
            "inputSchema": {
                "properties": {
                    "count": {"type": "integer"},
                    "metadata": {"type": "object"},
                },
                "required": ["count"],
            }
        }
        task = "process data"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_no_schema(self):
        """Test building arguments when tool has no schema."""
        tool = {}
        task = "simple task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_empty_schema(self):
        """Test building arguments when schema is empty."""
        tool = {"inputSchema": {}}
        task = "simple task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_empty_properties(self):
        """Test building arguments when schema has no properties."""
        tool = {"inputSchema": {"properties": {}, "required": []}}
        task = "simple task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_no_required_params(self):
        """Test building arguments when no parameters are required."""
        tool = {
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": [],
            }
        }
        task = "search query"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_input_schema_alias(self):
        """Test building arguments with input_schema alias."""
        tool = {
            "input_schema": {
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            }
        }
        task = "search query"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_complex_tool(self):
        """Test building arguments for a complex tool with multiple parameters."""
        tool = {
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 10},
                    "filters": {"type": "object"},
                    "sort": {"type": "string"},
                },
                "required": ["query"],
            }
        }
        task = "find React components"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_edge_cases(self):
        """Test edge cases for argument building."""
        # Empty task
        tool = {
            "inputSchema": {
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            }
        }

        result = build_arguments(tool, "")

        assert result == {"query": ""}

        # None task
        tool = {
            "inputSchema": {
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            }
        }

        result = build_arguments(tool, None)

        assert result == {"query": None}
