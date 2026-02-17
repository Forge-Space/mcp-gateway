from __future__ import annotations

from unittest.mock import patch

import pytest

from tool_router.gateway.client import HTTPGatewayClient, call_tool, get_tools


def test_get_tools_raises_when_gateway_jwt_unset() -> None:
    with patch.dict("os.environ", {}, clear=True), pytest.raises(ValueError, match="GATEWAY_JWT"):
        get_tools()


def test_get_tools_returns_list_from_list_response() -> None:
    data = [{"name": "t1", "description": "d1"}]

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("tool_router.gateway.client._validate_url_security"):
            with patch.object(HTTPGatewayClient, "_make_request", return_value=data):
                result = get_tools()
    assert result == data


def test_get_tools_returns_tools_from_wrapped_response() -> None:
    data = {"tools": [{"name": "t1"}]}

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("tool_router.gateway.client._validate_url_security"):
            with patch.object(HTTPGatewayClient, "_make_request", return_value=data):
                result = get_tools()
    assert result == [{"name": "t1"}]


def test_get_tools_returns_empty_for_unknown_shape() -> None:
    data = {}

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("tool_router.gateway.client._validate_url_security"):
            with patch.object(HTTPGatewayClient, "_make_request", return_value=data):
                result = get_tools()
    assert result == []


def test_call_tool_raises_when_gateway_jwt_unset() -> None:
    with patch.dict("os.environ", {}, clear=True), pytest.raises(ValueError, match="GATEWAY_JWT"):
        call_tool("foo", {})


def test_call_tool_returns_error_message_on_jsonrpc_error() -> None:
    out = {"jsonrpc": "2.0", "id": 1, "error": {"message": "Tool not found"}}

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("tool_router.gateway.client._validate_url_security"):
            with patch.object(HTTPGatewayClient, "_make_request", return_value=out):
                with pytest.raises(ValueError, match="Gateway error.*Tool not found"):
                    call_tool("bad_tool", {})


def test_call_tool_returns_text_content() -> None:
    out = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"content": [{"type": "text", "text": "Hello"}]},
    }

    with patch.dict("os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}):
        with patch("tool_router.gateway.client._validate_url_security"):
            with patch.object(HTTPGatewayClient, "_make_request", return_value=out):
                result = call_tool("greet", {})
    assert result == "Hello"
