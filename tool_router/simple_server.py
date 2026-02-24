import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


logger = logging.getLogger(__name__)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {"status": "healthy", "service": "tool-router"}
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, fmt: str, *args: object) -> None:
        logger.info(fmt, *args)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8030"))
    host = os.environ.get("HOST", "127.0.0.1")
    server = HTTPServer((host, port), Handler)
    logger.info("Starting server on %s:%d", host, port)
    server.serve_forever()
