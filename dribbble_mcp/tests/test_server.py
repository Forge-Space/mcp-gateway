"""Tests for dribbble_mcp.server MCP tool functions."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx

from dribbble_mcp.server import (
    analyze_image,
    collect_references,
    get_shot_details,
    screenshot_shot,
    search_dribbble,
)

_SHOT = {
    "title": "Dark Dashboard",
    "url": "https://dribbble.com/shots/123-dark",
    "image_url": "https://cdn.dribbble.com/img.jpg",
    "designer": "Jane",
    "designer_url": "https://dribbble.com/jane",
    "tags": ["dashboard", "dark"],
    "likes": 500,
}

_DETAILS = {
    "title": "Dark Dashboard",
    "url": "https://dribbble.com/shots/123-dark",
    "description": "A dark UI",
    "image_urls": ["https://cdn.dribbble.com/img.jpg"],
    "designer": "Jane",
    "designer_url": "https://dribbble.com/jane",
    "tags": ["dashboard"],
    "likes": 500,
    "views": 10000,
    "colors": ["#1A2B3C"],
}

_IMAGE_ANALYSIS = {
    "width": 400,
    "height": 300,
    "aspect_ratio": 1.3333,
    "format": "PNG",
    "dominant_colors": ["#FF5733", "#2C3E50"],
    "file_size_bytes": 12345,
}


class TestSearchDribbble:
    def test_returns_json_with_shots(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = [_SHOT]
            mock_scraper_fn.return_value = mock_scraper

            result = search_dribbble("dark dashboard")

        data = json.loads(result)
        assert data["count"] == 1
        assert data["shots"][0]["title"] == "Dark Dashboard"
        assert data["query"] == "dark dashboard"

    def test_empty_query_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.side_effect = ValueError(
                "query must not be empty"
            )
            mock_scraper_fn.return_value = mock_scraper

            result = search_dribbble("")

        data = json.loads(result)
        assert "error" in data

    def test_network_error_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.side_effect = httpx.RequestError("timeout")
            mock_scraper_fn.return_value = mock_scraper

            result = search_dribbble("ui")

        data = json.loads(result)
        assert "error" in data

    def test_passes_filters_to_scraper(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = []
            mock_scraper_fn.return_value = mock_scraper

            search_dribbble(
                "ui", limit=5, timeframe="week", category="web-design", color="ff5733"
            )

        mock_scraper.search_shots.assert_called_once_with(
            query="ui",
            limit=5,
            timeframe="week",
            category="web-design",
            color="ff5733",
        )

    def test_empty_filters_passed_as_none(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = []
            mock_scraper_fn.return_value = mock_scraper

            search_dribbble("ui")

        call_kwargs = mock_scraper.search_shots.call_args[1]
        assert call_kwargs["timeframe"] is None
        assert call_kwargs["category"] is None
        assert call_kwargs["color"] is None

    def test_returns_valid_json(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = []
            mock_scraper_fn.return_value = mock_scraper

            result = search_dribbble("ui")

        parsed = json.loads(result)
        assert isinstance(parsed, dict)


class TestGetShotDetails:
    def test_returns_details(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.get_shot_details.return_value = _DETAILS
            mock_scraper_fn.return_value = mock_scraper

            result = get_shot_details("https://dribbble.com/shots/123-dark")

        data = json.loads(result)
        assert data["title"] == "Dark Dashboard"
        assert data["likes"] == 500

    def test_invalid_url_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.get_shot_details.side_effect = ValueError("invalid URL")
            mock_scraper_fn.return_value = mock_scraper

            result = get_shot_details("https://example.com/not-dribbble")

        data = json.loads(result)
        assert "error" in data

    def test_network_error_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.get_shot_details.side_effect = httpx.RequestError("timeout")
            mock_scraper_fn.return_value = mock_scraper

            result = get_shot_details("https://dribbble.com/shots/123-dark")

        data = json.loads(result)
        assert "error" in data


class TestScreenshotShot:
    def test_returns_base64_png(self) -> None:
        with patch("dribbble_mcp.server._get_screenshot") as mock_cap_fn:
            mock_cap = MagicMock()
            mock_cap.capture_shot.return_value = "aGVsbG8="
            mock_cap_fn.return_value = mock_cap

            result = screenshot_shot("https://dribbble.com/shots/123-dark")

        data = json.loads(result)
        assert data["format"] == "png"
        assert data["encoding"] == "base64"
        assert data["data"] == "aGVsbG8="

    def test_invalid_url_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_screenshot") as mock_cap_fn:
            mock_cap = MagicMock()
            mock_cap.capture_shot.side_effect = ValueError("invalid URL")
            mock_cap_fn.return_value = mock_cap

            result = screenshot_shot("https://example.com")

        data = json.loads(result)
        assert "error" in data

    def test_runtime_error_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_screenshot") as mock_cap_fn:
            mock_cap = MagicMock()
            mock_cap.capture_shot.side_effect = RuntimeError("browser crash")
            mock_cap_fn.return_value = mock_cap

            result = screenshot_shot("https://dribbble.com/shots/123-dark")

        data = json.loads(result)
        assert "error" in data

    def test_full_page_flag_passed(self) -> None:
        with patch("dribbble_mcp.server._get_screenshot") as mock_cap_fn:
            mock_cap = MagicMock()
            mock_cap.capture_shot.return_value = "aGVsbG8="
            mock_cap_fn.return_value = mock_cap

            screenshot_shot("https://dribbble.com/shots/123-dark", full_page=True)

        mock_cap.capture_shot.assert_called_once_with(
            "https://dribbble.com/shots/123-dark", full_page=True
        )


class TestAnalyzeImage:
    def test_returns_analysis(self) -> None:
        with patch("dribbble_mcp.server._get_analyzer") as mock_analyzer_fn:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_from_url.return_value = _IMAGE_ANALYSIS
            mock_analyzer_fn.return_value = mock_analyzer

            result = analyze_image("https://cdn.dribbble.com/img.jpg")

        data = json.loads(result)
        assert data["width"] == 400
        assert data["format"] == "PNG"
        assert "#FF5733" in data["dominant_colors"]

    def test_invalid_url_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_analyzer") as mock_analyzer_fn:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_from_url.side_effect = ValueError("invalid URL")
            mock_analyzer_fn.return_value = mock_analyzer

            result = analyze_image("not-a-url")

        data = json.loads(result)
        assert "error" in data

    def test_runtime_error_returns_error(self) -> None:
        with patch("dribbble_mcp.server._get_analyzer") as mock_analyzer_fn:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_from_url.side_effect = RuntimeError("download failed")
            mock_analyzer_fn.return_value = mock_analyzer

            result = analyze_image("https://cdn.dribbble.com/img.jpg")

        data = json.loads(result)
        assert "error" in data


class TestCollectReferences:
    def test_returns_references_with_analysis(self) -> None:
        with (
            patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn,
            patch("dribbble_mcp.server._get_analyzer") as mock_analyzer_fn,
        ):
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = [_SHOT]
            mock_scraper_fn.return_value = mock_scraper

            mock_analyzer = MagicMock()
            mock_analyzer.analyze_from_url.return_value = _IMAGE_ANALYSIS
            mock_analyzer_fn.return_value = mock_analyzer

            result = collect_references("dark dashboard")

        data = json.loads(result)
        assert data["count"] == 1
        assert data["references"][0]["title"] == "Dark Dashboard"
        assert data["references"][0]["image_analysis"]["width"] == 400

    def test_analyze_images_false_skips_analysis(self) -> None:
        with (
            patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn,
            patch("dribbble_mcp.server._get_analyzer") as mock_analyzer_fn,
        ):
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = [_SHOT]
            mock_scraper_fn.return_value = mock_scraper

            result = collect_references("dark dashboard", analyze_images=False)

        mock_analyzer_fn.assert_not_called()
        data = json.loads(result)
        assert "image_analysis" not in data["references"][0]

    def test_image_analysis_failure_sets_none(self) -> None:
        with (
            patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn,
            patch("dribbble_mcp.server._get_analyzer") as mock_analyzer_fn,
        ):
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = [_SHOT]
            mock_scraper_fn.return_value = mock_scraper

            mock_analyzer = MagicMock()
            mock_analyzer.analyze_from_url.side_effect = RuntimeError("download failed")
            mock_analyzer_fn.return_value = mock_analyzer

            result = collect_references("dark dashboard")

        data = json.loads(result)
        assert data["references"][0]["image_analysis"] is None

    def test_invalid_filters_json_returns_error(self) -> None:
        result = collect_references("dark dashboard", filters="{invalid json}")
        data = json.loads(result)
        assert "error" in data

    def test_valid_filters_json_passed_to_scraper(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = []
            mock_scraper_fn.return_value = mock_scraper

            collect_references(
                "ui",
                filters='{"timeframe": "month", "category": "web-design", "color": "3b82f6"}',
                analyze_images=False,
            )

        call_kwargs = mock_scraper.search_shots.call_args[1]
        assert call_kwargs["timeframe"] == "month"
        assert call_kwargs["category"] == "web-design"
        assert call_kwargs["color"] == "3b82f6"

    def test_limit_clamped_to_12(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = []
            mock_scraper_fn.return_value = mock_scraper

            collect_references("ui", limit=100, analyze_images=False)

        call_kwargs = mock_scraper.search_shots.call_args[1]
        assert call_kwargs["limit"] == 12

    def test_search_error_returns_error_json(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.side_effect = httpx.RequestError("timeout")
            mock_scraper_fn.return_value = mock_scraper

            result = collect_references("ui")

        data = json.loads(result)
        assert "error" in data

    def test_returns_valid_json(self) -> None:
        with patch("dribbble_mcp.server._get_scraper") as mock_scraper_fn:
            mock_scraper = MagicMock()
            mock_scraper.search_shots.return_value = []
            mock_scraper_fn.return_value = mock_scraper

            result = collect_references("ui", analyze_images=False)

        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert "references" in parsed
