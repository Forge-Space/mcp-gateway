#!/usr/bin/env python3
"""Simple test server for debugging tool router issues."""

import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Python version: %s", sys.version)
logger.info("Python path: %s", sys.path)
logger.info("Current working directory: %s", Path.cwd())
logger.info("Environment variables: %s", dict(os.environ))

try:
    import fastapi

    logger.info("FastAPI imported successfully: %s", fastapi.__version__)
except ImportError as e:
    logger.warning("FastAPI import failed: %s", e)

try:
    import uvicorn

    logger.info("Uvicorn imported successfully: %s", uvicorn.__version__)
except ImportError as e:
    logger.warning("Uvicorn import failed: %s", e)

logger.info("Starting simple HTTP server...")


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "healthy", "service": "test-tool-router"}')

    def log_message(self, fmt: str, *args: object) -> None:
        logger.info(fmt, *args)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8030"))
    host = os.environ.get("HOST", "127.0.0.1")

    logger.info("Starting simple HTTP server on %s:%d", host, port)

    server = HTTPServer((host, port), SimpleHandler)
    server.serve_forever()
