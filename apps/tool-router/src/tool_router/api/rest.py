"""REST API handlers for virtual server lifecycle management.

Provides Flask and FastAPI integration examples for the lifecycle API.
"""

import os
from typing import Any

from flask import jsonify, request

from tool_router.api.lifecycle import (
    disable_server,
    enable_server,
    get_server_status,
    list_virtual_servers,
)


def handle_list_servers() -> tuple[dict[str, Any], int]:
    """Handle GET /api/virtual-servers request.

    Returns:
        Tuple of (response_dict, status_code)
    """
    try:
        result = list_virtual_servers()
        return result, 200
    except Exception as e:
        return {"error": str(e)}, 500


def handle_get_server(server_name: str) -> tuple[dict[str, Any], int]:
    """Handle GET /api/virtual-servers/{server_name} request.

    Args:
        server_name: Name of the server to retrieve

    Returns:
        Tuple of (response_dict, status_code)
    """
    try:
        result = get_server_status(server_name)
        if result.get("found"):
            return result, 200
        return result, 404
    except Exception as e:
        return {"error": str(e)}, 500


def handle_update_server(server_name: str, data: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Handle PATCH /api/virtual-servers/{server_name} request.

    Args:
        server_name: Name of the server to update
        data: Request body with 'enabled' field

    Returns:
        Tuple of (response_dict, status_code)
    """
    try:
        if "enabled" not in data:
            return {"error": "Missing 'enabled' field in request body"}, 400

        enabled = data["enabled"]
        if not isinstance(enabled, bool):
            return {"error": "'enabled' must be a boolean"}, 400

        result = enable_server(server_name) if enabled else disable_server(server_name)

        if result.get("success"):
            return result, 200
        return result, 404
    except Exception as e:
        return {"error": str(e)}, 500


# Flask integration example
def register_flask_routes(app: Any) -> None:
    """Register REST API routes with a Flask app.

    Args:
        app: Flask application instance

    Example:
        from flask import Flask
        from tool_router.api.rest import register_flask_routes

        app = Flask(__name__)
        register_flask_routes(app)
    """
    # Register feature toggle API blueprint
    from tool_router.api.features import features_bp

    app.register_blueprint(features_bp)

    @app.route("/api/virtual-servers", methods=["GET"])
    def list_servers_endpoint():
        result, status = handle_list_servers()
        return jsonify(result), status

    @app.route("/api/virtual-servers/<server_name>", methods=["GET"])
    def get_server_endpoint(server_name: str):
        result, status = handle_get_server(server_name)
        return jsonify(result), status

    @app.route("/api/virtual-servers/<server_name>", methods=["PATCH"])
    def update_server_endpoint(server_name: str):
        data = request.get_json() or {}
        result, status = handle_update_server(server_name, data)
        return jsonify(result), status


# FastAPI integration example
def register_fastapi_routes(app: Any) -> None:
    """Register REST API routes with a FastAPI app.

    Args:
        app: FastAPI application instance

    Example:
        from fastapi import FastAPI
        from tool_router.api.rest import register_fastapi_routes

        app = FastAPI()
        register_fastapi_routes(app)
    """
    from fastapi import Body
    from fastapi.responses import JSONResponse

    @app.get("/api/virtual-servers")
    async def list_servers_endpoint():
        result, status = handle_list_servers()
        return JSONResponse(content=result, status_code=status)

    @app.get("/api/virtual-servers/{server_name}")
    async def get_server_endpoint(server_name: str):
        result, status = handle_get_server(server_name)
        return JSONResponse(content=result, status_code=status)

    @app.patch("/api/virtual-servers/{server_name}")
    async def update_server_endpoint(server_name: str, data: dict[str, Any] = None):
        if data is None:
            data = Body(...)
        result, status = handle_update_server(server_name, data)
        return JSONResponse(content=result, status_code=status)


# Standalone WSGI application for testing
def create_wsgi_app() -> Any:
    """Create a standalone Flask WSGI application for testing.

    Returns:
        Flask application with REST API routes registered

    Example:
        from tool_router.api.rest import create_wsgi_app

        app = create_wsgi_app()
        app.run(host='0.0.0.0', port=5000)
    """
    try:
        from flask import Flask
        from flask_cors import CORS
    except ImportError:
        msg = "Flask and flask-cors required. Install with: pip install flask flask-cors"
        raise ImportError(msg) from None

    app = Flask(__name__)
    # CORS configuration: restrict origins in production
    # For development/testing, allows all origins. In production, set CORS_ORIGINS env var.
    cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    CORS(app, origins=cors_origins)
    register_flask_routes(app)

    return app


if __name__ == "__main__":
    # Run standalone REST API server for testing
    app = create_wsgi_app()
    # Bind to localhost for security; set FLASK_HOST env var to override
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    # Debug mode disabled by default; set FLASK_DEBUG=1 to enable in safe dev environments
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    if debug:
        pass
    app.run(host=host, port=5000, debug=debug)
