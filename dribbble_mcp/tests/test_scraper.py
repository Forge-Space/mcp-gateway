"""Tests for dribbble_mcp.scraper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from dribbble_mcp.scraper import (
    DribbbleScraper,
    _extract_hex_from_style,
    _parse_count,
)

SEARCH_HTML = """
<html><body>
<ul>
  <li class="shot-thumbnail">
    <a class="shot-thumbnail-link" href="/shots/123-my-design" title="My Design">
      <img src="https://cdn.dribbble.com/shot.jpg" />
    </a>
    <span class="shot-title">My Design</span>
    <span class="display-name">Jane Doe</span>
    <span class="js-shot-likes-count">1.2k</span>
    <a href="/tags/ui">ui</a>
    <a href="/tags/dark">dark</a>
  </li>
  <li class="shot-thumbnail">
    <a class="shot-thumbnail-link" href="/shots/456-another" title="Another">
      <img data-src="https://cdn.dribbble.com/another.png" />
    </a>
    <span class="shot-title">Another Shot</span>
    <span class="display-name">John Smith</span>
    <span class="js-shot-likes-count">500</span>
  </li>
</ul>
</body></html>
"""

SHOT_DETAIL_HTML = """
<html><head><title>Cool Dashboard on Dribbble</title></head>
<body>
  <h1 class="shot-title">Cool Dashboard</h1>
  <div class="shot-desc">A beautiful dark dashboard design.</div>
  <div class="shot-media">
    <img src="https://cdn.dribbble.com/main.jpg" />
    <img data-src="https://cdn.dribbble.com/alt.jpg" />
  </div>
  <div class="shot-user-name"><a href="/designers/jane">Jane Doe</a></div>
  <a class="tag" href="/tags/dashboard">dashboard</a>
  <a class="tag" href="/tags/dark">dark</a>
  <span class="js-shot-likes-count">2,500</span>
  <span class="js-shot-views-count">45k</span>
  <div class="color-chip" style="background: #1A2B3C;"></div>
  <div class="color-chip" style="background: #FFFFFF;"></div>
