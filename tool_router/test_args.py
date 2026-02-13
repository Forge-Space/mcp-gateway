from __future__ import annotations

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
