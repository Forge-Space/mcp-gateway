"""Tests for MCP Streamable HTTP endpoint."""

import asyncio
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tool_router.api.streamable_http import _sessions, router


@pytest.fixture(autouse=True)
def _clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def app():
    from fastapi import FastAPI

    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestSessionManagement:
    def test_creates_session_on_first_request(self, client):
        with patch(
            "tool_router.api.streamable_http.RPC_METHOD_HANDLERS",
            {"tools/list": lambda p, c: {"tools": []}},
        ):
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            )
        assert resp.status_code == 200
        assert "mcp-session-id" in resp.headers
        session_id = resp.headers["mcp-session-id"]
        assert session_id in _sessions

    def test_reuses_existing_session(self, client):
        _sessions["existing-session"] = {
            "created": 0,
            "last_seen": 0,
        }
        with patch(
            "tool_router.api.streamable_http.RPC_METHOD_HANDLERS",
            {"tools/list": lambda p, c: {"tools": []}},
        ):
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={"Mcp-Session-Id": "existing-session"},
            )
        assert resp.status_code == 200
        assert _sessions["existing-session"]["last_seen"] > 0

    def test_rejects_unknown_session(self, client):
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={"Mcp-Session-Id": "nonexistent"},
        )
        assert resp.status_code == 404

    def test_delete_session(self, client):
        _sessions["to-delete"] = {"created": 0, "last_seen": 0}
        resp = client.delete("/mcp", headers={"Mcp-Session-Id": "to-delete"})
        assert resp.status_code == 204
        assert "to-delete" not in _sessions

    def test_delete_unknown_session(self, client):
        resp = client.delete("/mcp", headers={"Mcp-Session-Id": "nope"})
        assert resp.status_code == 404


class TestJsonRpcRouting:
    def test_method_not_found(self, client):
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "unknown/method", "id": 1},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["error"]["code"] == -32601

    def test_tools_list(self, client):
        with patch(
            "tool_router.api.streamable_http.RPC_METHOD_HANDLERS",
            {"tools/list": lambda p, c: {"tools": [{"name": "test"}]}},
        ):
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["result"]["tools"] == [{"name": "test"}]
        assert body["id"] == 1

    def test_handler_exception(self, client):
        def boom(params, ctx):
            msg = "kaboom"
            raise RuntimeError(msg)

        with patch(
            "tool_router.api.streamable_http.RPC_METHOD_HANDLERS",
            {"tools/list": boom},
        ):
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["error"]["code"] == -32603


class TestStreamUpgrade:
    def test_sse_upgrade_for_tools_call(self, client):
        async def mock_stream(name, args, ctx):
            yield 'data: {"type": "start"}\n\n'
            yield 'data: {"type": "complete", "code": "hello"}\n\n'

        with patch(
            "tool_router.api.streamable_http._stream_tool_call",
            mock_stream,
        ):
            resp = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "generate_ui",
                        "arguments": {"task": "button"},
                    },
                    "id": 1,
                },
                headers={"Accept": "text/event-stream"},
            )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_missing_tool_name_returns_400(self, client):
        resp = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"arguments": {}},
                "id": 1,
            },
            headers={"Accept": "text/event-stream"},
        )
        assert resp.status_code == 400


class TestSessionPruning:
    def test_prunes_old_sessions(self):
        from tool_router.api.streamable_http import (
            _MAX_SESSIONS,
            _prune_sessions,
        )

        for i in range(_MAX_SESSIONS + 50):
            _sessions[f"s{i}"] = {"created": i, "last_seen": i}

        asyncio.run(_prune_sessions())
        assert len(_sessions) == _MAX_SESSIONS
