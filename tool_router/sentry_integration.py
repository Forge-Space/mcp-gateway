"""
Sentry integration for MCP Gateway with Supabase monitoring
Configures error tracking, performance monitoring, and database observability
"""

import os
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.structlog import StructlogIntegration


# Supabase monitoring integration
try:
    from supabase import Client as SupabaseClient  # noqa: F401

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


def init_sentry(
    dsn: str | None = None,
    environment: str | None = None,
    release: str | None = None,
    sample_rate: float = 0.1,
    enable_supabase: bool = True,
) -> None:
    """
    Initialize Sentry SDK with MCP Gateway and Supabase integrations

    Args:
        dsn: Sentry DSN URL
        environment: Environment name (development, staging, production)
        release: Release version
        sample_rate: Tracing sample rate for cost control
        enable_supabase: Enable Supabase-specific monitoring
    """

    # Get configuration from environment
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        print("⚠️  SENTRY_DSN not configured, skipping Sentry initialization")
        return

    # Configure integrations
    integrations = [
        # FastAPI integration for web endpoints
        FastApiIntegration(
            auto_enabling_integrations=False,
            transaction_style="endpoint",
        ),
        # Structured logging integration
        StructlogIntegration(
            event_level=logging.INFO,
            level=logging.INFO,
        ),
        # SQLAlchemy integration for database queries
        SqlalchemyIntegration(
            engine=None,
            service_name=None,
            capture_statement=True,
            capture_parameters=True,
        ),
        # Redis integration for caching
        RedisIntegration(
            service_name=None,
            capture_statement=True,
        ),
    ]

    # Add Supabase-specific monitoring if available
    if enable_supabase and SUPABASE_AVAILABLE:
        try:
            from sentry_sdk.integrations.supabase import SupabaseIntegration

            integrations.append(SupabaseIntegration())
        except ImportError:
            print("⚠️  Sentry Supabase integration not available")

    # Initialize Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=integrations,
        enable_logs=True,
        traces_sample_rate=sample_rate,
        profiles_sample_rate=sample_rate * 0.5,  # Lower sampling for profiling
        environment=environment or os.getenv("NODE_ENV", "development"),
        release=release or f"mcp-gateway@{get_version()}",
        # Performance and error settings
        max_breadcrumbs=100,
        before_send=before_send_filter,
        before_send_transaction=before_send_transaction_filter,
        # Debug settings for development
        debug=environment == "development",
        # Ignore specific errors that are expected in MCP operations
        ignore_errors=[
            "KeyboardInterrupt",
            "SystemExit",
            "ConnectionError",  # Expected in distributed systems
        ],
    )

    print(f"✅ Sentry initialized for environment: {environment or 'development'}")


def get_version() -> str:
    """Get the current version from pyproject.toml"""
    try:
        import tomllib

        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "unknown")
    except Exception:
        return "unknown"


