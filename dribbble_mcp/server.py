"""Dribbble MCP server — FastMCP tool definitions."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dribbble_mcp.image_analysis import ImageAnalyzer
from dribbble_mcp.scraper import DribbbleScraper
from dribbble_mcp.screenshot import ScreenshotCapture


try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    msg = "Install the MCP SDK: pip install mcp"
    raise ImportError(msg) from exc


logger = logging.getLogger(__name__)

mcp = FastMCP("dribbble-mcp", json_response=True)

_SESSION_COOKIE = os.getenv("DRIBBBLE_SESSION_COOKIE")
_RATE_LIMIT_MS = int(os.getenv("DRIBBBLE_RATE_LIMIT_MS", "1000"))
_SCREENSHOT_TIMEOUT_MS = int(os.getenv("DRIBBBLE_SCREENSHOT_TIMEOUT_MS", "10000"))
_HTTP_TIMEOUT_S = float(os.getenv("DRIBBBLE_HTTP_TIMEOUT_S", "15.0"))


def _get_scraper() -> DribbbleScraper:
    return DribbbleScraper(
        session_cookie=_SESSION_COOKIE,
        rate_limit_ms=_RATE_LIMIT_MS,
        timeout_s=_HTTP_TIMEOUT_S,
    )


def _get_analyzer() -> ImageAnalyzer:
    return ImageAnalyzer(timeout_s=_HTTP_TIMEOUT_S)


def _get_screenshot() -> ScreenshotCapture:
    return ScreenshotCapture(timeout_ms=_SCREENSHOT_TIMEOUT_MS)


@mcp.tool()
def search_dribbble(
    query: str,
    limit: int = 12,
    timeframe: str = "",
    category: str = "",
    color: str = "",
) -> str:
    """Search Dribbble for design shots matching a query.

    Returns a JSON list of shots with title, URL, image URL, designer, tags, and likes.
    Use this to discover visual references for a UI project.

    Args:
        query: Search keywords (e.g. 'dark dashboard', 'mobile onboarding', 'glassmorphism').
        limit: Number of results to return (1-48, default 12).
        timeframe: Filter by recency — one of: now, week, month, year, all.
        category: Design category — one of: animation, branding, illustration,
                  mobile, print, product-design, typography, web-design.
        color: Dominant color filter as hex without '#' (e.g. 'ff5733').
    """
    logger.info("search_dribbble called: query=%s limit=%d", query, limit)

    scraper = _get_scraper()

    try:
        shots = scraper.search_shots(
            query=query,
            limit=limit,
            timeframe=timeframe or None,
            category=category or None,
            color=color or None,
        )
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("search_dribbble failed")
        return json.dumps({"error": f"Search failed: {exc}"})

    return json.dumps({"query": query, "count": len(shots), "shots": shots}, ensure_ascii=False)


@mcp.tool()
def get_shot_details(shot_url: str) -> str:
    """Fetch full metadata for a single Dribbble shot.

    Returns JSON with title, description, image URLs, designer info, tags,
    likes, views, and color palette extracted from the shot page.

    Args:
        shot_url: Full Dribbble shot URL (e.g. https://dribbble.com/shots/12345-my-design).
    """
    logger.info("get_shot_details called: %s", shot_url)

    scraper = _get_scraper()

    try:
        details = scraper.get_shot_details(shot_url)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("get_shot_details failed")
        return json.dumps({"error": f"Failed to fetch shot details: {exc}"})

    return json.dumps(details, ensure_ascii=False)


@mcp.tool()
def screenshot_shot(shot_url: str, full_page: bool = False) -> str:
    """Take a Playwright screenshot of a Dribbble shot page.

    Returns a JSON object with a base64-encoded PNG image.
    Requires playwright and chromium to be installed.

    Args:
        shot_url: Full Dribbble shot URL.
        full_page: If true, capture the full page; otherwise capture the shot element only.
    """
    logger.info("screenshot_shot called: %s full_page=%s", shot_url, full_page)

    capture = _get_screenshot()

    try:
        b64_png = capture.capture_shot(shot_url, full_page=full_page)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("screenshot_shot failed")
        return json.dumps({"error": f"Screenshot failed: {exc}"})

    return json.dumps(
        {
            "shot_url": shot_url,
            "format": "png",
            "encoding": "base64",
            "data": b64_png,
        }
    )


@mcp.tool()
def analyze_image(image_url: str) -> str:
    """Analyze a design image for dominant colors, dimensions, and format.

    Returns JSON with: width, height, aspect_ratio, format (PNG/JPG/etc.),
    dominant_colors (list of hex strings), file_size_bytes.

    Args:
        image_url: Public URL of the image to analyze (e.g. a Dribbble CDN URL).
    """
    logger.info("analyze_image called: %s", image_url)

    analyzer = _get_analyzer()

    try:
        result = analyzer.analyze_from_url(image_url)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("analyze_image failed")
        return json.dumps({"error": f"Image analysis failed: {exc}"})

    return json.dumps({"image_url": image_url, **result}, ensure_ascii=False)


@mcp.tool()
def collect_references(
    query: str,
    limit: int = 6,
    filters: str = "",
    analyze_images: bool = True,
) -> str:
    """Collect visual design references from Dribbble for a UI project.

    This is the primary tool for uiforge-mcp. It searches Dribbble, then
    optionally analyzes each shot's image for colors and dimensions.
    Returns a rich reference pack ready for UI generation.

    Args:
        query: Design search keywords (e.g. 'SaaS dashboard dark mode', 'mobile fintech app').
        limit: Number of references to collect (1-12, default 6).
        filters: Optional JSON string with filter keys: timeframe (now/week/month/year/all),
                 category (web-design/mobile/branding/illustration/etc.), color (hex without #).
                 Example: '{"timeframe": "month", "category": "web-design", "color": "3b82f6"}'.
        analyze_images: If true, run image analysis on each shot's image (default true).
    """
    logger.info("collect_references called: query=%s limit=%d", query, limit)

    limit = max(1, min(12, limit))
    scraper = _get_scraper()
    analyzer = _get_analyzer() if analyze_images else None

    filter_opts: dict[str, str] = {}
    if filters:
        try:
            filter_opts = json.loads(filters)
        except json.JSONDecodeError as exc:
            return json.dumps({"error": f"Invalid filters JSON: {exc}"})

    try:
        shots = scraper.search_shots(
            query=query,
            limit=limit,
            timeframe=filter_opts.get("timeframe") or None,
            category=filter_opts.get("category") or None,
            color=filter_opts.get("color") or None,
        )
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger.exception("collect_references: search failed")
        return json.dumps({"error": f"Search failed: {exc}"})

    references: list[dict[str, Any]] = []
    for shot in shots:
        ref: dict[str, Any] = dict(shot)
        if analyzer and shot.get("image_url"):
            try:
                image_data = analyzer.analyze_from_url(shot["image_url"])
                ref["image_analysis"] = image_data
            except (RuntimeError, ValueError) as exc:
                logger.warning("Image analysis failed for %s: %s", shot.get("url"), exc)
                ref["image_analysis"] = None
        references.append(ref)

    return json.dumps(
        {
            "query": query,
            "count": len(references),
            "references": references,
        },
        ensure_ascii=False,
    )


def main() -> None:
    """Initialize and run the Dribbble MCP server."""
    logging.basicConfig(level=logging.INFO)
    logger.info(
        "Starting dribbble-mcp (session_cookie=%s, rate_limit_ms=%d)",
        "set" if _SESSION_COOKIE else "not set",
        _RATE_LIMIT_MS,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
