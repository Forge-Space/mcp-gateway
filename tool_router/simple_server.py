#!/usr/bin/env python3
"""Simple HTTP server for tool-router health checks."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class HealthHandler(BaseHTTPRequestHandler):
    """Handle health check requests."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'tool-router',
                'version': '1.0.0'
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/health':
            self.do_GET()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass

def main():
    """Run the simple HTTP server."""
    port = 8030
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Simple health server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    main()
