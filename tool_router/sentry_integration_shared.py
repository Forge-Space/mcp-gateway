"""
Enhanced Sentry Integration for mcp-gateway with Shared Logging
Integrates Sentry with Supabase and shared logging table
"""

import os
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import structlog
from sentry_sdk import configure_scope, add_breadcrumb, capture_exception, capture_message
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.structlog import StructlogIntegration

from shared_logger import (
    SharedLogger, SharedLoggerConfig, LogLevel, create_correlation_id,
    get_or_create_correlation_id, add_correlation_to_headers
)

# Global logger instance
shared_logger: Optional[SharedLogger] = None


def init_sentry(
    dsn: str,
    environment: str = "development",
    release: Optional[str] = None,
    sample_rate: float = 0.1,
    enable_supabase: bool = True,
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    service_name: str = "mcp-gateway",
    service_version: Optional[str] = None,
) -> bool:
    """
    Initialize Sentry with Supabase integration and shared logging
    """
    try:
        # Initialize shared logger first
        global shared_logger
        if enable_supabase and supabase_url and supabase_key:
            shared_logger_config = SharedLoggerConfig(
                service_name=service_name,
                service_version=service_version,
                environment=environment,
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                enable_sentry=True,
                sentry_dsn=dsn,
            )
            shared_logger = SharedLogger(shared_logger_config)

        # Configure Sentry integrations
        integrations = [
            FastApiIntegration(auto_enabling_integrations=False),
            SqlalchemyIntegration(),
            RedisIntegration(),
            StructlogIntegration(
                event_level_mapper="name",
                logger_name_mapper="name",
                extra_keys={
                    "request_id",
                    "correlation_id",
                    "user_id",
                    "service_name",
                },
            ),
        ]

        # Initialize Sentry
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            integrations=integrations,
            environment=environment,
            release=release or f"{service_name}@{service_version or 'unknown'}",
            sample_rate=sample_rate,
            traces_sample_rate=0.05,
            profiles_sample_rate=0.01,
            before_send=before_send_filter,
            before_send_transaction=before_send_transaction_filter,
            debug=environment == "development",
        )

        # Configure structlog with Sentry integration
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                add_service_context,
                add_correlation_context,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        logger = structlog.get_logger()
        logger.info("Sentry initialized successfully", service_name=service_name, environment=environment)
        
        return True

    except Exception as e:
        print(f"Failed to initialize Sentry: {e}")
        return False


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter events before sending to Sentry"""
    # Remove sensitive environment variables
    if "extra" in event and "environment" in event["extra"]:
        env = event["extra"]["environment"]
        sensitive_keys = ["SENTRY_DSN", "SUPABASE_URL", "SUPABASE_KEY", "JWT_SECRET"]
        for key in sensitive_keys:
            if key in env:
                del env[key]

    # Filter out expected errors
    if "exception" in event:
        exception = event["exception"].get("values", [{}])[0]
        if exception and "value" in exception:
            error_message = exception["value"]
            if should_skip_error(error_message):
                return None

    return event


def before_send_transaction_filter(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter transactions before sending to Sentry"""
    # Skip health check transactions
    if "transaction" in event:
        transaction = event["transaction"]
        if should_skip_transaction(transaction):
            return None

    return event


def should_skip_error(error_message: str) -> bool:
    """Determine if an error should be skipped"""
    skip_phrases = [
        "network error",
        "timeout occurred",
        "connection reset",
        "failed to fetch",
        "chunk load error",
        "loading chunk",
    ]
    return any(phrase in error_message.lower() for phrase in skip_phrases)


def should_skip_transaction(transaction_name: str) -> bool:
    """Determine if a transaction should be skipped"""
    skip_paths = [
        "/health",
        "/api/health",
        "/favicon.ico",
        "/robots.txt",
        "/sitemap.xml",
        "/_next/static",
    ]
    return any(path in transaction_name for path in skip_paths)


