"""Playwright-based screenshot capture for Dribbble shots."""

from __future__ import annotations

import base64
import logging
from typing import Any


try:
    from playwright.async_api import async_playwright
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None  # type: ignore[assignment]
    async_playwright = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

_SHOT_SELECTORS = [
    ".shot-media",
    ".media-content",
    ".shot-image",
    ".dribbble-shot",
    "main",
]

_DEFAULT_VIEWPORT: dict[str, int] = {"width": 1280, "height": 900}
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class ScreenshotCapture:
    """Captures screenshots of Dribbble shot pages using Playwright."""

    def __init__(self, timeout_ms: int = 10_000) -> None:
        self._timeout = timeout_ms

    def capture_shot(self, shot_url: str, full_page: bool = False) -> str:
        """Capture a screenshot of a Dribbble shot page.

        Args:
            shot_url: Full URL of the Dribbble shot.
            full_page: If True, capture the full page; otherwise capture the shot element.

        Returns:
            Base64-encoded PNG image string.

        Raises:
            ValueError: If shot_url is invalid.
            RuntimeError: If screenshot capture fails.
        """
        if not shot_url or "dribbble.com" not in shot_url:
            msg = "shot_url must be a valid Dribbble shot URL"
            raise ValueError(msg)

        if sync_playwright is None:
            msg = "playwright is required: pip install playwright && playwright install chromium"
            raise RuntimeError(msg)

        logger.info("Capturing screenshot: %s", shot_url)

        try:
            with sync_playwright() as pw:
                return self._do_capture(pw, shot_url, full_page)
        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Screenshot capture failed for %s", shot_url)
            msg = f"Screenshot capture failed: {exc}"
            raise RuntimeError(msg) from exc

    def _do_capture(self, pw: Any, shot_url: str, full_page: bool) -> str:
        browser = pw.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport=_DEFAULT_VIEWPORT, user_agent=_USER_AGENT)
            page = context.new_page()
            page.goto(shot_url, timeout=self._timeout, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

            png_bytes = (
                page.screenshot(full_page=True, type="png")
                if full_page
                else self._capture_element(page)
            )
            return base64.b64encode(png_bytes).decode("utf-8")
        finally:
            browser.close()

    def _capture_element(self, page: Any) -> bytes:
        for selector in _SHOT_SELECTORS:
            try:
                element = page.query_selector(selector)
                if element:
                    return element.screenshot(type="png")
            except Exception as exc:  # noqa: BLE001
                logger.debug("Selector %s failed: %s", selector, exc)
                continue
        return page.screenshot(type="png")


async def capture_shot_async(shot_url: str, timeout_ms: int = 10_000, full_page: bool = False) -> str:
    """Async version of screenshot capture using Playwright async API.

    Args:
        shot_url: Full URL of the Dribbble shot.
        timeout_ms: Timeout in milliseconds.
        full_page: If True, capture the full page.

    Returns:
        Base64-encoded PNG image string.
    """
    if not shot_url or "dribbble.com" not in shot_url:
        msg = "shot_url must be a valid Dribbble shot URL"
        raise ValueError(msg)

    if async_playwright is None:
        msg = "playwright is required: pip install playwright && playwright install chromium"
        raise RuntimeError(msg)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            context = await browser.new_context(viewport=_DEFAULT_VIEWPORT, user_agent=_USER_AGENT)
            page = await context.new_page()
            await page.goto(shot_url, timeout=timeout_ms, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

            for selector in _SHOT_SELECTORS:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        png_bytes = await element.screenshot(type="png")
                        return base64.b64encode(png_bytes).decode("utf-8")
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Async selector %s failed: %s", selector, exc)
                    continue

            png_bytes = await page.screenshot(full_page=full_page, type="png")
            return base64.b64encode(png_bytes).decode("utf-8")
        finally:
            await browser.close()