def before_send_filter(
    event: dict[str, Any], hint: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Filter events before sending to Sentry
    Remove sensitive data and filter out expected errors
    """

    # Remove sensitive environment variables
    if "extra" in event and "environment" in event["extra"]:
        env = event["extra"]["environment"]
        sensitive_keys = ["SENTRY_DSN", "DATABASE_URL", "SUPABASE_KEY", "JWT_SECRET"]
        for key in sensitive_keys:
            env.pop(key, None)

    # Filter out expected MCP connection errors
    if "exception" in event:
        exception = event["exception"]["values"][0]
        error_message = exception.get("value", "")

        # Skip common MCP connection issues
        if any(
            skip_phrase in error_message.lower()
            for skip_phrase in [
                "connection refused",
                "timeout occurred",
                "connection reset",
                "broken pipe",
            ]
        ):
            return None

    return event


def before_send_transaction_filter(
    event: dict[str, Any], hint: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Filter transactions before sending to Sentry
    Remove high-volume, low-value transactions
    """

    # Skip health check transactions
    if "transaction" in event:
        transaction = event["transaction"]
        if any(
            skip_path in transaction
            for skip_path in [
                "/health",
                "/metrics",
                "/_health/",
                "/favicon.ico",
            ]
        ):
            return None

    return event


def add_supabase_context(supabase_client: Any) -> None:
    """
    Add Supabase-specific context to Sentry events

    Args:
        supabase_client: Supabase client instance
    """
    if not SUPABASE_AVAILABLE or not supabase_client:
        return

    try:
        # Add Supabase configuration as tags
        sentry_sdk.set_tag("supabase.project", supabase_client.supabase_url)
        sentry_sdk.set_tag("database.type", "supabase")

        # Add user context if authenticated
        # This would be implemented based on your auth system

    except Exception as e:
        print(f"⚠️  Failed to add Supabase context: {e}")


def capture_supabase_error(
    error: Exception,
    operation: str,
    table: str | None = None,
    query: str | None = None,
) -> None:
    """
    Capture Supabase-specific errors with rich context

    Args:
        error: The exception that occurred
        operation: The operation being performed (select, insert, update, delete)
        table: The table being accessed
        query: The query being executed (sanitized)
    """

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("database.operation", operation)
        scope.set_tag("database.provider", "supabase")

        if table:
            scope.set_tag("database.table", table)

        if query:
            # Sanitize query to remove sensitive data
            sanitized_query = sanitize_query(query)
            scope.set_extra("database.query", sanitized_query)

        scope.set_context(
            "supabase",
            {
                "operation": operation,
                "table": table,
                "error_type": type(error).__name__,
            },
        )

    sentry_sdk.capture_exception(error)


def sanitize_query(query: str) -> str:
    """
    Sanitize database queries to remove sensitive information

    Args:
        query: The raw SQL query

    Returns:
        Sanitized query string
    """

    # Remove common sensitive patterns
    import re

    # Remove email addresses
    query = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", query
    )

    # Remove API keys and tokens
    query = re.sub(r"[A-Za-z0-9]{20,}", "[REDACTED]", query)

    # Remove password patterns
    query = re.sub(
        r"password\s*=\s*\'[^\']*\'",
        "password='[REDACTED]'",
        query,
        flags=re.IGNORECASE,
    )

    return query


def create_supabase_span(operation: str, table: str = None) -> Any:
    """
    Create a Sentry span for Supabase operations

    Args:
        operation: The database operation
        table: The table being accessed

    Returns:
        Sentry span context manager
    """

    span_name = f"supabase.{operation}"
    if table:
        span_name += f".{table}"

    return sentry_sdk.start_span(span_name)


# MCP Gateway specific monitoring functions
def monitor_mcp_request(
    tool_name: str, server_name: str, execution_time: float
) -> None:
    """
    Monitor MCP tool execution with performance metrics

    Args:
        tool_name: Name of the MCP tool
        server_name: Name of the MCP server
        execution_time: Execution time in milliseconds
    """

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("mcp.tool_name", tool_name)
        scope.set_tag("mcp.server_name", server_name)
        scope.set_tag("mcp.operation", "tool_execution")

        scope.set_context(
            "mcp",
            {
                "tool_name": tool_name,
                "server_name": server_name,
                "execution_time_ms": execution_time,
            },
        )

    sentry_sdk.add_breadcrumb(
        category="mcp",
        message=f"Executed {tool_name} on {server_name}",
        level="info",
        data={
            "tool_name": tool_name,
            "server_name": server_name,
            "execution_time_ms": execution_time,
        },
    )


def monitor_service_lifecycle(service_name: str, action: str, success: bool) -> None:
    """
    Monitor service lifecycle events (start, stop, sleep, wake)

    Args:
        service_name: Name of the service
        action: The lifecycle action
        success: Whether the action was successful
    """

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("service.name", service_name)
        scope.set_tag("service.action", action)
        scope.set_tag("service.success", success)

        scope.set_context(
            "service",
            {
                "name": service_name,
                "action": action,
                "success": success,
            },
        )

    level = "error" if not success else "info"
    sentry_sdk.add_breadcrumb(
        category="service",
        message=f"Service {action}: {service_name}",
        level=level,
        data={
            "service_name": service_name,
            "action": action,
            "success": success,
        },
    )


# Initialize Sentry when this module is imported
if os.getenv("SENTRY_DSN"):
    init_sentry()
