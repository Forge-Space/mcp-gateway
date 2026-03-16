"""Tests for the transport module.

Covers:
- TransportMode enum values
- Transport abstract base class enforcement
- HttpTransport: start/stop/is_connected lifecycle
- HttpTransport: send success and error paths (retries, ValueError, ConnectionError)
- StdioTransport: constructor validation
- StdioTransport: start/stop/is_connected lifecycle
- StdioTransport: send success, not-started error, process-closed-stdout error
- __init__.py exports
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tool_router.transport import HttpTransport, StdioTransport, Transport, TransportMode


# ---------------------------------------------------------------------------
# TransportMode
# ---------------------------------------------------------------------------


def test_transport_mode_values() -> None:
    assert TransportMode.HTTP == "http"
    assert TransportMode.STDIO == "stdio"


def test_transport_mode_is_strenum() -> None:
    assert isinstance(TransportMode.HTTP, str)
    assert isinstance(TransportMode.STDIO, str)


# ---------------------------------------------------------------------------
# Transport ABC enforcement
# ---------------------------------------------------------------------------


def test_transport_abc_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        Transport()  # type: ignore[abstract]


def test_transport_subclass_must_implement_all_methods() -> None:
    class Incomplete(Transport):
        async def send(self, message: dict[str, Any]) -> dict[str, Any]:
            return {}

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_transport_complete_subclass_ok() -> None:
    class Complete(Transport):
        async def send(self, message: dict[str, Any]) -> dict[str, Any]:
            return {}

        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

        def is_connected(self) -> bool:
            return True

    inst = Complete()
    assert inst.is_connected() is True


# ---------------------------------------------------------------------------
# HttpTransport — lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_http_transport_start_sets_connected() -> None:
    t = HttpTransport(base_url="http://localhost:9999", jwt="tok")
    assert t.is_connected() is False
    await t.start()
    assert t.is_connected() is True


@pytest.mark.asyncio
async def test_http_transport_stop_clears_connected() -> None:
    t = HttpTransport(base_url="http://localhost:9999", jwt="tok")
    await t.start()
    await t.stop()
    assert t.is_connected() is False


def test_http_transport_strips_trailing_slash() -> None:
    t = HttpTransport(base_url="http://localhost:9999/", jwt="tok")
    assert t.base_url == "http://localhost:9999"


def test_http_transport_default_params() -> None:
    t = HttpTransport(base_url="http://localhost:9999", jwt="tok")
    assert t._timeout == 120.0
    assert t._max_retries == 3
    assert t._retry_delay == 1.0


def test_http_transport_custom_params() -> None:
    t = HttpTransport(
        base_url="http://localhost:9999",
        jwt="tok",
        timeout_ms=5000,
        max_retries=2,
        retry_delay_ms=500,
    )
    assert t._timeout == 5.0
    assert t._max_retries == 2
    assert t._retry_delay == 0.5


# ---------------------------------------------------------------------------
# HttpTransport — send success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_http_transport_send_returns_response() -> None:
    t = HttpTransport(base_url="http://localhost:9999", jwt="my-jwt", max_retries=1)
    expected = {"result": "ok", "id": 1}

    fake_resp = MagicMock()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    fake_resp.read.return_value = json.dumps(expected).encode()

    with patch("urllib.request.urlopen", return_value=fake_resp):
        result = await t.send({"method": "ping", "id": 1})

    assert result == expected


@pytest.mark.asyncio
async def test_http_transport_send_uses_jwt_header() -> None:
    t = HttpTransport(base_url="http://localhost:9999", jwt="secret-token", max_retries=1)
    captured: list[urllib.request.Request] = []

    fake_resp = MagicMock()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    fake_resp.read.return_value = b'{"ok": true}'

    def fake_urlopen(req: urllib.request.Request, timeout: float) -> MagicMock:
        captured.append(req)
        return fake_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        await t.send({"method": "ping"})

    assert captured[0].get_header("Authorization") == "Bearer secret-token"


@pytest.mark.asyncio
async def test_http_transport_send_posts_to_rpc_endpoint() -> None:
    t = HttpTransport(base_url="http://localhost:9999", jwt="tok", max_retries=1)
    captured: list[urllib.request.Request] = []

    fake_resp = MagicMock()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    fake_resp.read.return_value = b'{"ok": true}'

    def fake_urlopen(req: urllib.request.Request, timeout: float) -> MagicMock:
        captured.append(req)
        return fake_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        await t.send({"method": "ping"})

    assert captured[0].full_url == "http://localhost:9999/rpc"
    assert captured[0].method == "POST"


# ---------------------------------------------------------------------------
# HttpTransport — send error paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_http_transport_4xx_raises_value_error() -> None:
    t = HttpTransport(base_url="http://localhost:9999", jwt="tok", max_retries=1)

    err = urllib.error.HTTPError(
        url="http://localhost:9999/rpc",
        code=404,
        msg="Not Found",
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(b"not found"),
    )

    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(ValueError, match="HTTP 404"):
            await t.send({"method": "ping"})


@pytest.mark.asyncio
async def test_http_transport_5xx_retries_then_raises_value_error_on_last() -> None:
    """On last retry a 5xx raises ValueError (not ConnectionError) because
    the retry guard `attempt < max_retries - 1` is False on the last attempt."""
    t = HttpTransport(
        base_url="http://localhost:9999",
        jwt="tok",
        max_retries=2,
        retry_delay_ms=0,
    )

    err = urllib.error.HTTPError(
        url="http://localhost:9999/rpc",
        code=503,
        msg="Service Unavailable",
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(b"down"),
    )

    with patch("urllib.request.urlopen", side_effect=err):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(ValueError, match="HTTP 503"):
                await t.send({"method": "ping"})


@pytest.mark.asyncio
async def test_http_transport_url_error_raises_connection_error() -> None:
    t = HttpTransport(
        base_url="http://localhost:9999",
        jwt="tok",
        max_retries=2,
        retry_delay_ms=0,
    )

    err = urllib.error.URLError(reason="Connection refused")

    with patch("urllib.request.urlopen", side_effect=err):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(ConnectionError, match="Failed after 2 attempts"):
                await t.send({"method": "ping"})


# ---------------------------------------------------------------------------
# StdioTransport — constructor
# ---------------------------------------------------------------------------


def test_stdio_transport_empty_command_raises() -> None:
    with pytest.raises(ValueError, match="Command list must not be empty"):
        StdioTransport(command=[])


def test_stdio_transport_valid_constructor() -> None:
    t = StdioTransport(command=["echo", "hello"])
    assert t.command == ["echo", "hello"]
    assert t.env is None
    assert t.cwd is None
    assert t._process is None


def test_stdio_transport_with_env_and_cwd() -> None:
    t = StdioTransport(command=["cat"], env={"FOO": "bar"}, cwd="/tmp")
    assert t.env == {"FOO": "bar"}
    assert t.cwd == "/tmp"


# ---------------------------------------------------------------------------
# StdioTransport — lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stdio_transport_is_not_connected_before_start() -> None:
    t = StdioTransport(command=["cat"])
    assert t.is_connected() is False


@pytest.mark.asyncio
async def test_stdio_transport_start_creates_process() -> None:
    t = StdioTransport(command=["cat"])
    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.pid = 12345

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc):
        await t.start()

    assert t._process is mock_proc
    assert t.is_connected() is True


@pytest.mark.asyncio
async def test_stdio_transport_stop_terminates_process() -> None:
    t = StdioTransport(command=["cat"])
    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.terminate = MagicMock()
    mock_proc.wait = AsyncMock()

    t._process = mock_proc

    with patch("asyncio.wait_for", new_callable=AsyncMock):
        await t.stop()

    mock_proc.terminate.assert_called_once()
    assert t._process is None
    assert t.is_connected() is False


@pytest.mark.asyncio
async def test_stdio_transport_stop_noop_when_not_running() -> None:
    t = StdioTransport(command=["cat"])
    mock_proc = MagicMock()
    mock_proc.returncode = 0

    t._process = mock_proc
    await t.stop()
    assert t._process is None


@pytest.mark.asyncio
async def test_stdio_transport_stop_kills_on_timeout() -> None:
    t = StdioTransport(command=["cat"])
    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.terminate = MagicMock()
    mock_proc.kill = MagicMock()
    mock_proc.wait = AsyncMock()

    t._process = mock_proc

    async def _raise_timeout(*args: Any, **kwargs: Any) -> None:
        raise TimeoutError

    with patch("asyncio.wait_for", side_effect=_raise_timeout):
        await t.stop()

    mock_proc.kill.assert_called_once()


# ---------------------------------------------------------------------------
# StdioTransport — send
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stdio_transport_send_raises_when_not_started() -> None:
    t = StdioTransport(command=["cat"])
    with pytest.raises(ConnectionError, match="not started"):
        await t.send({"method": "ping"})


@pytest.mark.asyncio
async def test_stdio_transport_send_returns_parsed_response() -> None:
    t = StdioTransport(command=["cat"])

    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdin.write = MagicMock()
    mock_proc.stdin.drain = AsyncMock()
    mock_proc.stdout = MagicMock()

    response_line = json.dumps({"result": "pong", "id": 1}).encode() + b"\n"
    mock_proc.stdout.readline = AsyncMock(return_value=response_line)

    t._process = mock_proc

    async def _fake_wait_for(coro: Any, **_: Any) -> Any:
        return await coro

    with patch("asyncio.wait_for", side_effect=_fake_wait_for):
        result = await t.send({"method": "ping", "id": 1})

    assert result == {"result": "pong", "id": 1}


@pytest.mark.asyncio
async def test_stdio_transport_send_assigns_id_if_missing() -> None:
    t = StdioTransport(command=["cat"])

    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdin.drain = AsyncMock()
    mock_proc.stdout = MagicMock()

    sent_payloads: list[bytes] = []

    def capture_write(data: bytes) -> None:
        sent_payloads.append(data)

    mock_proc.stdin.write = capture_write
    response_line = json.dumps({"result": "ok", "id": 1}).encode() + b"\n"
    mock_proc.stdout.readline = AsyncMock(return_value=response_line)

    t._process = mock_proc

    async def _fake_wait_for(coro: Any, **_: Any) -> Any:
        return await coro

    with patch("asyncio.wait_for", side_effect=_fake_wait_for):
        await t.send({"method": "ping"})

    sent = json.loads(sent_payloads[0].decode().strip())
    assert "id" in sent
    assert sent["id"] == 1


@pytest.mark.asyncio
async def test_stdio_transport_send_raises_on_empty_line() -> None:
    t = StdioTransport(command=["cat"])

    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.stdin = MagicMock()
    mock_proc.stdin.write = MagicMock()
    mock_proc.stdin.drain = AsyncMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = AsyncMock(return_value=b"")

    t._process = mock_proc

    async def _fake_wait_for(coro: Any, **_: Any) -> Any:
        return await coro

    with patch("asyncio.wait_for", side_effect=_fake_wait_for):
        with pytest.raises(ConnectionError, match="closed stdout"):
            await t.send({"method": "ping"})


# ---------------------------------------------------------------------------
# __init__.py exports
# ---------------------------------------------------------------------------


def test_transport_module_exports() -> None:
    from tool_router.transport import HttpTransport as HttpTransportExport
    from tool_router.transport import StdioTransport as StdioTransportExport
    from tool_router.transport import Transport as TransportExport
    from tool_router.transport import TransportMode as TransportModeExport

    assert HttpTransportExport is HttpTransport
    assert StdioTransportExport is StdioTransport
    assert TransportModeExport is TransportMode
    assert TransportExport is Transport
