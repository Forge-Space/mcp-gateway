"""Tests for OTel spans added to gateway client, scoring, and security middleware.

All tests run in no-op mode (OTel absent) — SpanContext returns a no-op span
that accepts set_attribute() calls without error.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tool(name: str, description: str = "") -> dict[str, Any]:
    return {"name": name, "description": description}


def _make_gateway_config(url: str = "http://gateway:8080") -> Any:
    from tool_router.core.config import GatewayConfig

    return GatewayConfig(url=url, jwt="test-jwt")


# ---------------------------------------------------------------------------
# Gateway client spans
# ---------------------------------------------------------------------------


class TestGatewayClientSpans:
    """Tests for OTel spans in HTTPGatewayClient."""

    def _make_client(self, url: str = "http://gateway:8080") -> Any:
        from tool_router.gateway.client import HTTPGatewayClient

        config = _make_gateway_config(url)
        return HTTPGatewayClient(config)

    def test_get_tools_success_span_no_error(self) -> None:
        """get_tools() completes without raising when request succeeds."""
        client = self._make_client()
        tools_response = {"tools": [_make_tool("search"), _make_tool("read")]}
        with patch.object(client, "_make_request", return_value=tools_response):
            result = client.get_tools()
        assert len(result) == 2

    def test_get_tools_returns_list_response(self) -> None:
        """get_tools() handles bare list response."""
        client = self._make_client()
        tools_list = [_make_tool("tool_a"), _make_tool("tool_b"), _make_tool("tool_c")]
        with patch.object(client, "_make_request", return_value=tools_list):
            result = client.get_tools()
        assert len(result) == 3

    def test_get_tools_empty_response(self) -> None:
        """get_tools() returns [] for empty dict response."""
        client = self._make_client()
        with patch.object(client, "_make_request", return_value={}):
            result = client.get_tools()
        assert result == []

    def test_get_tools_connection_error_returns_empty(self) -> None:
        """get_tools() returns [] on ConnectionError (circuit open / network)."""
        client = self._make_client()
        with patch.object(client, "_make_request", side_effect=ConnectionError("network down")):
            result = client.get_tools()
        assert result == []

    def test_get_tools_value_error_reraises(self) -> None:
        """get_tools() re-raises ValueError from HTTP 4xx errors."""
        client = self._make_client()
        with patch.object(client, "_make_request", side_effect=ValueError("Gateway HTTP error 401: Unauthorized")):
            with pytest.raises(ValueError, match="Failed to fetch tools"):
                client.get_tools()

    def test_get_tools_invalid_json_returns_empty(self) -> None:
        """get_tools() returns [] on invalid JSON response."""
        client = self._make_client()
        with patch.object(client, "_make_request", side_effect=ValueError("Invalid JSON response")):
            result = client.get_tools()
        assert result == []

    def test_call_tool_success_returns_text(self) -> None:
        """call_tool() returns text content on success."""
        client = self._make_client()
        rpc_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": "hello world"}]},
        }
        with patch.object(client, "_make_request", return_value=rpc_response):
            result = client.call_tool("search", {"query": "test"})
        assert result == "hello world"

    def test_call_tool_multiple_content_items(self) -> None:
        """call_tool() joins multiple text content items."""
        client = self._make_client()
        rpc_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {"type": "text", "text": "line1"},
                    {"type": "text", "text": "line2"},
                ]
            },
        }
        with patch.object(client, "_make_request", return_value=rpc_response):
            result = client.call_tool("read", {"path": "/tmp/f"})
        assert result == "line1\nline2"

    def test_call_tool_connection_error_returns_error_string(self) -> None:
        """call_tool() returns error string on ConnectionError."""
        client = self._make_client()
        with patch.object(client, "_make_request", side_effect=ConnectionError("timeout")):
            result = client.call_tool("search", {})
        assert "Failed to call tool" in result

    def test_call_tool_gateway_error_in_response(self) -> None:
        """call_tool() returns error string when JSON-RPC response has error field."""
        client = self._make_client()
        rpc_response = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}
        with patch.object(client, "_make_request", return_value=rpc_response):
            result = client.call_tool("unknown_tool", {})
        assert "Gateway error" in result

    def test_call_tool_empty_content_returns_json(self) -> None:
        """call_tool() returns JSON-serialized result when content is empty."""
        client = self._make_client()
        rpc_response = {"jsonrpc": "2.0", "id": 1, "result": {"status": "ok"}}
        with patch.object(client, "_make_request", return_value=rpc_response):
            result = client.call_tool("ping", {})
        assert "status" in result


# ---------------------------------------------------------------------------
# Scoring matcher spans
# ---------------------------------------------------------------------------


class TestScoringMatcherSpans:
    """Tests for OTel spans in scoring/matcher.py."""

    def test_select_top_matching_tools_empty_returns_empty(self) -> None:
        """select_top_matching_tools() returns [] for empty tools list."""
        from tool_router.scoring.matcher import select_top_matching_tools

        result = select_top_matching_tools([], "search files", "", top_n=3)
        assert result == []

    def test_select_top_matching_tools_returns_best_match(self) -> None:
        """select_top_matching_tools() returns the most relevant tool."""
        from tool_router.scoring.matcher import select_top_matching_tools

        tools = [
            _make_tool("search_files", "search and find files"),
            _make_tool("send_email", "send email messages"),
        ]
        result = select_top_matching_tools(tools, "search files", "", top_n=1)
        assert len(result) == 1
        assert result[0]["name"] == "search_files"

    def test_select_top_matching_tools_top_n_respected(self) -> None:
        """select_top_matching_tools() respects top_n limit."""
        from tool_router.scoring.matcher import select_top_matching_tools

        tools = [_make_tool(f"search_tool_{i}", "search and find") for i in range(5)]
        result = select_top_matching_tools(tools, "search", "", top_n=2)
        assert len(result) <= 2

    def test_select_top_matching_tools_no_match_returns_empty(self) -> None:
        """select_top_matching_tools() returns [] when no tools score > 0."""
        from tool_router.scoring.matcher import select_top_matching_tools

        tools = [_make_tool("xyz_tool", "xyz operation")]
        result = select_top_matching_tools(tools, "aaabbbccc", "", top_n=1)
        assert result == []

    def test_select_top_matching_tools_hybrid_empty_returns_empty(self) -> None:
        """select_top_matching_tools_hybrid() returns [] for empty tools list."""
        from tool_router.scoring.matcher import select_top_matching_tools_hybrid

        result = select_top_matching_tools_hybrid([], "search", "", top_n=1)
        assert result == []

    def test_select_top_matching_tools_hybrid_no_ai_selector(self) -> None:
        """select_top_matching_tools_hybrid() works without AI selector."""
        from tool_router.scoring.matcher import select_top_matching_tools_hybrid

        tools = [
            _make_tool("search_files", "search and find files"),
            _make_tool("delete_file", "delete a file"),
        ]
        result = select_top_matching_tools_hybrid(tools, "search files", "", top_n=1, ai_selector=None)
        assert isinstance(result, list)

    def test_select_top_matching_tools_hybrid_with_ai_selector(self) -> None:
        """select_top_matching_tools_hybrid() uses AI selector when provided."""
        from tool_router.scoring.matcher import select_top_matching_tools_hybrid

        tools = [_make_tool("search_files", "search files"), _make_tool("read_file", "read file")]
        mock_ai = MagicMock()
        mock_ai.select_tool.return_value = {"tool_name": "search_files", "confidence": 0.9}

        result = select_top_matching_tools_hybrid(tools, "search files", "", top_n=1, ai_selector=mock_ai)
        assert isinstance(result, list)
        mock_ai.select_tool.assert_called_once()

    def test_select_top_matching_tools_hybrid_ai_failure_fallback(self) -> None:
        """select_top_matching_tools_hybrid() falls back to keyword when AI fails."""
        from tool_router.scoring.matcher import select_top_matching_tools_hybrid

        tools = [_make_tool("search_files", "search and find files")]
        mock_ai = MagicMock()
        mock_ai.select_tool.side_effect = RuntimeError("AI unavailable")

        result = select_top_matching_tools_hybrid(tools, "search files", "", top_n=1, ai_selector=mock_ai)
        assert isinstance(result, list)

    def test_select_top_matching_tools_enhanced_empty_returns_empty(self) -> None:
        """select_top_matching_tools_enhanced() returns [] for empty tools list."""
        from tool_router.scoring.matcher import select_top_matching_tools_enhanced

        result = select_top_matching_tools_enhanced([], "search", "", top_n=1)
        assert result == []

    def test_select_top_matching_tools_enhanced_no_ai(self) -> None:
        """select_top_matching_tools_enhanced() works without AI selector."""
        from tool_router.scoring.matcher import select_top_matching_tools_enhanced

        tools = [_make_tool("search_files", "search and find files")]
        result = select_top_matching_tools_enhanced(tools, "search files", "", top_n=1)
        assert isinstance(result, list)

    def test_select_top_matching_tools_enhanced_with_nlp_hints_false(self) -> None:
        """select_top_matching_tools_enhanced() works with use_nlp_hints=False."""
        from tool_router.scoring.matcher import select_top_matching_tools_enhanced

        tools = [_make_tool("search_files", "search and find files")]
        result = select_top_matching_tools_enhanced(tools, "search files", "", top_n=1, use_nlp_hints=False)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Security middleware spans
# ---------------------------------------------------------------------------


class TestSecurityMiddlewareSpans:
    """Tests for OTel spans in SecurityMiddleware.check_request_security."""

    def _make_middleware(self, enabled: bool = True, strict_mode: bool = False) -> Any:
        from tool_router.security.security_middleware import SecurityMiddleware

        config: dict[str, Any] = {
            "enabled": enabled,
            "strict_mode": strict_mode,
            "validation_level": "standard",
            "rate_limiting": {},
            "audit_logging": {"enable_console": False},
        }
        return SecurityMiddleware(config)

    def _make_context(self, user_id: str = "user123", endpoint: str = "/rpc") -> Any:
        from tool_router.security.security_middleware import SecurityContext

        return SecurityContext(user_id=user_id, endpoint=endpoint)

    def _call_check(self, middleware: Any, ctx: Any, task: str = "search files") -> Any:
        """Helper to call check_request_security with all required args."""
        return middleware.check_request_security(ctx, task, "general", "", "")

    def test_check_request_security_allowed(self) -> None:
        """check_request_security() returns allowed=True for clean request."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        result = self._call_check(middleware, ctx)
        assert result.allowed is True

    def test_check_request_security_disabled_returns_allowed(self) -> None:
        """check_request_security() returns allowed=True when middleware disabled."""
        middleware = self._make_middleware(enabled=False)
        ctx = self._make_context()
        result = self._call_check(middleware, ctx, "anything")
        assert result.allowed is True

    def test_check_request_security_result_has_risk_score(self) -> None:
        """check_request_security() result includes a risk_score float."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        result = self._call_check(middleware, ctx)
        assert isinstance(result.risk_score, float)
        assert 0.0 <= result.risk_score <= 1.0

    def test_check_request_security_result_has_violations_list(self) -> None:
        """check_request_security() result includes violations list."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        result = self._call_check(middleware, ctx)
        assert isinstance(result.violations, list)

    def test_check_request_security_result_has_sanitized_inputs(self) -> None:
        """check_request_security() result includes sanitized_inputs dict."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        result = self._call_check(middleware, ctx)
        assert isinstance(result.sanitized_inputs, dict)

    def test_check_request_security_no_user_id(self) -> None:
        """check_request_security() handles None user_id without error."""
        middleware = self._make_middleware()
        ctx = self._make_context(user_id=None)
        result = self._call_check(middleware, ctx)
        assert result is not None

    def test_check_request_security_empty_task(self) -> None:
        """check_request_security() handles empty task string."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        result = self._call_check(middleware, ctx, task="")
        assert result is not None

    def test_check_request_security_span_context_used(self) -> None:
        """check_request_security() uses SpanContext (no-op in test env)."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        with patch("tool_router.security.security_middleware.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span

            self._call_check(middleware, ctx)

        mock_span_cls.assert_called_once()
        call_kwargs = mock_span_cls.call_args
        assert call_kwargs[0][0] == "security.check_request"

    def test_check_request_security_span_sets_outcome(self) -> None:
        """check_request_security() sets security.outcome on span."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        with patch("tool_router.security.security_middleware.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span

            self._call_check(middleware, ctx)

        set_attr_calls = {call[0][0]: call[0][1] for call in mock_span.set_attribute.call_args_list}
        assert "security.outcome" in set_attr_calls
        assert set_attr_calls["security.outcome"] in ("allowed", "blocked")

    def test_check_request_security_span_sets_risk_score(self) -> None:
        """check_request_security() sets security.risk_score on span."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        with patch("tool_router.security.security_middleware.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span

            self._call_check(middleware, ctx)

        set_attr_calls = {call[0][0]: call[0][1] for call in mock_span.set_attribute.call_args_list}
        assert "security.risk_score" in set_attr_calls
        assert isinstance(set_attr_calls["security.risk_score"], float)

    def test_check_request_security_span_sets_blocked(self) -> None:
        """check_request_security() sets security.blocked on span."""
        middleware = self._make_middleware()
        ctx = self._make_context()
        with patch("tool_router.security.security_middleware.SpanContext") as mock_span_cls:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_span_cls.return_value = mock_span

            self._call_check(middleware, ctx)

        set_attr_calls = {call[0][0]: call[0][1] for call in mock_span.set_attribute.call_args_list}
        assert "security.blocked" in set_attr_calls
        assert isinstance(set_attr_calls["security.blocked"], bool)
