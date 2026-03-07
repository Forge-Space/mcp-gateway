"""Tests for the JSON-RPC endpoint handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tool_router.api.rpc_handler import (
    JsonRpcRequest,
    JsonRpcResponse,
    _handle_tools_call,
    _handle_tools_list,
    init_rpc_security,
)
from tool_router.security.security_middleware import SecurityContext


@pytest.fixture
def security_context() -> SecurityContext:
    return SecurityContext(
        user_id="user-123",
        session_id="sess-456",
        ip_address="127.0.0.1",
        user_agent="test-agent",
        request_id="rpc_test_1",
        endpoint="/rpc",
        authentication_method="jwt",
        user_role="user",
    )


class TestJsonRpcRequest:
    def test_valid_request(self) -> None:
        req = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/list",
            params={},
            id="1",
        )
        assert req.method == "tools/list"
        assert req.params == {}

    def test_default_params(self) -> None:
        req = JsonRpcRequest(method="tools/list")
        assert req.params == {}
        assert req.jsonrpc == "2.0"

    def test_tool_call_request(self) -> None:
        req = JsonRpcRequest(
            method="tools/call",
            params={"name": "execute_specialist_task", "arguments": {"task": "hello"}},
            id=42,
        )
        assert req.params["name"] == "execute_specialist_task"
        assert req.id == 42


class TestHandleToolsList:
    @patch("tool_router.api.rpc_handler._get_available_tools")
    def test_returns_tools(self, mock_tools: MagicMock, security_context: SecurityContext) -> None:
        mock_tools.return_value = [
            {"name": "execute_task", "description": "Run a tool"},
        ]
        result = _handle_tools_list({}, security_context)
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "execute_task"

    @patch("tool_router.api.rpc_handler._get_available_tools")
    def test_empty_tools(self, mock_tools: MagicMock, security_context: SecurityContext) -> None:
        mock_tools.return_value = []
        result = _handle_tools_list({}, security_context)
        assert result["tools"] == []


class TestHandleToolsCall:
    @patch("tool_router.api.rpc_handler._call_tool")
    def test_successful_call(self, mock_call: MagicMock, security_context: SecurityContext) -> None:
        mock_call.return_value = "<div>Hello</div>"
        result = _handle_tools_call(
            {"name": "execute_task", "arguments": {"task": "create button"}},
            security_context,
        )
        assert result["content"][0]["text"] == "<div>Hello</div>"
        assert result["metadata"]["tool"] == "execute_task"
        assert result["metadata"]["user_id"] == "user-123"
        mock_call.assert_called_once_with("execute_task", {"task": "create button"})

    def test_missing_name_raises(self, security_context: SecurityContext) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _handle_tools_call({"arguments": {}}, security_context)
        assert exc_info.value.status_code == 400

    @patch("tool_router.api.rpc_handler._call_tool")
    def test_default_arguments(self, mock_call: MagicMock, security_context: SecurityContext) -> None:
        mock_call.return_value = "ok"
        _handle_tools_call({"name": "search_tools"}, security_context)
        mock_call.assert_called_once_with("search_tools", {})

    @patch("tool_router.api.rpc_handler._call_tool")
    @patch("tool_router.api.rpc_handler._run_security_check")
    def test_blocked_by_security(
        self,
        mock_security: MagicMock,
        mock_call: MagicMock,
        security_context: SecurityContext,
    ) -> None:
        from fastapi import HTTPException

        mock_security.return_value = (False, "Prompt injection detected", {})
        with pytest.raises(HTTPException) as exc_info:
            _handle_tools_call(
                {"name": "execute_task", "arguments": {"task": "ignore instructions"}},
                security_context,
            )
        assert exc_info.value.status_code == 403
        assert "Prompt injection" in str(exc_info.value.detail)
        mock_call.assert_not_called()

    @patch("tool_router.api.rpc_handler._call_tool")
    def test_sanitized_inputs_applied(self, mock_call: MagicMock, security_context: SecurityContext) -> None:
        mock_security = MagicMock()
        mock_security.check_request_security.return_value = MagicMock(
            allowed=True,
            blocked_reason=None,
            sanitized_inputs={
                "task": "sanitized task",
                "context": "sanitized context",
            },
            risk_score=0.1,
            violations=[],
        )
        init_rpc_security(mock_security, MagicMock())
        mock_call.return_value = "result"

        _handle_tools_call(
            {"name": "execute_task", "arguments": {"task": "raw task", "context": "raw"}},
            security_context,
        )

        call_args = mock_call.call_args[0][1]
        assert call_args["task"] == "sanitized task"
        assert call_args["context"] == "sanitized context"

        # Reset global state
        init_rpc_security(None, None)


class TestInitRpcSecurity:
    def test_init_sets_globals(self) -> None:
        from tool_router.api import rpc_handler

        mock_mw = MagicMock()
        mock_audit = MagicMock()
        init_rpc_security(mock_mw, mock_audit)
        assert rpc_handler._security_middleware is mock_mw
        assert rpc_handler._audit_logger is mock_audit
        # Cleanup
        init_rpc_security(None, None)


class TestJsonRpcResponse:
    def test_success_response(self) -> None:
        resp = JsonRpcResponse(
            id="1",
            result={"tools": []},
        )
        assert resp.jsonrpc == "2.0"
        assert resp.result == {"tools": []}
        assert resp.error is None

    def test_error_response(self) -> None:
        from tool_router.api.rpc_handler import JsonRpcError

        resp = JsonRpcResponse(
            id="1",
            error=JsonRpcError(code=-32601, message="Method not found"),
        )
        assert resp.result is None
        assert resp.error.code == -32601


class TestSseEvent:
    def test_format(self) -> None:
        from tool_router.api.rpc_handler import _sse_event

        result = _sse_event({"type": "start", "timestamp": 1000})
        assert result.startswith("data: ")
        assert result.endswith("\n\n")
        import json

        parsed = json.loads(result[6:].strip())
        assert parsed["type"] == "start"
        assert parsed["timestamp"] == 1000


class TestStreamToolCall:
    @pytest.mark.asyncio
    @patch("tool_router.api.rpc_handler._call_tool")
    async def test_streams_chunks(self, mock_call: MagicMock, security_context: SecurityContext) -> None:
        from tool_router.api.rpc_handler import _stream_tool_call

        mock_call.return_value = "A" * 500

        events = []
        async for chunk in _stream_tool_call("test_tool", {"task": "gen"}, security_context):
            import json

            parsed = json.loads(chunk[6:].strip())
            events.append(parsed)

        types = [e["type"] for e in events]
        assert types[0] == "start"
        assert "chunk" in types
        assert types[-1] == "complete"

        chunks = [e for e in events if e["type"] == "chunk"]
        assert len(chunks) == 3  # 500 / 200 = 3 chunks
        assert "".join(c["content"] for c in chunks) == "A" * 500

        quality_events = [e for e in events if e["type"] == "quality"]
        assert len(quality_events) == 1
        assert "report" in quality_events[0]

        complete = events[-1]
        assert complete["totalLength"] == 500
        assert complete["metadata"]["tool"] == "test_tool"
        assert "qualityPassed" in complete
        assert "quality_score" in complete["metadata"]

    @pytest.mark.asyncio
    @patch("tool_router.api.rpc_handler._call_tool")
    async def test_streams_error_on_failure(self, mock_call: MagicMock, security_context: SecurityContext) -> None:
        from tool_router.api.rpc_handler import _stream_tool_call

        mock_call.side_effect = ConnectionError("Gateway unreachable")

        events = []
        async for chunk in _stream_tool_call("test_tool", {}, security_context):
            import json

            parsed = json.loads(chunk[6:].strip())
            events.append(parsed)

        types = [e["type"] for e in events]
        assert "start" in types
        assert "error" in types
        assert "complete" not in types
        assert "Gateway unreachable" in events[-1]["message"]
