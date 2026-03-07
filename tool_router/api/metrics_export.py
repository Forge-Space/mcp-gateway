"""Prometheus-compatible metrics endpoint for MCP Gateway."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import APIRouter, Response


logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])


class MetricsCollector:
    """Thread-safe metrics collector for Prometheus text format."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._request_count: dict[str, int] = defaultdict(int)
        self._error_count: dict[str, int] = defaultdict(int)
        self._duration_sum: dict[str, float] = defaultdict(float)
        self._duration_count: dict[str, int] = defaultdict(int)
        self._start_time = time.monotonic()

    def record_request(self, method: str, path: str, status: int, duration: float) -> None:
        key = f"{method}_{path}_{status}"
        with self._lock:
            self._request_count[key] += 1
            self._duration_sum[key] += duration
            self._duration_count[key] += 1
            if status >= 400:
                self._error_count[f"{method}_{path}"] += 1

    def format_prometheus(self) -> str:
        lines: list[str] = []
        uptime = time.monotonic() - self._start_time

        lines.append("# HELP gateway_uptime_seconds Time since gateway started.")
        lines.append("# TYPE gateway_uptime_seconds gauge")
        lines.append(f"gateway_uptime_seconds {uptime:.2f}")
        lines.append("")

        with self._lock:
            lines.append("# HELP gateway_requests_total Total HTTP requests.")
            lines.append("# TYPE gateway_requests_total counter")
            total = sum(self._request_count.values())
            lines.append(f"gateway_requests_total {total}")

            for key, count in sorted(self._request_count.items()):
                parts = key.rsplit("_", 1)
                if len(parts) == 2:
                    route, status = parts[0], parts[1]
                    lines.append(f'gateway_requests_total{{route="{route}",status="{status}"}} {count}')
            lines.append("")

            lines.append("# HELP gateway_errors_total Total HTTP error responses.")
            lines.append("# TYPE gateway_errors_total counter")
            error_total = sum(self._error_count.values())
            lines.append(f"gateway_errors_total {error_total}")
            for key, count in sorted(self._error_count.items()):
                lines.append(f'gateway_errors_total{{route="{key}"}} {count}')
            lines.append("")

            lines.append("# HELP gateway_request_duration_seconds Request duration in seconds.")
            lines.append("# TYPE gateway_request_duration_seconds summary")
            for key in sorted(self._duration_sum):
                parts = key.rsplit("_", 1)
                if len(parts) == 2:
                    route = parts[0]
                    dur_sum = self._duration_sum[key]
                    dur_count = self._duration_count[key]
                    lines.append(f'gateway_request_duration_seconds_sum{{route="{route}"}} {dur_sum:.6f}')
                    lines.append(f'gateway_request_duration_seconds_count{{route="{route}"}} {dur_count}')
            lines.append("")

        lines.append("# EOF")
        return "\n".join(lines) + "\n"


metrics = MetricsCollector()


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description=(
        "Exposes gateway metrics in Prometheus text format. Includes request count, error count, duration, and uptime."
    ),
    response_class=Response,
    responses={200: {"content": {"text/plain; version=0.0.4; charset=utf-8": {}}}},
)
async def get_metrics() -> Response:
    return Response(
        content=metrics.format_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
