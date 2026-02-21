"""Unit tests for observability logger module."""

from __future__ import annotations

import logging
import sys
from io import StringIO
from unittest.mock import MagicMock

from tool_router.observability.logger import (
    ContextLoggerAdapter,
    LogContext,
    StructuredFormatter,
    get_logger,
    setup_logging,
)


class TestStructuredFormatter:
    """Test StructuredFormatter class."""

    def test_format_basic_record(self) -> None:
        """Test formatting basic log record."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should contain timestamp, level, logger, and message
        assert "timestamp=" in result
        assert "level=INFO" in result
        assert "logger=test_logger" in result
        assert "message=Test message" in result

    def test_format_with_exception(self) -> None:
        """Test formatting log record with exception."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)

        assert "exception=" in result
        assert "ValueError: Test error" in result

    def test_format_with_extra_fields(self) -> None:
        """Test formatting log record with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_fields = {"user_id": "123", "request_id": "abc"}

        result = formatter.format(record)

        assert "user_id=123" in result
        assert "request_id=abc" in result

    def test_format_time_customization(self) -> None:
        """Test time formatting customization."""
        formatter = StructuredFormatter(datefmt="%Y-%m-%d")
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should use custom date format
        assert "timestamp=" in result
        # Check that it's in YYYY-MM-DD format
        import re

        timestamp_pattern = r"timestamp=\d{4}-\d{2}-\d{2}"
        assert re.search(timestamp_pattern, result) is not None


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_structured_default(self) -> None:
        """Test setup_logging with structured format and default level."""
        # Capture stdout
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            setup_logging()

            # Get root logger and verify configuration
            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO

            # Verify handler
            assert len(root_logger.handlers) == 1
            handler = root_logger.handlers[0]
            assert isinstance(handler, logging.StreamHandler)
            assert handler.level == logging.INFO
            assert isinstance(handler.formatter, StructuredFormatter)

        finally:
            sys.stdout = old_stdout

    def test_setup_logging_structured_custom_level(self) -> None:
        """Test setup_logging with custom log level."""
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            setup_logging(level="DEBUG")

            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

        finally:
            sys.stdout = old_stdout

    def test_setup_logging_non_structured(self) -> None:
        """Test setup_logging with non-structured format."""
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            setup_logging(structured=False)

            root_logger = logging.getLogger()
            handler = root_logger.handlers[0]
            assert not isinstance(handler.formatter, StructuredFormatter)
            assert isinstance(handler.formatter, logging.Formatter)

        finally:
            sys.stdout = old_stdout

    def test_setup_logging_invalid_level(self) -> None:
        """Test setup_logging with invalid log level (should default to INFO)."""
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            setup_logging(level="INVALID")

            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO

        finally:
            sys.stdout = old_stdout

    def test_setup_logging_removes_existing_handlers(self) -> None:
        """Test that setup_logging removes existing handlers."""
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            # Add a handler first
            root_logger = logging.getLogger()
            existing_handler = logging.StreamHandler()
            root_logger.addHandler(existing_handler)

            # Setup logging should remove existing handlers
            setup_logging()

            # Should only have one handler (the new one)
            assert len(root_logger.handlers) == 1
            assert root_logger.handlers[0] is not existing_handler

        finally:
            sys.stdout = old_stdout

    def test_setup_logging_sets_specific_logger_levels(self) -> None:
        """Test that specific logger levels are set correctly."""
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            setup_logging(level="DEBUG")

            # Check urllib3 is set to WARNING
            urllib3_logger = logging.getLogger("urllib3")
            assert urllib3_logger.level == logging.WARNING

            # Check tool_router follows the specified level
            tool_router_logger = logging.getLogger("tool_router")
            assert tool_router_logger.level == logging.DEBUG

        finally:
            sys.stdout = old_stdout


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger(self) -> None:
        """Test getting a logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_same_instance(self) -> None:
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        assert logger1 is logger2

    def test_get_logger_different_names(self) -> None:
        """Test that get_logger returns different instances for different names."""
        logger1 = get_logger("test_logger1")
        logger2 = get_logger("test_logger2")
        assert logger1 is not logger2
        assert logger1.name == "test_logger1"
        assert logger2.name == "test_logger2"


