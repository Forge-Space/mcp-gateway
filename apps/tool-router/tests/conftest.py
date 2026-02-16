"""Shared pytest fixtures for tool-router tests."""

import pytest
from flask import Flask

from tool_router.api.features import features_bp


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.register_blueprint(features_bp)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