def add_service_context(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service context to all log entries"""
    event_dict["service_name"] = "mcp-gateway"
    event_dict["service_version"] = os.getenv("SERVICE_VERSION", "unknown")
    return event_dict


def add_correlation_context(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation context to log entries"""
    # Try to get correlation ID from current scope
    try:
        from sentry_sdk import get_current_span
        span = get_current_span()
        if span and span.trace_id:
            event_dict["trace_id"] = span.trace_id
            event_dict["span_id"] = span.span_id
    except Exception:
        pass

    return event_dict


def add_supabase_context(
    operation: str,
    table: Optional[str] = None,
    query: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """Add Supabase-specific context to Sentry"""
    configure_scope(
        lambda scope: scope.set_tag("database.operation", operation)
        .set_tag("database.provider", "supabase")
        .set_tag("database.type", "postgresql")
        .set_context(
            "supabase",
            {
                "operation": operation,
                "table": table,
                "user_id": user_id,
                "error_type": "database_error" if query else None,
            },
        )
    )

    if table:
        configure_scope(lambda scope: scope.set_tag("database.table", table))

    if query:
        sanitized_query = sanitize_query(query)
        configure_scope(lambda scope: scope.set_extra("database.query", sanitized_query))


def capture_supabase_error(
    error: Exception,
    operation: str,
    table: Optional[str] = None,
    query: Optional[str] = None,
) -> None:
    """Capture Supabase-specific errors with rich context"""
    add_supabase_context(operation, table, query)
    
    configure_scope(
        lambda scope: scope.set_tag("database.error", True)
        .set_context("supabase_error", {
            "operation": operation,
            "table": table,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
        })
    )

    capture_exception(error)


def sanitize_query(query: str) -> str:
    """Sanitize database queries to remove sensitive information"""
    if not query:
        return ""

    # Remove email addresses
    import re
    sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', query)

    # Remove API keys and tokens
    sanitized = re.sub(r'[A-Za-z0-9]{20,}', '[REDACTED]', sanitized)

    # Remove password patterns
    sanitized = re.sub(r"password\s*=\s*'[^']*'", "password='[REDACTED]'", sanitized, flags=re.IGNORECASE)

    return sanitized


def create_supabase_span(operation: str, table: Optional[str] = None) -> Any:
    """Create a Sentry span for Supabase operations"""
    try:
        from sentry_sdk import start_span
        span_name = f"supabase.{operation}"
        full_span_name = f"{span_name}.{table}" if table else span_name
        return start_span(full_span_name)
    except Exception:
        return None


async def monitor_mcp_request(
    tool_name: str,
    success: bool,
    duration: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Monitor MCP tool execution"""
    if shared_logger:
        await shared_logger.log_mcp_tool_execution(tool_name, success, duration, context)

    # Also send to Sentry
    configure_scope(
        lambda scope: scope.set_tag("mcp.tool_name", tool_name)
        .set_tag("mcp.success", success)
        .set_context("mcp", {
            "tool_name": tool_name,
            "success": success,
            "duration_ms": duration,
            **(context or {}),
        })
    )

    level = "info" if success else "error"
    add_breadcrumb(
        category="mcp",
        message=f"MCP tool: {tool_name}",
        level=level,
        data={
            "tool_name": tool_name,
            "success": success,
            "duration_ms": duration,
            **(context or {}),
        },
    )


async def monitor_service_lifecycle(
    event: str,
    success: bool,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Monitor service lifecycle events"""
    if shared_logger:
        await shared_logger.info(f"Service lifecycle: {event}", context)

    configure_scope(
        lambda scope: scope.set_tag("service.event", event)
        .set_tag("service.success", success)
        .set_context("service_lifecycle", {
            "event": event,
            "success": success,
            **(context or {}),
        })
    )

    level = "info" if success else "error"
    add_breadcrumb(
        category="service",
        message=f"Service lifecycle: {event}",
        level=level,
        data={
            "event": event,
            "success": success,
            **(context or {}),
        },
    )


@asynccontextmanager
async def correlation_context(correlation_id: Optional[str] = None):
    """Context manager for correlation ID tracking"""
    if not correlation_id:
        correlation_id = create_correlation_id()

    # Add correlation ID to Sentry scope
    configure_scope(lambda scope: scope.set_tag("correlation_id", correlation_id))

    # Add correlation ID to shared logger context
    if shared_logger:
        await shared_logger.debug("Starting correlation context", {"correlation_id": correlation_id})

    try:
        yield correlation_id
    finally:
        if shared_logger:
            await shared_logger.debug("Ending correlation context", {"correlation_id": correlation_id})


def get_correlation_id_from_request(request) -> str:
    """Extract or create correlation ID from FastAPI request"""
    headers = dict(request.headers)
    return get_or_create_correlation_id(headers)


def add_correlation_headers(response, correlation_id: str):
    """Add correlation ID to response headers"""
    response.headers["x-correlation-id"] = correlation_id
    return response


# Utility functions for shared logging
async def log_api_request(
    request_id: str,
    method: str,
    endpoint: str,
    status_code: int,
    duration: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Log API request to shared logger"""
    if shared_logger:
        await shared_logger.log_api_request(request_id, method, endpoint, status_code, duration, context)


async def log_database_operation(
    operation: str,
    table: str,
    success: bool,
    duration: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Log database operation to shared logger"""
    if shared_logger:
        await shared_logger.log_database_operation(operation, table, success, duration, context)


async def log_user_activity(
    user_id: str,
    session_id: str,
    action: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Log user activity to shared logger"""
    if shared_logger:
        await shared_logger.log_user_activity(user_id, session_id, action, context)


# Export the shared logger
def get_shared_logger_instance() -> Optional[SharedLogger]:
    """Get the shared logger instance"""
    return shared_logger
