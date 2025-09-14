"""
Unit tests for the structured logging system.

This module tests the comprehensive logging configuration, context management,
performance logging, error logging, and integration functionality.
"""

import json
import logging
import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from qolaba_mcp_server.core.logging_config import (
    LoggerFactory,
    LoggingConfig,
    RequestContextFilter,
    StructuredFormatter,
    PerformanceLogger,
    ErrorLogger,
    RequestContext,
    get_logger,
    get_module_logger,
    get_performance_logger,
    get_error_logger,
    request_id_var,
    user_id_var,
    operation_var
)


class TestLoggingConfig:
    """Test LoggingConfig class functionality."""

    def test_logging_config_initialization(self):
        """Test LoggingConfig initialization with default values."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.format_type == "structured"
        assert config.log_file is None
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5

    def test_logging_config_custom_values(self):
        """Test LoggingConfig initialization with custom values."""
        config = LoggingConfig(
            level="DEBUG",
            format_type="simple",
            log_file="test.log",
            max_file_size=5 * 1024 * 1024,
            backup_count=3
        )
        
        assert config.level == "DEBUG"
        assert config.format_type == "simple"
        assert config.log_file == "test.log"
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.backup_count == 3

    def test_console_formatter_structured(self):
        """Test console formatter in structured mode."""
        config = LoggingConfig(format_type="structured")
        formatter = config.get_console_formatter()
        
        assert isinstance(formatter, StructuredFormatter)

    def test_console_formatter_simple(self):
        """Test console formatter in simple mode."""
        config = LoggingConfig(format_type="simple")
        formatter = config.get_console_formatter()
        
        assert isinstance(formatter, logging.Formatter)
        assert not isinstance(formatter, StructuredFormatter)

    def test_file_formatter_always_structured(self):
        """Test that file formatter is always structured."""
        config = LoggingConfig(format_type="simple")
        formatter = config.get_file_formatter()
        
        assert isinstance(formatter, StructuredFormatter)

    def test_setup_logging_console_only(self):
        """Test logging setup with console handler only."""
        config = LoggingConfig()
        logging_config = config.setup_logging()
        
        assert "console" in logging_config["handlers"]
        assert "file" not in logging_config["handlers"]
        assert "qolaba_mcp_server" in logging_config["loggers"]

    def test_setup_logging_with_file(self):
        """Test logging setup with file handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            config = LoggingConfig(log_file=tmp_file.name)
            logging_config = config.setup_logging()
            
            assert "console" in logging_config["handlers"]
            assert "file" in logging_config["handlers"]
            assert logging_config["handlers"]["file"]["filename"] == tmp_file.name
            
            # Cleanup
            os.unlink(tmp_file.name)


class TestRequestContextFilter:
    """Test RequestContextFilter functionality."""

    def test_filter_adds_context_variables(self):
        """Test that filter adds context variables to log record."""
        filter_obj = RequestContextFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        # Set context variables
        request_id = str(uuid4())
        user_id = "test_user"
        operation = "test_operation"
        
        request_id_var.set(request_id)
        user_id_var.set(user_id)
        operation_var.set(operation)
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert hasattr(record, 'request_id')
        assert hasattr(record, 'user_id')
        assert hasattr(record, 'operation')
        assert hasattr(record, 'timestamp')
        assert record.request_id == request_id
        assert record.user_id == user_id
        assert record.operation == operation

    def test_filter_with_no_context(self):
        """Test filter behavior with no context variables set."""
        # Explicitly clear any existing context from previous tests
        request_id_var.set(None)
        user_id_var.set(None)
        operation_var.set(None)

        filter_obj = RequestContextFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )

        result = filter_obj.filter(record)

        assert result is True
        assert record.request_id is None
        assert record.user_id is None
        assert record.operation is None


class TestStructuredFormatter:
    """Test StructuredFormatter functionality."""

    def test_structured_formatter_basic_fields(self):
        """Test that structured formatter adds basic fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger", level=logging.INFO, pathname="test.py", lineno=42,
            msg="test message", args=(), exc_info=None, func="test_function"
        )
        
        # Add context fields
        record.request_id = "test_request"
        record.user_id = "test_user"
        record.operation = "test_operation"
        record.timestamp = "2024-01-01T00:00:00Z"
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["module"] == "test"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert log_data["request_id"] == "test_request"
        assert log_data["user_id"] == "test_user"
        assert log_data["operation"] == "test_operation"
        assert "process_id" in log_data
        assert "thread_name" in log_data

    def test_structured_formatter_with_exception(self):
        """Test structured formatter with exception information."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test_logger", level=logging.ERROR, pathname="test.py", lineno=42,
                msg="test message", args=(), exc_info=sys.exc_info(), func="test_function"
            )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test exception"
        assert isinstance(log_data["exception"]["traceback"], list)


