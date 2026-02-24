"""Tests for dribbble_mcp.image_analysis."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import httpx
import pytest

from dribbble_mcp.image_analysis import ImageAnalyzer, _extract_dominant_colors


def _make_png_bytes(
    width: int = 10, height: int = 10, color: tuple = (255, 0, 0)
) -> bytes:
    """Create a minimal PNG image in memory."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_jpeg_bytes(width: int = 20, height: int = 10) -> bytes:
    from PIL import Image

    img = Image.new("RGB", (width, height), color=(0, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def analyzer() -> ImageAnalyzer:
    return ImageAnalyzer(timeout_s=5.0)


class TestImageAnalyzer:
    def test_analyze_from_bytes_png(self, analyzer: ImageAnalyzer) -> None:
        png = _make_png_bytes(100, 50, color=(255, 0, 0))
        result = analyzer.analyze_from_bytes(png)

        assert result["width"] == 100
        assert result["height"] == 50
        assert result["format"] == "PNG"
        assert result["aspect_ratio"] == pytest.approx(2.0, rel=0.01)
        assert isinstance(result["dominant_colors"], list)
        assert result["file_size_bytes"] == len(png)

    def test_analyze_from_bytes_jpeg(self, analyzer: ImageAnalyzer) -> None:
        jpeg = _make_jpeg_bytes(20, 10)
        result = analyzer.analyze_from_bytes(jpeg)

        assert result["width"] == 20
        assert result["height"] == 10
        assert result["format"] == "JPEG"

    def test_analyze_from_bytes_aspect_ratio(self, analyzer: ImageAnalyzer) -> None:
        png = _make_png_bytes(200, 100)
        result = analyzer.analyze_from_bytes(png)
        assert result["aspect_ratio"] == pytest.approx(2.0, rel=0.01)

    def test_analyze_from_bytes_square_aspect_ratio(
        self, analyzer: ImageAnalyzer
    ) -> None:
        png = _make_png_bytes(50, 50)
        result = analyzer.analyze_from_bytes(png)
        assert result["aspect_ratio"] == pytest.approx(1.0, rel=0.01)

    def test_analyze_from_bytes_invalid_data_raises(
        self, analyzer: ImageAnalyzer
    ) -> None:
        with pytest.raises(RuntimeError, match="Failed to open image"):
            analyzer.analyze_from_bytes(b"not an image")

    def test_analyze_from_bytes_empty_raises(self, analyzer: ImageAnalyzer) -> None:
        with pytest.raises(RuntimeError):
            analyzer.analyze_from_bytes(b"")

    def test_analyze_from_url_success(self, analyzer: ImageAnalyzer) -> None:
        png = _make_png_bytes(30, 30)
        mock_response = MagicMock()
        mock_response.content = png
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = analyzer.analyze_from_url("https://cdn.dribbble.com/image.png")

        assert result["width"] == 30
        assert result["height"] == 30

    def test_analyze_from_url_empty_raises(self, analyzer: ImageAnalyzer) -> None:
        with pytest.raises(ValueError, match="valid HTTP"):
            analyzer.analyze_from_url("")

    def test_analyze_from_url_invalid_scheme_raises(
        self, analyzer: ImageAnalyzer
    ) -> None:
        with pytest.raises(ValueError, match="valid HTTP"):
            analyzer.analyze_from_url("ftp://example.com/image.png")

    def test_analyze_from_url_http_error_raises(self, analyzer: ImageAnalyzer) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "404", request=MagicMock(), response=mock_response
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="Failed to download image"):
                analyzer.analyze_from_url("https://cdn.dribbble.com/missing.png")

    def test_analyze_from_url_network_error_raises(
        self, analyzer: ImageAnalyzer
    ) -> None:
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.RequestError("timeout")
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="Network error"):
                analyzer.analyze_from_url("https://cdn.dribbble.com/image.png")

    def test_dominant_colors_returned(self, analyzer: ImageAnalyzer) -> None:
        png = _make_png_bytes(50, 50, color=(255, 0, 0))
        result = analyzer.analyze_from_bytes(png)
        assert len(result["dominant_colors"]) >= 1
        for color in result["dominant_colors"]:
            assert color.startswith("#")
            assert len(color) in (4, 7)

    def test_file_size_bytes_correct(self, analyzer: ImageAnalyzer) -> None:
        png = _make_png_bytes(10, 10)
        result = analyzer.analyze_from_bytes(png)
        assert result["file_size_bytes"] == len(png)


class TestExtractDominantColors:
    def test_returns_list(self) -> None:
        from PIL import Image

        img = Image.new("RGB", (10, 10), color=(100, 200, 50))
        colors = _extract_dominant_colors(img)
        assert isinstance(colors, list)

    def test_colors_are_hex_strings(self) -> None:
        from PIL import Image

        img = Image.new("RGB", (20, 20), color=(255, 128, 0))
        colors = _extract_dominant_colors(img)
        for c in colors:
            assert c.startswith("#")

    def test_handles_invalid_image_gracefully(self) -> None:
        mock_img = MagicMock()
        mock_img.convert.side_effect = RuntimeError("bad image")
        colors = _extract_dominant_colors(mock_img)
        assert colors == []
