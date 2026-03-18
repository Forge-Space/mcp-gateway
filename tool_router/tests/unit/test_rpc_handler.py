"""Tests for the JSON-RPC endpoint handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.rpc_handler import (
    JsonRpcRequest,
    JsonRpcResponse,
    _get_rate_limit_headers,
    _handle_tools_call,
    _handle_tools_list,
    init_rpc_security,
)
from tool_router.api.rpc_handler import (
    router as rpc_router,
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


class TestGetRateLimitHeaders:
    def test_returns_empty_when_no_middleware(self, security_context: SecurityContext) -> None:
        init_rpc_security(None, None)
        headers = _get_rate_limit_headers(security_context)
        assert headers == {}

    def test_returns_standard_headers(self, security_context: SecurityContext) -> None:
        mock_mw = MagicMock()
        mock_mw._get_rate_limit_identifier.return_value = "user:user-123"
        mock_config = MagicMock()
        mock_config.requests_per_minute = 60
        mock_mw._get_rate_limit_config.return_value = mock_config
        mock_mw.rate_limiter.get_usage_stats.return_value = {
            "minute": {"count": 5, "window_end": 1700000060},
        }
        init_rpc_security(mock_mw, MagicMock())

        headers = _get_rate_limit_headers(security_context)

        assert headers["X-RateLimit-Limit"] == "60"
        assert headers["X-RateLimit-Remaining"] == "55"
        assert headers["X-RateLimit-Reset"] == "1700000060"
        assert "Retry-After" not in headers

        init_rpc_security(None, None)

    def test_includes_retry_after_on_penalty(self, security_context: SecurityContext) -> None:
        import time

        mock_mw = MagicMock()
        mock_mw._get_rate_limit_identifier.return_value = "user:user-123"
        mock_config = MagicMock()
        mock_config.requests_per_minute = 60
        mock_mw._get_rate_limit_config.return_value = mock_config
        penalty_end = int(time.time()) + 120
        mock_mw.rate_limiter.get_usage_stats.return_value = {
            "minute": {"count": 60, "window_end": 1700000060},
            "penalty_active": True,
            "penalty_end": penalty_end,
        }
        init_rpc_security(mock_mw, MagicMock())

        headers = _get_rate_limit_headers(security_context)

        assert headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in headers
        assert int(headers["Retry-After"]) > 0

        init_rpc_security(None, None)

    def test_remaining_never_negative(self, security_context: SecurityContext) -> None:
        mock_mw = MagicMock()
        mock_mw._get_rate_limit_identifier.return_value = "user:user-123"
        mock_config = MagicMock()
        mock_config.requests_per_minute = 10
        mock_mw._get_rate_limit_config.return_value = mock_config
        mock_mw.rate_limiter.get_usage_stats.return_value = {
            "minute": {"count": 15, "window_end": 1700000060},
        }
        init_rpc_security(mock_mw, MagicMock())

        headers = _get_rate_limit_headers(security_context)
        assert headers["X-RateLimit-Remaining"] == "0"

        init_rpc_security(None, None)


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
        assert "security_spoke" in quality_events[0]["report"]
        assert quality_events[0]["report"]["security_spoke"]["version"] == "v1"
        assert quality_events[0]["report"]["security_spoke"]["dast"]["status"] == "not_executed"

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
        assert events[-1]["message"] == "Tool execution failed"


# ---------------------------------------------------------------------------
# Tests: json_rpc_endpoint HTTP handler (lines 303-338)
# ---------------------------------------------------------------------------


class TestJsonRpcHttpEndpoint:
    """Test the JSON-RPC HTTP endpoint via TestClient."""

    def _make_app(self, security_context: SecurityContext) -> FastAPI:
        from tool_router.api.dependencies import get_security_context

        app = FastAPI()
        app.include_router(rpc_router)

        def _mock_ctx() -> SecurityContext:
            return security_context

        app.dependency_overrides[get_security_context] = _mock_ctx
        return app

    def _ctx(self) -> SecurityContext:
        return SecurityContext(
            user_id="u1",
            session_id="s1",
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-1",
            endpoint="/rpc",
            authentication_method="jwt",
            user_role="developer",
        )

    def test_tools_list_via_http(self) -> None:
        with patch("tool_router.api.rpc_handler._get_available_tools", return_value=[]):
            app = self._make_app(self._ctx())
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert "tools" in data["result"]

    def test_method_not_found_via_http(self) -> None:
        app = self._make_app(self._ctx())
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "unknown/method", "id": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"]["code"] == -32601

    def test_tools_call_http_400_returns_rpc_error(self) -> None:
        """HTTPException 400 from handler → JSON-RPC error -32602."""
        from fastapi import HTTPException

        def _raise(*_a, **_kw):
            raise HTTPException(status_code=400, detail="bad params")

        # Patch at the RPC_METHOD_HANDLERS level
        from tool_router.api.rpc_handler import RPC_METHOD_HANDLERS

        original = RPC_METHOD_HANDLERS.get("tools/call")
        try:
            RPC_METHOD_HANDLERS["tools/call"] = _raise
            app = self._make_app(self._ctx())
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "tools/call", "id": 3, "params": {}})
        finally:
            if original is not None:
                RPC_METHOD_HANDLERS["tools/call"] = original
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is not None
        assert data["error"]["code"] == -32602

    def test_generic_exception_returns_internal_error(self) -> None:
        def _raise(*_a, **_kw):
            raise RuntimeError("unexpected failure")

        # Patch the dispatch table directly to guarantee the exception fires
        with patch(
            "tool_router.api.rpc_handler.RPC_METHOD_HANDLERS",
            {"tools/list": _raise},
        ):
            with patch("tool_router.api.rpc_handler._get_available_tools", return_value=[]):
                app = self._make_app(self._ctx())
                client = TestClient(app, raise_server_exceptions=False)
                resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "tools/list", "id": 4})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 4
        assert data["error"] is not None
        assert data["error"]["code"] == -32603

    def test_endpoint_responds_with_200(self) -> None:
        """Verify the /rpc endpoint returns 200 for a valid request."""
        with patch("tool_router.api.rpc_handler._get_available_tools", return_value=[]):
            app = self._make_app(self._ctx())
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "tools/list", "id": 5})
        assert resp.status_code == 200
        # Rate limit headers are only present when security middleware is initialised
        # (not in unit test context — that's tested in TestGetRateLimitHeaders)

    def test_register_tool_dispatch(self) -> None:
        from tool_router.api.rpc_handler import TOOL_DISPATCH, register_tool_dispatch

        original = dict(TOOL_DISPATCH)
        try:
            register_tool_dispatch({"my_tool": lambda: "ok"})
            assert "my_tool" in TOOL_DISPATCH
        finally:
            TOOL_DISPATCH.clear()
            TOOL_DISPATCH.update(original)

    def test_get_available_tools_returns_list(self) -> None:
        from tool_router.api.rpc_handler import _get_available_tools

        with patch("tool_router.gateway.client.get_tools", return_value=[{"name": "t"}]):
            result = _get_available_tools()
        assert isinstance(result, list)

    def test_get_available_tools_handles_connection_error(self) -> None:
        from tool_router.api.rpc_handler import _get_available_tools

        with patch("tool_router.gateway.client.get_tools", side_effect=ConnectionError("down")):
            result = _get_available_tools()
        assert result == []

    def test_call_tool_proxies_to_client(self) -> None:
        from tool_router.api.rpc_handler import _call_tool

        with patch("tool_router.gateway.client.call_tool", return_value="result"):
            result = _call_tool("test", {})
        assert result == "result"


class TestHandleToolsListWithAuditLogger:
    """Cover line 190: _audit_logger.log_request_received in _handle_tools_list."""

    @patch("tool_router.api.rpc_handler._get_available_tools")
    def test_audit_logger_called_when_set(self, mock_tools: MagicMock, security_context: SecurityContext) -> None:
        mock_tools.return_value = []
        mock_audit = MagicMock()
        init_rpc_security(None, mock_audit)
        try:
            _handle_tools_list({}, security_context)
            mock_audit.log_request_received.assert_called_once()
        finally:
            init_rpc_security(None, None)

    @patch("tool_router.api.rpc_handler._get_available_tools")
    def test_no_audit_logger_does_not_fail(self, mock_tools: MagicMock, security_context: SecurityContext) -> None:
        mock_tools.return_value = []
        init_rpc_security(None, None)
        result = _handle_tools_list({}, security_context)
        assert "tools" in result


class TestHandleToolsCallAuditPaths:
    """Cover lines 240 (audit log when blocked) and audited tools/call path."""

    @patch("tool_router.api.rpc_handler._call_tool")
    @patch("tool_router.api.rpc_handler._run_security_check")
    def test_audit_logger_called_on_block(
        self,
        mock_security: MagicMock,
        mock_call: MagicMock,
        security_context: SecurityContext,
    ) -> None:
        from fastapi import HTTPException

        mock_security.return_value = (False, "Injection detected", {})
        mock_audit = MagicMock()
        init_rpc_security(MagicMock(), mock_audit)
        try:
            with pytest.raises(HTTPException) as exc_info:
                _handle_tools_call(
                    {"name": "execute_task", "arguments": {"task": "bad"}},
                    security_context,
                )
            assert exc_info.value.status_code == 403
            mock_audit.log_request_blocked.assert_called_once()
        finally:
            init_rpc_security(None, None)

    @patch("tool_router.api.rpc_handler._call_tool")
    def test_audit_logger_called_on_successful_tools_call(
        self, mock_call: MagicMock, security_context: SecurityContext
    ) -> None:
        mock_call.return_value = "ok"
        mock_audit = MagicMock()
        init_rpc_security(None, mock_audit)
        try:
            result = _handle_tools_call(
                {"name": "execute_task", "arguments": {"task": "build button"}},
                security_context,
            )
            assert result["content"][0]["text"] == "ok"
            mock_audit.log_request_received.assert_called_once()
        finally:
            init_rpc_security(None, None)


class TestJsonRpcStreamEndpoint:
    """Cover lines 441-519: json_rpc_stream_endpoint."""

    def _make_app(self, security_context: SecurityContext) -> FastAPI:
        from tool_router.api.dependencies import get_security_context

        app = FastAPI()
        app.include_router(rpc_router)

        def _mock_ctx() -> SecurityContext:
            return security_context

        app.dependency_overrides[get_security_context] = _mock_ctx
        return app

    def _ctx(self) -> SecurityContext:
        return SecurityContext(
            user_id="u1",
            session_id="s1",
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-stream",
            endpoint="/rpc/stream",
            authentication_method="jwt",
            user_role="developer",
        )

    @patch("tool_router.api.rpc_handler._call_tool")
    def test_stream_tools_call_returns_event_stream(self, mock_call: MagicMock) -> None:
        mock_call.return_value = "stream result"
        app = self._make_app(self._ctx())
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/rpc/stream",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "execute_task", "arguments": {"task": "hello"}},
                "id": 1,
            },
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_stream_wrong_method_returns_error_stream(self) -> None:
        app = self._make_app(self._ctx())
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/rpc/stream",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            },
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        content = resp.text
        assert "error" in content

    def test_stream_missing_name_returns_400(self) -> None:
        app = self._make_app(self._ctx())
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/rpc/stream",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"arguments": {}},
                "id": 3,
            },
        )
        assert resp.status_code == 400

    @patch("tool_router.api.rpc_handler._call_tool")
    @patch("tool_router.api.rpc_handler._run_security_check")
    def test_stream_blocked_by_security_returns_403(
        self,
        mock_security: MagicMock,
        mock_call: MagicMock,
    ) -> None:
        mock_security.return_value = (False, "Blocked for testing", {})
        app = self._make_app(self._ctx())
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/rpc/stream",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "execute_task", "arguments": {"task": "bad input"}},
                "id": 4,
            },
        )
        assert resp.status_code == 403

    @patch("tool_router.api.rpc_handler._call_tool")
    @patch("tool_router.api.rpc_handler._run_security_check")
    def test_stream_blocked_logs_to_audit(
        self,
        mock_security: MagicMock,
        mock_call: MagicMock,
    ) -> None:

        mock_security.return_value = (False, "Injection", {})
        mock_audit = MagicMock()
        init_rpc_security(MagicMock(), mock_audit)
        try:
            app = self._make_app(self._ctx())
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/rpc/stream",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "execute_task", "arguments": {"task": "bad"}},
                    "id": 5,
                },
            )
            assert resp.status_code == 403
            mock_audit.log_request_blocked.assert_called_once()
        finally:
            init_rpc_security(None, None)

    @patch("tool_router.api.rpc_handler._call_tool")
    def test_stream_audit_logger_called_on_success(self, mock_call: MagicMock) -> None:
        mock_call.return_value = "ok"
        mock_audit = MagicMock()
        init_rpc_security(None, mock_audit)
        try:
            app = self._make_app(self._ctx())
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/rpc/stream",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "execute_task", "arguments": {"task": "hello"}},
                    "id": 6,
                },
            )
            assert resp.status_code == 200
            mock_audit.log_request_received.assert_called_once()
        finally:
            init_rpc_security(None, None)


class TestRpcHandlerCoverageGaps:
    def _make_app(self, security_context: SecurityContext) -> FastAPI:
        from tool_router.api.dependencies import get_security_context

        app = FastAPI()
        app.include_router(rpc_router)

        def _mock_ctx() -> SecurityContext:
            return security_context

        app.dependency_overrides[get_security_context] = _mock_ctx
        return app

    def _ctx(self, endpoint: str = "/rpc") -> SecurityContext:
        return SecurityContext(
            user_id="u-coverage",
            session_id="s-coverage",
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="req-coverage",
            endpoint=endpoint,
            authentication_method="jwt",
            user_role="developer",
        )

    def test_run_security_check_returns_blocked_tuple(self) -> None:
        from tool_router.api.rpc_handler import _run_security_check

        mock_mw = MagicMock()
        mock_mw.check_request_security.return_value = MagicMock(
            allowed=False,
            blocked_reason="blocked",
            sanitized_inputs={"task": "clean task", "context": "clean context"},
        )
        init_rpc_security(mock_mw, MagicMock())
        try:
            allowed, reason, sanitized = _run_security_check(
                self._ctx(),
                "raw task",
                "specialist",
                "raw context",
                "",
            )
            assert allowed is False
            assert reason == "blocked"
            assert sanitized["task"] == "clean task"
        finally:
            init_rpc_security(None, None)

    def test_http_endpoint_propagates_rate_limit_headers(self) -> None:
        app = self._make_app(self._ctx(endpoint="/rpc"))
        client = TestClient(app, raise_server_exceptions=False)

        with patch("tool_router.api.rpc_handler._get_available_tools", return_value=[]):
            with patch(
                "tool_router.api.rpc_handler._get_rate_limit_headers",
                return_value={"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "59"},
            ):
                resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "tools/list", "id": 77})

        assert resp.status_code == 200
        assert resp.headers["X-RateLimit-Limit"] == "60"
        assert resp.headers["X-RateLimit-Remaining"] == "59"

    @patch("tool_router.api.rpc_handler._run_security_check")
    @patch("tool_router.api.rpc_handler._call_tool")
    def test_stream_endpoint_applies_sanitized_context(
        self,
        mock_call: MagicMock,
        mock_security: MagicMock,
    ) -> None:
        mock_call.return_value = "stream result"
        mock_security.return_value = (
            True,
            None,
            {"task": "sanitized task", "context": "sanitized context"},
        )

        app = self._make_app(self._ctx(endpoint="/rpc/stream"))
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post(
            "/rpc/stream",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "execute_task",
                    "arguments": {"task": "raw task", "context": "raw context"},
                },
                "id": 101,
            },
        )

        assert resp.status_code == 200
        _ = resp.text
        called_args = mock_call.call_args[0][1]
        assert called_args["task"] == "sanitized task"
        assert called_args["context"] == "sanitized context"