class TestLoggerFactory:
    """Test LoggerFactory functionality."""

    def test_logger_factory_singleton(self):
        """Test that LoggerFactory is a singleton."""
        factory1 = LoggerFactory()
        factory2 = LoggerFactory()
        
        assert factory1 is factory2

    def test_get_logger(self):
        """Test getting a logger instance."""
        factory = LoggerFactory()
        logger = factory.get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_module_logger(self):
        """Test getting a module logger."""
        factory = LoggerFactory()
        logger = factory.get_module_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "qolaba_mcp_server.test_module"

    @patch.dict(os.environ, {"FASTMCP_LOG_LEVEL": "DEBUG", "FASTMCP_TEST_MODE": "1"})
    def test_environment_configuration(self):
        """Test logger factory configuration from environment."""
        # Reset singleton to test environment configuration
        LoggerFactory._instance = None
        LoggerFactory._initialized = False
        
        factory = LoggerFactory()
        
        # Verify that environment variables are respected
        # This is more of an integration test to ensure the setup works
        assert factory._initialized is True


class TestPerformanceLogger:
    """Test PerformanceLogger functionality."""

    def test_performance_logger_initialization(self):
        """Test PerformanceLogger initialization."""
        mock_logger = MagicMock()
        perf_logger = PerformanceLogger(mock_logger)
        
        assert perf_logger.logger == mock_logger

    def test_log_api_call(self):
        """Test logging API call performance metrics."""
        mock_logger = MagicMock()
        perf_logger = PerformanceLogger(mock_logger)
        
        perf_logger.log_api_call(
            endpoint="/test",
            method="POST",
            status_code=200,
            response_time_ms=150.5,
            request_size=1024,
            response_size=2048,
            error=None
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        assert "API call completed" in call_args[0][0]
        extra_data = call_args[1]["extra"]
        assert extra_data["event_type"] == "api_call"
        assert extra_data["endpoint"] == "/test"
        assert extra_data["method"] == "POST"
        assert extra_data["status_code"] == 200
        assert extra_data["response_time_ms"] == 150.5
        assert extra_data["success"] is True

    def test_log_api_call_with_error(self):
        """Test logging failed API call."""
        mock_logger = MagicMock()
        perf_logger = PerformanceLogger(mock_logger)
        
        perf_logger.log_api_call(
            endpoint="/test",
            method="POST",
            status_code=500,
            response_time_ms=1000.0,
            error="Server Error"
        )
        
        call_args = mock_logger.info.call_args
        extra_data = call_args[1]["extra"]
        assert extra_data["success"] is False
        assert extra_data["error"] == "Server Error"

    def test_log_operation_timing(self):
        """Test logging operation timing."""
        mock_logger = MagicMock()
        perf_logger = PerformanceLogger(mock_logger)
        
        perf_logger.log_operation_timing(
            operation="test_operation",
            duration_ms=250.0,
            success=True,
            metadata={"request_count": 5}
        )
        
        call_args = mock_logger.info.call_args
        extra_data = call_args[1]["extra"]
        assert extra_data["event_type"] == "operation_timing"
        assert extra_data["operation"] == "test_operation"
        assert extra_data["duration_ms"] == 250.0
        assert extra_data["success"] is True
        assert extra_data["request_count"] == 5


class TestErrorLogger:
    """Test ErrorLogger functionality."""

    def test_error_logger_initialization(self):
        """Test ErrorLogger initialization."""
        mock_logger = MagicMock()
        error_logger = ErrorLogger(mock_logger)
        
        assert error_logger.logger == mock_logger

    def test_log_exception(self):
        """Test logging exception with context."""
        mock_logger = MagicMock()
        error_logger = ErrorLogger(mock_logger)
        
        test_exception = ValueError("Test error")
        context = {"operation": "test_op", "request_id": "123"}
        
        error_logger.log_exception(
            exception=test_exception,
            context=context,
            user_message="A test error occurred"
        )
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        assert "Exception occurred: ValueError" in call_args[0][0]
        extra_data = call_args[1]["extra"]
        assert extra_data["event_type"] == "exception"
        assert extra_data["exception_type"] == "ValueError"
        assert extra_data["exception_message"] == "Test error"
        assert extra_data["user_message"] == "A test error occurred"
        assert extra_data["operation"] == "test_op"
        assert extra_data["request_id"] == "123"
        assert call_args[1]["exc_info"] is True

    def test_log_validation_error(self):
        """Test logging validation error."""
        mock_logger = MagicMock()
        error_logger = ErrorLogger(mock_logger)
        
        error_logger.log_validation_error(
            field="email",
            value="invalid-email",
            constraint="email_format",
            user_message="Invalid email format"
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        assert "Validation failed for field: email" in call_args[0][0]
        extra_data = call_args[1]["extra"]
        assert extra_data["event_type"] == "validation_error"
        assert extra_data["field"] == "email"
        assert extra_data["value"] == "invalid-email"
        assert extra_data["constraint"] == "email_format"

    def test_log_http_error(self):
        """Test logging HTTP error."""
        mock_logger = MagicMock()
        error_logger = ErrorLogger(mock_logger)
        
        error_logger.log_http_error(
            url="https://api.example.com/test",
            method="POST",
            status_code=404,
            response_text="Not Found",
            request_id="req_123"
        )
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        assert "HTTP error 404 for POST" in call_args[0][0]
        extra_data = call_args[1]["extra"]
        assert extra_data["event_type"] == "http_error"
        assert extra_data["url"] == "https://api.example.com/test"
        assert extra_data["method"] == "POST"
        assert extra_data["status_code"] == 404
        assert extra_data["response_text"] == "Not Found"
        assert extra_data["request_id"] == "req_123"


class TestRequestContext:
    """Test RequestContext functionality."""

    def test_request_context_manager(self):
        """Test RequestContext as context manager."""
        request_id = str(uuid4())
        user_id = "test_user"
        operation = "test_operation"
        
        with RequestContext(request_id=request_id, user_id=user_id, operation=operation):
            assert request_id_var.get() == request_id
            assert user_id_var.get() == user_id
            assert operation_var.get() == operation
        
        # Context should be cleared after exiting
        assert request_id_var.get() is None
        assert user_id_var.get() is None
        assert operation_var.get() is None

    def test_request_context_auto_generate_id(self):
        """Test RequestContext auto-generates request ID if not provided."""
        with RequestContext() as ctx:
            assert ctx.request_id is not None
            assert len(ctx.request_id) > 0
            assert request_id_var.get() == ctx.request_id

    def test_request_context_partial_data(self):
        """Test RequestContext with partial context data."""
        request_id = str(uuid4())
        
        with RequestContext(request_id=request_id, operation="test_op"):
            assert request_id_var.get() == request_id
            assert user_id_var.get() is None
            assert operation_var.get() == "test_op"


class TestConvenienceFunctions:
    """Test convenience functions for getting loggers."""

    def test_get_logger_function(self):
        """Test get_logger convenience function."""
        logger = get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_module_logger_function(self):
        """Test get_module_logger convenience function."""
        logger = get_module_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "qolaba_mcp_server.test_module"

    def test_get_performance_logger_function(self):
        """Test get_performance_logger convenience function."""
        perf_logger = get_performance_logger("test_module")
        
        assert isinstance(perf_logger, PerformanceLogger)
        assert isinstance(perf_logger.logger, logging.Logger)

    def test_get_error_logger_function(self):
        """Test get_error_logger convenience function."""
        error_logger = get_error_logger("test_module")
        
        assert isinstance(error_logger, ErrorLogger)
        assert isinstance(error_logger.logger, logging.Logger)


class TestLoggingIntegration:
    """Integration tests for the complete logging system."""

    def test_full_logging_workflow(self):
        """Test complete logging workflow with context and formatting."""
        # Create a string buffer to capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())
        handler.addFilter(RequestContextFilter())
        
        # Create and configure logger
        test_logger = logging.getLogger("test_integration")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(handler)
        
        request_id = str(uuid4())
        
        # Test logging with context
        with RequestContext(request_id=request_id, operation="integration_test"):
            test_logger.info("Test message", extra={"custom_field": "custom_value"})
        
        # Parse the logged output
        log_output = log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["message"] == "Test message"
        assert log_data["request_id"] == request_id
        assert log_data["operation"] == "integration_test"
        assert log_data["custom_field"] == "custom_value"
        assert log_data["level"] == "INFO"

    @patch.dict(os.environ, {"LOG_FILE_PATH": ""})
    def test_environment_based_configuration(self):
        """Test that logging respects environment configuration."""
        # This test ensures environment variables are properly used
        # Reset singleton for clean test
        LoggerFactory._instance = None
        LoggerFactory._initialized = False
        
        factory = LoggerFactory()
        logger = factory.get_logger("env_test")
        
        assert isinstance(logger, logging.Logger)
        assert factory._initialized is True