</body></html>
"""


@pytest.fixture
def scraper() -> DribbbleScraper:
    return DribbbleScraper(session_cookie=None, rate_limit_ms=0, timeout_s=5.0)


class TestDribbbleScraper:
    def test_search_shots_returns_shots(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SEARCH_HTML):
            shots = scraper.search_shots("dark dashboard")

        assert len(shots) == 2
        assert shots[0]["title"] == "My Design"
        assert shots[0]["url"] == "https://dribbble.com/shots/123-my-design"
        assert shots[0]["image_url"] == "https://cdn.dribbble.com/shot.jpg"
        assert shots[0]["designer"] == "Jane Doe"
        assert "ui" in shots[0]["tags"]
        assert shots[0]["likes"] == 1200

    def test_search_shots_respects_limit(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SEARCH_HTML):
            shots = scraper.search_shots("ui", limit=1)

        assert len(shots) == 1

    def test_search_shots_empty_query_raises(self, scraper: DribbbleScraper) -> None:
        with pytest.raises(ValueError, match="query must not be empty"):
            scraper.search_shots("")

    def test_search_shots_whitespace_query_raises(self, scraper: DribbbleScraper) -> None:
        with pytest.raises(ValueError, match="query must not be empty"):
            scraper.search_shots("   ")

    def test_search_shots_limit_clamped(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SEARCH_HTML):
            shots = scraper.search_shots("ui", limit=100)
        assert len(shots) <= 48

    def test_search_shots_with_filters(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SEARCH_HTML) as mock_get:
            scraper.search_shots("ui", timeframe="week", category="web-design", color="ff5733")
        call_url = mock_get.call_args[0][0]
        assert "timeframe=week" in call_url
        assert "category=web-design" in call_url
        assert "color=ff5733" in call_url

    def test_search_shots_invalid_timeframe_ignored(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SEARCH_HTML) as mock_get:
            scraper.search_shots("ui", timeframe="invalid")
        call_url = mock_get.call_args[0][0]
        assert "timeframe" not in call_url

    def test_search_shots_invalid_category_ignored(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SEARCH_HTML) as mock_get:
            scraper.search_shots("ui", category="not-a-category")
        call_url = mock_get.call_args[0][0]
        assert "category" not in call_url

    def test_search_shots_http_error_propagates(self, scraper: DribbbleScraper) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 403
        with patch.object(
            scraper,
            "_get",
            side_effect=httpx.HTTPStatusError("403", request=MagicMock(), response=mock_response),
        ):
            with pytest.raises(httpx.HTTPStatusError):
                scraper.search_shots("ui")

    def test_search_shots_request_error_propagates(self, scraper: DribbbleScraper) -> None:
        with patch.object(
            scraper,
            "_get",
            side_effect=httpx.RequestError("connection refused"),
        ):
            with pytest.raises(httpx.RequestError):
                scraper.search_shots("ui")

    def test_search_shots_empty_page_returns_empty(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value="<html><body></body></html>"):
            shots = scraper.search_shots("ui")
        assert shots == []

    def test_search_shots_data_src_image(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SEARCH_HTML):
            shots = scraper.search_shots("ui")
        assert shots[1]["image_url"] == "https://cdn.dribbble.com/another.png"

    def test_get_shot_details_returns_metadata(self, scraper: DribbbleScraper) -> None:
        with patch.object(scraper, "_get", return_value=SHOT_DETAIL_HTML):
            details = scraper.get_shot_details("https://dribbble.com/shots/123-cool")

        assert details["title"] == "Cool Dashboard"
        assert details["description"] == "A beautiful dark dashboard design."
        assert "https://cdn.dribbble.com/main.jpg" in details["image_urls"]
        assert details["designer"] == "Jane Doe"
        assert details["designer_url"] == "https://dribbble.com/designers/jane"
        assert "dashboard" in details["tags"]
        assert details["likes"] == 2500
        assert details["views"] == 45000
        assert "#1A2B3C" in details["colors"]

    def test_get_shot_details_invalid_url_raises(self, scraper: DribbbleScraper) -> None:
        with pytest.raises(ValueError, match="valid Dribbble shot URL"):
            scraper.get_shot_details("https://example.com/not-dribbble")

    def test_get_shot_details_empty_url_raises(self, scraper: DribbbleScraper) -> None:
        with pytest.raises(ValueError):
            scraper.get_shot_details("")

    def test_get_shot_details_http_error_propagates(self, scraper: DribbbleScraper) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch.object(
            scraper,
            "_get",
            side_effect=httpx.HTTPStatusError("404", request=MagicMock(), response=mock_response),
        ):
            with pytest.raises(httpx.HTTPStatusError):
                scraper.get_shot_details("https://dribbble.com/shots/999-gone")

    def test_session_cookie_added_to_headers(self) -> None:
        scraper_with_cookie = DribbbleScraper(session_cookie="abc123", rate_limit_ms=0)
        headers = scraper_with_cookie._build_headers()
        assert "Cookie" in headers
        assert "abc123" in headers["Cookie"]

    def test_no_session_cookie_no_cookie_header(self, scraper: DribbbleScraper) -> None:
        headers = scraper._build_headers()
        assert "Cookie" not in headers

    def test_throttle_enforces_rate_limit(self) -> None:
        import time

        scraper_slow = DribbbleScraper(rate_limit_ms=100)
        scraper_slow._last_request_time = time.monotonic()
        start = time.monotonic()
        scraper_slow._throttle()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.08


class TestParseCount:
    def test_plain_integer(self) -> None:
        assert _parse_count("1234") == 1234

    def test_comma_separated(self) -> None:
        assert _parse_count("1,234") == 1234

    def test_k_suffix_lowercase(self) -> None:
        assert _parse_count("1.2k") == 1200

    def test_k_suffix_uppercase(self) -> None:
        assert _parse_count("5K") == 5000

    def test_zero(self) -> None:
        assert _parse_count("0") == 0

    def test_empty_string(self) -> None:
        assert _parse_count("") == 0

    def test_non_numeric(self) -> None:
        assert _parse_count("abc") == 0

    def test_whitespace(self) -> None:
        assert _parse_count("  500  ") == 500


class TestExtractHexFromStyle:
    def test_six_digit_hex(self) -> None:
        result = _extract_hex_from_style("background: #1a2b3c;")
        assert result == "#1A2B3C"

    def test_three_digit_hex(self) -> None:
        result = _extract_hex_from_style("background: #fff;")
        assert result == "#FFF"

    def test_no_hex(self) -> None:
        result = _extract_hex_from_style("background: rgb(255, 0, 0);")
        assert result is None

    def test_empty_style(self) -> None:
        result = _extract_hex_from_style("")
        assert result is None
