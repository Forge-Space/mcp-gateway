from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from tool_router.gateway_client import call_tool, get_tools


def test_get_tools_raises_when_gateway_jwt_unset() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GATEWAY_JWT"):
            get_tools()


def test_get_tools_returns_list_from_list_response() -> None:
    data = [{"name": "t1", "description": "d1"}]
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("urllib.request.urlopen", return_value=resp):
            result = get_tools()
    assert result == data


def test_get_tools_returns_tools_from_wrapped_response() -> None:
    data = {"tools": [{"name": "t1"}]}
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("urllib.request.urlopen", return_value=resp):
            result = get_tools()
    assert result == [{"name": "t1"}]


def test_get_tools_returns_empty_for_unknown_shape() -> None:
    resp = MagicMock()
    resp.read.return_value = b"{}"
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("urllib.request.urlopen", return_value=resp):
            result = get_tools()
    assert result == []


def test_call_tool_raises_when_gateway_jwt_unset() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GATEWAY_JWT"):
            call_tool("foo", {})


def test_call_tool_returns_error_message_on_jsonrpc_error() -> None:
    out = {"jsonrpc": "2.0", "id": 1, "error": {"message": "Tool not found"}}
    resp = MagicMock()
    resp.read.return_value = json.dumps(out).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("urllib.request.urlopen", return_value=resp):
            result = call_tool("bad_tool", {})
    assert "Gateway error" in result
    assert "Tool not found" in result


def test_call_tool_returns_text_content() -> None:
    out = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"content": [{"type": "text", "text": "Hello"}]},
    }
    resp = MagicMock()
    resp.read.return_value = json.dumps(out).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("urllib.request.urlopen", return_value=resp):
            result = call_tool("greet", {})
    assert result == "Hello"
