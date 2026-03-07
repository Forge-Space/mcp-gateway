"""Validate the OpenAPI schema is complete and well-formed."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture(scope="module")
def openapi_schema():
    from tool_router.http_server import app

    return app.openapi()


def test_schema_metadata(openapi_schema):
    assert openapi_schema["info"]["title"] == "Forge Space MCP Gateway"
    assert openapi_schema["openapi"].startswith("3.")


def test_minimum_paths(openapi_schema):
    paths = openapi_schema["paths"]
    assert len(paths) >= 15
    assert "/rpc" in paths
    assert "/rpc/stream" in paths
    assert "/" in paths
    assert "/health" in paths


def test_rpc_endpoint_has_description(openapi_schema):
    rpc = openapi_schema["paths"]["/rpc"]["post"]
    assert rpc.get("summary")
    assert rpc.get("description")
    assert "401" in rpc.get("responses", {})


def test_all_endpoints_have_summaries(openapi_schema):
    missing = []
    for path, methods in openapi_schema["paths"].items():
        for method, detail in methods.items():
            if not detail.get("summary"):
                missing.append(f"{method.upper()} {path}")
    assert not missing, f"Endpoints missing summaries: {missing}"


def test_schema_models_present(openapi_schema):
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    expected = [
        "JsonRpcRequest",
        "JsonRpcResponse",
        "JsonRpcError",
        "AuditEvent",
        "CacheMetricsResponse",
    ]
    for name in expected:
        assert name in schemas, f"Missing schema: {name}"


def test_json_rpc_request_has_examples(openapi_schema):
    schemas = openapi_schema["components"]["schemas"]
    rpc_req = schemas["JsonRpcRequest"]
    assert "examples" in rpc_req
    assert len(rpc_req["examples"]) >= 2
