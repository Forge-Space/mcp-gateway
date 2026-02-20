#!/usr/bin/env python3
"""Test HTTP server to debug container issues."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class TestHandler(BaseHTTPRequestHandler):
    """Handle test requests."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/test':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'tool-router-test',
                'timestamp': time.time()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests."""
        self.do_GET()
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass

def main():
    """Run the test HTTP server."""
    port = 8030
    server = HTTPServer(('0.0.0.0', port), TestHandler)
    print(f"Test server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    main()
