"""Image analysis using Pillow: dominant colors, dimensions, aspect ratio."""

from __future__ import annotations

import io
import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)

_MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
_COLOR_QUANTIZE_COLORS = 16
_TOP_COLORS = 5


class ImageAnalyzer:
    """Analyzes images for dominant colors, dimensions, and format."""

    def __init__(self, timeout_s: float = 15.0) -> None:
        self._timeout = timeout_s

    def analyze_from_url(self, image_url: str) -> dict[str, Any]:
        """Download and analyze an image from a URL.

        Args:
            image_url: Public URL of the image to analyze.

        Returns:
            Dict with keys: width, height, aspect_ratio, format,
            dominant_colors (list of hex strings), file_size_bytes.

        Raises:
            ValueError: If image_url is empty or invalid.
            RuntimeError: If download or analysis fails.
        """
        if not image_url or not image_url.startswith(("http://", "https://")):
            msg = "image_url must be a valid HTTP/HTTPS URL"
            raise ValueError(msg)

        logger.info("Analyzing image: %s", image_url)

        try:
            image_bytes = self._download(image_url)
        except httpx.HTTPStatusError as exc:
            msg = f"Failed to download image (HTTP {exc.response.status_code}): {image_url}"
            raise RuntimeError(msg) from exc
        except httpx.RequestError as exc:
            msg = f"Network error downloading image: {exc}"
            raise RuntimeError(msg) from exc

        return self.analyze_from_bytes(image_bytes)

    def analyze_from_bytes(self, image_bytes: bytes) -> dict[str, Any]:
        """Analyze an image from raw bytes.

        Args:
            image_bytes: Raw image bytes.

        Returns:
            Dict with keys: width, height, aspect_ratio, format,
            dominant_colors, file_size_bytes.

        Raises:
            RuntimeError: If Pillow is not installed or analysis fails.
        """
        try:
            from PIL import Image  # noqa: PLC0415
        except ImportError as exc:
            msg = "Pillow is required: pip install Pillow"
            raise RuntimeError(msg) from exc

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()
        except Exception as exc:
            msg = f"Failed to open image: {exc}"
            raise RuntimeError(msg) from exc

        width, height = img.size
        aspect_ratio = round(width / height, 4) if height > 0 else 0.0
        fmt = (img.format or "UNKNOWN").upper()

        dominant_colors = _extract_dominant_colors(img)

        return {
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "format": fmt,
            "dominant_colors": dominant_colors,
            "file_size_bytes": len(image_bytes),
        }

    def _download(self, url: str) -> bytes:
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; DribbbleMCP/1.0; "
                        "+https://github.com/LucasSantana-Dev/forge-mcp-gateway)"
                    )
                },
            )
            response.raise_for_status()
            content = response.content
            if len(content) > _MAX_IMAGE_SIZE_BYTES:
                msg = f"Image too large: {len(content)} bytes (max {_MAX_IMAGE_SIZE_BYTES})"
                raise RuntimeError(msg)
            return content


def _extract_dominant_colors(img: Any) -> list[str]:
    """Extract the top dominant colors from an image using quantization.

    Args:
        img: PIL Image object.

    Returns:
        List of hex color strings (e.g. ['#FF5733', '#2C3E50']).
    """
    try:
        rgb_img = img.convert("RGB")
        quantized = rgb_img.quantize(colors=_COLOR_QUANTIZE_COLORS, method=2)
        palette = quantized.getpalette()
        if not palette:
            return []

        pixel_counts: dict[int, int] = {}
        pixels = list(quantized.getdata())
        for px in pixels:
            pixel_counts[px] = pixel_counts.get(px, 0) + 1

        sorted_indices = sorted(pixel_counts, key=lambda i: pixel_counts[i], reverse=True)

        colors: list[str] = []
        for idx in sorted_indices[:_TOP_COLORS]:
            r = palette[idx * 3]
            g = palette[idx * 3 + 1]
            b = palette[idx * 3 + 2]
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            if hex_color not in colors:
                colors.append(hex_color)
    except (AttributeError, TypeError, ValueError, OSError, RuntimeError) as exc:
        logger.warning("Color extraction failed: %s", exc)
        return []
    else:
        return colors
    return []