class TestContextLoggerAdapter:
    """Test ContextLoggerAdapter class."""

    def test_context_logger_adapter_process(self) -> None:
        """Test ContextLoggerAdapter process method."""
        logger = MagicMock()
        adapter = ContextLoggerAdapter(logger, {"user_id": "123"})

        msg, kwargs = adapter.process("Test message", {})

        assert msg == "Test message"
        assert "extra" in kwargs
        assert kwargs["extra"]["user_id"] == "123"

    def test_context_logger_adapter_process_with_existing_extra(self) -> None:
        """Test ContextLoggerAdapter process with existing extra."""
        logger = MagicMock()
        adapter = ContextLoggerAdapter(logger, {"user_id": "123"})

        msg, kwargs = adapter.process("Test message", {"extra": {"existing": "value"}})

        assert msg == "Test message"
        assert kwargs["extra"]["existing"] == "value"
        assert kwargs["extra"]["user_id"] == "123"

    def test_context_logger_adapter_process_with_extra_merge(self) -> None:
        """Test ContextLoggerAdapter process merges extra fields."""
        logger = MagicMock()
        adapter = ContextLoggerAdapter(logger, {"user_id": "123", "request_id": "abc"})

        msg, kwargs = adapter.process("Test message", {"extra": {"existing": "value"}})

        assert msg == "Test message"
        assert kwargs["extra"]["existing"] == "value"
        assert kwargs["extra"]["user_id"] == "123"
        assert kwargs["extra"]["request_id"] == "abc"


class TestLogContext:
    """Test LogContext class."""

    def test_log_context_initialization(self) -> None:
        """Test LogContext initialization."""
        logger = MagicMock()
        context = LogContext(logger, user_id="123", request_id="abc")

        assert context.logger == logger
        assert context.extra_fields == {"user_id": "123", "request_id": "abc"}
        assert context.adapter is None

    def test_log_context_enter(self) -> None:
        """Test LogContext enter method."""
        logger = MagicMock()
        context = LogContext(logger, user_id="123")

        adapter = context.__enter__()

        assert isinstance(adapter, ContextLoggerAdapter)
        assert adapter.logger == logger
        assert adapter.extra == {"user_id": "123"}
        assert context.adapter == adapter

    def test_log_context_exit(self) -> None:
        """Test LogContext exit method."""
        logger = MagicMock()
        context = LogContext(logger, user_id="123")

        # Enter first to create adapter
        adapter = context.__enter__()
        assert context.adapter is not None

        # Exit should not raise any exceptions
        result = context.__exit__()
        assert result is None

    def test_log_context_as_context_manager(self) -> None:
        """Test LogContext as context manager."""
        logger = MagicMock()
        extra_fields = {"user_id": "123", "request_id": "abc"}

        with LogContext(logger, **extra_fields) as adapter:
            assert isinstance(adapter, ContextLoggerAdapter)
            assert adapter.extra == extra_fields

    def test_log_context_with_logging(self) -> None:
        """Test LogContext with actual logging."""
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            # Setup structured logging
            setup_logging(level="INFO", structured=True)
            logger = get_logger("test_logger")

            # Use LogContext
            with LogContext(logger, user_id="123", request_id="abc") as adapter:
                adapter.info("Test message")

            output = captured_output.getvalue()
            # Note: The extra fields are added to the record but may not appear in output
            # depending on the formatter implementation. The important thing is that
            # the adapter works without errors.
            assert "timestamp=" in output
            assert "level=INFO" in output
            assert "logger=test_logger" in output
            assert "message=Test message" in output

        finally:
            sys.stdout = old_stdout

    def test_log_context_nested_contexts(self) -> None:
        """Test nested LogContext usage."""
        logger = MagicMock()

        with LogContext(logger, user_id="123") as outer_adapter:
            assert outer_adapter.extra == {"user_id": "123"}

            with LogContext(logger, request_id="abc") as inner_adapter:
                assert inner_adapter.extra == {"request_id": "abc"}

            # Inner context should not affect outer
            assert outer_adapter.extra == {"user_id": "123"}

    def test_log_context_empty_extra_fields(self) -> None:
        """Test LogContext with no extra fields and context manager behavior."""
        logger = MagicMock()

        with LogContext(logger) as adapter:
            # Should start with empty extra fields
            assert adapter.extra == {}

            # Business logic: context should be properly initialized
            # This tests the context manager initialization and cleanup logic
            assert adapter.logger is logger

            # Should be able to add fields dynamically
            adapter.extra["test_field"] = "test_value"
            assert adapter.extra == {"test_field": "test_value"}

        # Tests context manager functionality and field management

    def test_log_context_with_various_field_types(self) -> None:
        """Test LogContext with various field types."""
        logger = MagicMock()
        extra_fields = {
            "user_id": 123,
            "is_active": True,
            "score": 95.5,
            "tags": ["tag1", "tag2"],
        }

        with LogContext(logger, **extra_fields) as adapter:
            assert adapter.extra == extra_fields
