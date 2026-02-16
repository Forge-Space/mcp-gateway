from __future__ import annotations

import pytest

from tool_router.args import build_arguments


def test_build_arguments_prefers_query() -> None:
    tool = {"inputSchema": {"properties": {"query": {"type": "string"}}}}
    assert build_arguments(tool, "my task") == {"query": "my task"}


def test_build_arguments_uses_q_when_no_query() -> None:
    tool = {"inputSchema": {"properties": {"q": {"type": "string"}}}}
    assert build_arguments(tool, "my task") == {"q": "my task"}


def test_build_arguments_uses_search_when_no_query_or_q() -> None:
    tool = {"inputSchema": {"properties": {"search": {"type": "string"}}}}
    assert build_arguments(tool, "my task") == {"search": "my task"}


def test_build_arguments_uses_first_required() -> None:
    tool = {"inputSchema": {"properties": {"url": {}}, "required": ["url"]}}
    assert build_arguments(tool, "https://example.com") == {"url": "https://example.com"}


def test_build_arguments_falls_back_to_task() -> None:
    tool = {"inputSchema": {"properties": {}}}
    assert build_arguments(tool, "do something") == {"task": "do something"}


def test_build_arguments_accepts_input_schema_snake_case() -> None:
    tool = {"input_schema": {"properties": {"query": {}}}}
    assert build_arguments(tool, "hello") == {"query": "hello"}


# Additional comprehensive tests


@pytest.mark.parametrize(
    "param_name",
    ["query", "q", "search", "task", "prompt", "question", "input", "text", "message", "command"],
)
def test_build_arguments_all_task_param_names(param_name: str) -> None:
    """Test that all common task parameter names are recognized."""
    tool = {"inputSchema": {"properties": {param_name: {"type": "string"}}}}
    args = build_arguments(tool, "test task")
    assert args == {param_name: "test task"}


def test_build_arguments_no_schema() -> None:
    """Test with missing inputSchema."""
    tool = {}
    args = build_arguments(tool, "test task")
    assert args == {"task": "test task"}


def test_build_arguments_no_properties() -> None:
    """Test with inputSchema but no properties."""
    tool = {"inputSchema": {}}
    args = build_arguments(tool, "test task")
    assert args == {"task": "test task"}


def test_build_arguments_first_required_non_string_skipped() -> None:
    """Test that non-string required params are skipped."""
    tool = {
        "inputSchema": {
            "properties": {
                "count": {"type": "number"},
                "data": {"type": "object"},
            },
            "required": ["count", "data"],
        }
    }
    args = build_arguments(tool, "test")
    # Should fallback to "task" since first required is not string
    assert args == {"task": "test"}


def test_build_arguments_no_type_treated_as_string() -> None:
    """Test that params without type are treated as strings."""
    tool = {
        "inputSchema": {
            "properties": {"field": {}},  # No type specified
            "required": ["field"],
        }
    }
    args = build_arguments(tool, "test")
    assert args == {"field": "test"}


def test_build_arguments_text_type_accepted() -> None:
    """Test that 'text' type is accepted as string-like."""
    tool = {
        "inputSchema": {
            "properties": {"content": {"type": "text"}},
            "required": ["content"],
        }
    }
    args = build_arguments(tool, "test content")
    assert args == {"content": "test content"}


def test_build_arguments_empty_required_list() -> None:
    """Test with empty required list."""
    tool = {
        "inputSchema": {
            "properties": {"other": {"type": "string"}},
            "required": [],
        }
    }
    args = build_arguments(tool, "test")
    assert args == {"task": "test"}


def test_build_arguments_required_param_in_task_names() -> None:
    """Test that common task param names are preferred over other required params."""
    tool = {
        "inputSchema": {
            "properties": {
                "message": {"type": "string"},
                "other": {"type": "string"},
            },
            "required": ["other"],
        }
    }
    # "message" is a common task param name, so it should be used first
    args = build_arguments(tool, "hello")
    assert args == {"message": "hello"}
