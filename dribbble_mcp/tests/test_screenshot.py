"""Tests for dribbble_mcp.screenshot."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dribbble_mcp.screenshot import ScreenshotCapture, capture_shot_async


@pytest.fixture
def capture() -> ScreenshotCapture:
    return ScreenshotCapture(timeout_ms=5000)


_FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50


def _make_sync_pw_mock(page_mock: MagicMock) -> MagicMock:
    mock_context = MagicMock()
    mock_context.new_page.return_value = page_mock

    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_chromium = MagicMock()
    mock_chromium.launch.return_value = mock_browser

    mock_pw = MagicMock()
    mock_pw.chromium = mock_chromium
    mock_pw.__enter__ = MagicMock(return_value=mock_pw)
    mock_pw.__exit__ = MagicMock(return_value=False)
    return mock_pw


class TestScreenshotCapture:
    def test_invalid_url_raises(self, capture: ScreenshotCapture) -> None:
        with pytest.raises(ValueError, match="valid Dribbble shot URL"):
            capture.capture_shot("https://example.com/not-dribbble")

    def test_empty_url_raises(self, capture: ScreenshotCapture) -> None:
        with pytest.raises(ValueError, match="valid Dribbble shot URL"):
            capture.capture_shot("")

    def test_missing_playwright_raises_runtime_error(self, capture: ScreenshotCapture) -> None:
        with patch("dribbble_mcp.screenshot.sync_playwright", None):
            with pytest.raises(RuntimeError, match="playwright is required"):
                capture.capture_shot("https://dribbble.com/shots/123-test")

    def test_capture_returns_base64_string(self, capture: ScreenshotCapture) -> None:
        mock_element = MagicMock()
        mock_element.screenshot.return_value = _FAKE_PNG

        mock_page = MagicMock()
        mock_page.query_selector.return_value = mock_element

        mock_pw = _make_sync_pw_mock(mock_page)

        with patch("dribbble_mcp.screenshot.sync_playwright", return_value=mock_pw):
            result = capture.capture_shot("https://dribbble.com/shots/123-test")

        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        assert decoded == _FAKE_PNG

    def test_capture_full_page(self, capture: ScreenshotCapture) -> None:
        mock_page = MagicMock()
        mock_page.screenshot.return_value = _FAKE_PNG

        mock_pw = _make_sync_pw_mock(mock_page)

        with patch("dribbble_mcp.screenshot.sync_playwright", return_value=mock_pw):
            result = capture.capture_shot("https://dribbble.com/shots/123-test", full_page=True)

        mock_page.screenshot.assert_called_once_with(full_page=True, type="png")
        assert isinstance(result, str)

    def test_capture_falls_back_to_page_screenshot_when_no_element(self, capture: ScreenshotCapture) -> None:
        mock_page = MagicMock()
        mock_page.query_selector.return_value = None
        mock_page.screenshot.return_value = _FAKE_PNG

        mock_pw = _make_sync_pw_mock(mock_page)

        with patch("dribbble_mcp.screenshot.sync_playwright", return_value=mock_pw):
            result = capture.capture_shot("https://dribbble.com/shots/123-test")

        assert isinstance(result, str)

    def test_playwright_exception_raises_runtime_error(self, capture: ScreenshotCapture) -> None:
        mock_pw = MagicMock()
        mock_pw.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw.__exit__ = MagicMock(return_value=False)
        mock_pw.chromium.launch.side_effect = RuntimeError("browser crash")

        with patch("dribbble_mcp.screenshot.sync_playwright", return_value=mock_pw):
            with pytest.raises(RuntimeError, match="Screenshot capture failed"):
                capture.capture_shot("https://dribbble.com/shots/123-test")

    def test_browser_closed_on_success(self, capture: ScreenshotCapture) -> None:
        mock_page = MagicMock()
        mock_page.query_selector.return_value = None
        mock_page.screenshot.return_value = _FAKE_PNG

        mock_pw = _make_sync_pw_mock(mock_page)

        with patch("dribbble_mcp.screenshot.sync_playwright", return_value=mock_pw):
            capture.capture_shot("https://dribbble.com/shots/123-test")

        mock_pw.chromium.launch.return_value.close.assert_called_once()

    def test_element_screenshot_exception_falls_back(self, capture: ScreenshotCapture) -> None:
        mock_element = MagicMock()
        mock_element.screenshot.side_effect = RuntimeError("element gone")

        mock_page = MagicMock()
        mock_page.query_selector.return_value = mock_element
        mock_page.screenshot.return_value = _FAKE_PNG

        mock_pw = _make_sync_pw_mock(mock_page)

        with patch("dribbble_mcp.screenshot.sync_playwright", return_value=mock_pw):
            result = capture.capture_shot("https://dribbble.com/shots/123-test")

        assert isinstance(result, str)


class TestCaptureShotAsync:
    def test_invalid_url_raises(self) -> None:
        import asyncio

        with pytest.raises(ValueError, match="valid Dribbble shot URL"):
            asyncio.run(capture_shot_async("https://example.com/not-dribbble"))

    def test_empty_url_raises(self) -> None:
        import asyncio

        with pytest.raises(ValueError, match="valid Dribbble shot URL"):
            asyncio.run(capture_shot_async(""))

    def test_missing_playwright_raises(self) -> None:
        import asyncio

        with patch("dribbble_mcp.screenshot.async_playwright", None):
            with pytest.raises(RuntimeError, match="playwright is required"):
                asyncio.run(capture_shot_async("https://dribbble.com/shots/123-test"))

    @pytest.mark.asyncio
    async def test_async_capture_returns_base64(self) -> None:
        mock_element = AsyncMock()
        mock_element.screenshot = AsyncMock(return_value=_FAKE_PNG)

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_page.screenshot = AsyncMock(return_value=_FAKE_PNG)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw = AsyncMock()
        mock_pw.chromium = mock_chromium
        mock_pw.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw.__aexit__ = AsyncMock(return_value=False)

        with patch("dribbble_mcp.screenshot.async_playwright", return_value=mock_pw):
            result = await capture_shot_async("https://dribbble.com/shots/123-test")

        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        assert decoded == _FAKE_PNG

    @pytest.mark.asyncio
    async def test_async_capture_fallback_to_page_screenshot(self) -> None:
        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.screenshot = AsyncMock(return_value=_FAKE_PNG)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw = AsyncMock()
        mock_pw.chromium = mock_chromium
        mock_pw.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw.__aexit__ = AsyncMock(return_value=False)

        with patch("dribbble_mcp.screenshot.async_playwright", return_value=mock_pw):
            result = await capture_shot_async("https://dribbble.com/shots/123-test")

        assert isinstance(result, str)
        mock_page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_selector_exception_falls_back(self) -> None:
        mock_element = AsyncMock()
        mock_element.screenshot = AsyncMock(side_effect=RuntimeError("gone"))

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_page.screenshot = AsyncMock(return_value=_FAKE_PNG)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw = AsyncMock()
        mock_pw.chromium = mock_chromium
        mock_pw.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw.__aexit__ = AsyncMock(return_value=False)

        with patch("dribbble_mcp.screenshot.async_playwright", return_value=mock_pw):
            result = await capture_shot_async("https://dribbble.com/shots/123-test")

        assert isinstance(result, str)
