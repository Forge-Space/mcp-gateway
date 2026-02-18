"""Dribbble scraper using httpx + BeautifulSoup."""

from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

DRIBBBLE_BASE = "https://dribbble.com"
SEARCH_URL = "https://dribbble.com/search/shots"

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

VALID_TIMEFRAMES = {"now", "week", "month", "year", "all"}
VALID_CATEGORIES = {
    "animation",
    "branding",
    "illustration",
    "mobile",
    "print",
    "product-design",
    "typography",
    "web-design",
}


class DribbbleScraper:
    """Scrapes Dribbble for design shots and metadata."""

    def __init__(
        self,
        session_cookie: str | None = None,
        rate_limit_ms: int = 1000,
        timeout_s: float = 15.0,
    ) -> None:
        self._session_cookie = session_cookie
        self._rate_limit_s = rate_limit_ms / 1000.0
        self._timeout = timeout_s
        self._last_request_time: float = 0.0

    def _build_headers(self) -> dict[str, str]:
        headers = dict(_DEFAULT_HEADERS)
        if self._session_cookie:
            headers["Cookie"] = f"dribbble_session={self._session_cookie}"
        return headers

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self._rate_limit_s:
            time.sleep(self._rate_limit_s - elapsed)
        self._last_request_time = time.monotonic()

    def _get(self, url: str) -> str:
        self._throttle()
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            response = client.get(url, headers=self._build_headers())
            response.raise_for_status()
            return response.text

    def search_shots(
        self,
        query: str,
        limit: int = 12,
        timeframe: str | None = None,
        category: str | None = None,
        color: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search Dribbble for shots matching the query.

        Args:
            query: Search keywords.
            limit: Maximum number of results (1-48).
            timeframe: One of 'now', 'week', 'month', 'year', 'all'.
            category: Design category filter (e.g. 'web-design').
            color: Hex color filter without '#' (e.g. 'ff5733').

        Returns:
            List of shot dicts with keys: title, url, image_url, designer,
            designer_url, tags, likes.
        """
        if not query or not query.strip():
            msg = "query must not be empty"
            raise ValueError(msg)

        limit = max(1, min(48, limit))

        params: list[tuple[str, str]] = [("q", query.strip())]
        if timeframe and timeframe in VALID_TIMEFRAMES:
            params.append(("timeframe", timeframe))
        if category and category in VALID_CATEGORIES:
            params.append(("category", category))
        if color:
            clean_color = color.lstrip("#")
            params.append(("color", clean_color))

        query_string = "&".join(f"{k}={quote_plus(v)}" for k, v in params)
        url = f"{SEARCH_URL}?{query_string}"

        logger.info("Searching Dribbble: %s", url)

        try:
            html = self._get(url)
        except httpx.HTTPStatusError:
            logger.exception("HTTP error fetching search results")
            raise
        except httpx.RequestError:
            logger.exception("Request error fetching search results")
            raise

        shots = self._parse_search_results(html)
        return shots[:limit]

    def _parse_search_results(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        shots: list[dict[str, Any]] = []

        shot_items = soup.select("li.shot-thumbnail")
        if not shot_items:
            shot_items = soup.select("[data-thumbnail]")
        if not shot_items:
            shot_items = soup.select(".shot-thumbnail-container")

        for item in shot_items:
            shot = self._extract_shot_from_list_item(item)
            if shot:
                shots.append(shot)

        logger.info("Parsed %d shots from search results", len(shots))
        return shots

    def _extract_shot_from_list_item(self, item: Any) -> dict[str, Any] | None:
        try:
            link = item.select_one("a.shot-thumbnail-link") or item.select_one("a[href*='/shots/']")
            if not link:
                return None

            shot_url = urljoin(DRIBBBLE_BASE, link.get("href", ""))
            if not shot_url or "/shots/" not in shot_url:
                return None

            title_el = item.select_one(".shot-title") or item.select_one("[class*='title']")
            title = title_el.get_text(strip=True) if title_el else link.get("title", "Untitled")

            img = item.select_one("img")
            image_url = ""
            if img:
                image_url = (
                    img.get("data-src")
                    or img.get("src")
                    or img.get("data-srcset", "").split(" ")[0]
                    or ""
                )

            designer_el = item.select_one(".display-name") or item.select_one("[class*='designer']")
            designer = designer_el.get_text(strip=True) if designer_el else ""

            designer_link = item.select_one("a[href*='/']")
            designer_url = ""
            if designer_link and designer_link.get("href", "").startswith("/"):
                href = designer_link.get("href", "")
                if "/shots/" not in href:
                    designer_url = urljoin(DRIBBBLE_BASE, href)

            likes_el = item.select_one(".js-shot-likes-count") or item.select_one("[class*='likes']")
            likes_text = likes_el.get_text(strip=True) if likes_el else "0"
            likes = _parse_count(likes_text)

            tags: list[str] = []
            for tag_el in item.select("a[href*='/tags/']"):
                tag_text = tag_el.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)

        except (AttributeError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse shot item: %s", exc)
            return None
        else:
            return {
                "title": title,
                "url": shot_url,
                "image_url": image_url,
                "designer": designer,
                "designer_url": designer_url,
                "tags": tags,
                "likes": likes,
            }
        return None

    def get_shot_details(self, shot_url: str) -> dict[str, Any]:
        """Fetch full metadata for a single Dribbble shot page.

        Args:
            shot_url: Full URL of the Dribbble shot (e.g. https://dribbble.com/shots/12345-...).

        Returns:
            Dict with keys: title, url, description, image_urls, designer,
            designer_url, tags, likes, colors, views.
        """
        if not shot_url or "dribbble.com" not in shot_url:
            msg = "shot_url must be a valid Dribbble shot URL"
            raise ValueError(msg)

        logger.info("Fetching shot details: %s", shot_url)

        try:
            html = self._get(shot_url)
        except httpx.HTTPStatusError:
            logger.exception("HTTP error fetching shot details")
            raise
        except httpx.RequestError:
            logger.exception("Request error fetching shot details")
            raise

        return self._parse_shot_page(html, shot_url)

    def _parse_shot_page(self, html: str, shot_url: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")

        title_el = soup.select_one("h1.shot-title") or soup.select_one("title")
        title = title_el.get_text(strip=True) if title_el else "Untitled"
        if " on Dribbble" in title:
            title = title.replace(" on Dribbble", "").strip()

        desc_el = soup.select_one(".shot-desc") or soup.select_one("[class*='description']")
        description = desc_el.get_text(strip=True) if desc_el else ""

        image_urls: list[str] = []
        for img in soup.select(".shot-media img, .media-content img, .shot-image img"):
            src = img.get("data-src") or img.get("src") or ""
            if src and src not in image_urls:
                image_urls.append(src)

        designer_el = soup.select_one(".shot-user-name a") or soup.select_one("[class*='player-name'] a")
        designer = designer_el.get_text(strip=True) if designer_el else ""
        designer_url = ""
        if designer_el and designer_el.get("href"):
            designer_url = urljoin(DRIBBBLE_BASE, designer_el["href"])

        tags: list[str] = []
        for tag_el in soup.select("a.tag, a[href*='/tags/']"):
            tag_text = tag_el.get_text(strip=True)
            if tag_text and tag_text not in tags:
                tags.append(tag_text)

        likes_el = soup.select_one(".js-shot-likes-count") or soup.select_one("[class*='likes-count']")
        likes = _parse_count(likes_el.get_text(strip=True) if likes_el else "0")

        views_el = soup.select_one(".js-shot-views-count") or soup.select_one("[class*='views-count']")
        views = _parse_count(views_el.get_text(strip=True) if views_el else "0")

        colors: list[str] = []
        for color_el in soup.select(".color-chip, [class*='color-swatch']"):
            style = color_el.get("style", "")
            if "background" in style:
                hex_color = _extract_hex_from_style(style)
                if hex_color and hex_color not in colors:
                    colors.append(hex_color)

        return {
            "title": title,
            "url": shot_url,
            "description": description,
            "image_urls": image_urls,
            "designer": designer,
            "designer_url": designer_url,
            "tags": tags,
            "likes": likes,
            "views": views,
            "colors": colors,
        }


def _parse_count(text: str) -> int:
    text = text.strip().replace(",", "")
    if text.endswith(("k", "K")):
        try:
            return int(float(text[:-1]) * 1000)
        except ValueError:
            return 0
    text = text.replace(".", "")
    try:
        return int(text)
    except ValueError:
        return 0


def _extract_hex_from_style(style: str) -> str | None:
    match = re.search(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})", style)
    if match:
        return f"#{match.group(1).upper()}"
    return None
