"""Unit tests for tool_router/args.py module."""

from tool_router.args import build_arguments
from tool_router.args.builder import COMMON_TASK_PARAMETER_NAMES


def test_common_task_parameter_names_exists() -> None:
    """Test that COMMON_TASK_PARAMETER_NAMES constant exists and has expected values."""
    assert isinstance(COMMON_TASK_PARAMETER_NAMES, list)
    assert len(COMMON_TASK_PARAMETER_NAMES) > 0
    assert "task" in COMMON_TASK_PARAMETER_NAMES
    assert "query" in COMMON_TASK_PARAMETER_NAMES
    assert "prompt" in COMMON_TASK_PARAMETER_NAMES


def test_build_arguments_basic() -> None:
    """Test build_arguments with basic input."""
    task = "search the web"
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "number"}
            },
            "required": ["query"]
        }
    }

    result = build_arguments(tool, task)

    assert isinstance(result, dict)
    assert "query" in result
    assert result["query"] == task


def test_build_arguments_with_task_param() -> None:
    """Test build_arguments when tool has 'task' parameter."""
    task = "create a file"
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "path": {"type": "string"}
            },
            "required": ["task"]
        }
    }

    result = build_arguments(tool, task)

    assert result == {"task": task}


def test_build_arguments_with_query_param() -> None:
    """Test build_arguments when tool has 'query' parameter."""
    task = "find documents"
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"}
            },
            "required": ["query"]
        }
    }

    result = build_arguments(tool, task)

    assert result == {"query": task}


def test_build_arguments_no_string_params() -> None:
    """Test build_arguments with no string parameters."""
    task = "process data"
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "number"},
                "enabled": {"type": "boolean"}
            },
            "required": ["count"]
        }
    }

    result = build_arguments(tool, task)

    # Should fall back to "task" since no common string parameters found and first required is not string
    assert result == {"task": task}


def test_build_arguments_empty_properties() -> None:
    """Test build_arguments with empty tool properties."""
    task = "simple task"
    tool = {}

    result = build_arguments(tool, task)

    # Should fall back to "task" parameter
    assert result == {"task": task}


def test_build_arguments_multiple_string_params() -> None:
    """Test build_arguments with multiple string parameters."""
    task = "search and filter"
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filter": {"type": "string"},
                "sort": {"type": "string"}
            },
            "required": ["query", "filter"]
        }
    }

    result = build_arguments(tool, task)

    # Should use the first common parameter found (query)
    assert result == {"query": task}


def test_common_task_parameter_names_priority() -> None:
    """Test that COMMON_TASK_PARAMETER_NAMES includes common parameter names in priority order."""
    expected_params = ["task", "query", "prompt", "text", "input"]

    for param in expected_params:
        assert param in COMMON_TASK_PARAMETER_NAMES, f"Missing common parameter: {param}"


def test_build_arguments_case_sensitivity() -> None:
    """Test build_arguments handles case sensitivity correctly."""
    task = "Test Task"
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "Task": {"type": "string"},  # Capital T
                "query": {"type": "string"}  # lowercase
            },
            "required": ["Task"]
        }
    }

    result = build_arguments(tool, task)

    # Should use "query" since it's in the common parameter list and comes before "Task"
    assert result == {"query": task}


def test_build_arguments_with_input_schema_alt() -> None:
    """Test build_arguments with input_schema (alternative key)."""
    task = "test task"
    tool = {
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"}
            },
            "required": ["prompt"]
        }
    }

    result = build_arguments(tool, task)

    assert result == {"prompt": task}
