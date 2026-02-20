"""Structured logging configuration for tool router."""

import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured fields."""
        # Base fields
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Format as key=value pairs for easy parsing
        parts = [f"{k}={v}" for k, v in log_data.items()]
        return " ".join(parts)


def setup_logging(level: str = "INFO", structured: bool = True) -> None:
    """Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Use structured logging format if True
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set formatter
    if structured:
        formatter = StructuredFormatter(fmt="%(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("tool_router").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class ContextLoggerAdapter(logging.LoggerAdapter):
    """Thread-safe logger adapter for adding contextual fields."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Add extra fields to log record."""
        # Merge extra fields into the log record
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs


class LogContext:
    """Context manager for adding extra fields to log records (thread-safe)."""

    def __init__(self, logger: logging.Logger, **extra_fields: Any) -> None:
        """Initialize log context.

        Args:
            logger: Logger to add context to
            **extra_fields: Additional fields to include in logs
        """
        self.logger = logger
        self.extra_fields = extra_fields
        self.adapter: ContextLoggerAdapter | None = None

    def __enter__(self) -> ContextLoggerAdapter:
        """Enter context and return logger adapter with extra fields."""
        self.adapter = ContextLoggerAdapter(self.logger, self.extra_fields)
        return self.adapter

    def __exit__(self, *args: Any) -> None:
        """Exit context (no cleanup needed for adapter approach)."""
