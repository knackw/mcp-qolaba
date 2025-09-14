"""
Comprehensive logging configuration for Qolaba MCP Server.

This module provides structured logging with JSON formatting, request tracing,
performance monitoring, and environment-specific configuration.
Features:
- Structured JSON logging for production
- Context-aware logging with request tracing  
- Performance logging for API calls
- Error logging with stack traces
- Log rotation and archiving
- Environment-specific configuration
"""

from __future__ import annotations

import json
import logging
import logging.config
import logging.handlers
import os
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, Tuple
from uuid import uuid4

from pythonjsonlogger import jsonlogger  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from pythonjsonlogger.jsonlogger import JsonFormatter as _JsonFormatter  # type: ignore[import-not-found]
else:
    try:
        from pythonjsonlogger.jsonlogger import JsonFormatter as _JsonFormatter  # type: ignore[import-not-found]
    except Exception:
        class _JsonFormatter(logging.Formatter):  # fallback if pythonjsonlogger is unavailable
            def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:  # type: ignore[override]
                pass
    
JsonFormatter = _JsonFormatter


# Context variables for request tracing
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
operation_var: ContextVar[Optional[str]] = ContextVar("operation", default=None)


class RequestContextFilter(logging.Filter):
    """Logging filter that adds request context to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context variables to log record."""
        record.request_id = request_id_var.get(None)
        record.user_id = user_id_var.get(None)
        record.operation = operation_var.get(None)
        record.timestamp = datetime.now(timezone.utc).isoformat()
        return True


class StructuredFormatter(JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = getattr(record, 'timestamp', datetime.now(timezone.utc).isoformat())
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add context fields
        log_record['request_id'] = getattr(record, 'request_id', None)
        log_record['user_id'] = getattr(record, 'user_id', None)
        log_record['operation'] = getattr(record, 'operation', None)
        
        # Add process info
        log_record['process_id'] = os.getpid()
        log_record['thread_name'] = record.threadName
        
        # Add exception details if present
        if record.exc_info and record.exc_info[0] is not None:
            exc_type, exc_value, exc_traceback = record.exc_info
            log_record['exception'] = {
                'type': exc_type.__name__ if exc_type else 'Unknown',
                'message': str(exc_value) if exc_value else '',
                'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback) if exc_traceback else []
            }


class LoggingConfig:
    """Central logging configuration manager."""
    
    def __init__(self, 
                 level: str = "INFO",
                 format_type: str = "structured",
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        self.level = level.upper()
        self.format_type = format_type
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Create logs directory if needed
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_console_formatter(self) -> logging.Formatter:
        """Get console formatter based on format type."""
        if self.format_type == "structured":
            return StructuredFormatter(
                fmt="%(timestamp)s %(level)s %(logger)s %(message)s"
            )
        else:
            return logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
    
    def get_file_formatter(self) -> logging.Formatter:
        """Get file formatter (always structured for production)."""
        return StructuredFormatter()
    
    def setup_logging(self) -> Dict[str, Any]:
        """Setup comprehensive logging configuration."""
        
        # Base configuration
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'console': {
                    '()': lambda: self.get_console_formatter()
                },
                'file': {
                    '()': lambda: self.get_file_formatter()
                }
            },
            'filters': {
                'context_filter': {
                    '()': RequestContextFilter
                }
            },
            'handlers': {
                'console': {
                    'level': self.level,
                    'class': 'logging.StreamHandler',
                    'formatter': 'console',
                    'filters': ['context_filter'],
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'qolaba_mcp_server': {
                    'level': self.level,
                    'handlers': ['console'],
                    'propagate': False
                },
                'httpx': {
                    'level': 'WARNING',
                    'handlers': ['console'],
                    'propagate': False
                },
                'uvicorn': {
                    'level': 'INFO',
                    'handlers': ['console'],
                    'propagate': False
                }
            },
            'root': {
                'level': 'WARNING',
                'handlers': ['console']
            }
        }
        
        # Add file handler if log file is specified
        if self.log_file:
            config['handlers']['file'] = {
                'level': self.level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'file',
                'filters': ['context_filter'],
                'filename': self.log_file,
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Add file handler to loggers
            for logger_name in ['qolaba_mcp_server', 'httpx', 'uvicorn']:
                config['loggers'][logger_name]['handlers'].append('file')
            config['root']['handlers'].append('file')
        
        return config


class LoggerFactory:
    """Factory for creating configured loggers."""
    
    _instance: Optional['LoggerFactory'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LoggerFactory':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_from_environment()
            self._initialized = True
    
    def _setup_from_environment(self):
        """Setup logging from environment variables."""
        level = os.getenv("FASTMCP_LOG_LEVEL", "INFO").upper()
        format_type = os.getenv("LOG_FORMAT_TYPE", "structured")
        log_file = os.getenv("LOG_FILE_PATH")
        
        # Development vs Production settings
        if os.getenv("FASTMCP_TEST_MODE") == "1":
            level = "DEBUG"
            format_type = "simple"
        
        config_manager = LoggingConfig(
            level=level,
            format_type=format_type,
            log_file=log_file
        )
        
        logging_config = config_manager.setup_logging()
        logging.config.dictConfig(logging_config)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a configured logger instance."""
        return logging.getLogger(name)
    
    def get_module_logger(self, module_name: str) -> logging.Logger:
        """Get logger for a specific module."""
        return self.get_logger(f"qolaba_mcp_server.{module_name}")


# Performance logging utilities
class PerformanceLogger:
    """Logger for performance monitoring and API call tracking."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_api_call(self,
                    endpoint: str,
                    method: str,
                    status_code: int,
                    response_time_ms: float,
                    request_size: int = 0,
                    response_size: int = 0,
                    error: Optional[str] = None) -> None:
        """Log API call performance metrics."""
        self.logger.info(
            "API call completed",
            extra={
                "event_type": "api_call",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "request_size_bytes": request_size,
                "response_size_bytes": response_size,
                "error": error,
                "success": status_code < 400 and error is None
            }
        )
    
    def log_operation_timing(self,
                           operation: str,
                           duration_ms: float,
                           success: bool = True,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log operation timing for performance analysis."""
        log_data = {
            "event_type": "operation_timing",
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success
        }
        
        if metadata:
            log_data.update(metadata)
        
        self.logger.info(f"Operation {operation} completed", extra=log_data)


# Request context management
class RequestContext:
    """Context manager for request-scoped logging."""
    
    def __init__(self, request_id: Optional[str] = None, 
                 user_id: Optional[str] = None,
                 operation: Optional[str] = None):
        self.request_id = request_id or str(uuid4())
        self.user_id = user_id
        self.operation = operation
        self._tokens = []
    
    def __enter__(self) -> "RequestContext":
        self._tokens.append(request_id_var.set(self.request_id))
        if self.user_id:
            self._tokens.append(user_id_var.set(self.user_id))
        if self.operation:
            self._tokens.append(operation_var.set(self.operation))
        return self
    
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        for token in reversed(self._tokens):
            token.var.reset(token)
        self._tokens.clear()


# Error logging utilities
class ErrorLogger:
    """Specialized logger for error handling and stack trace logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_exception(self,
                     exception: Exception,
                     context: Optional[Dict[str, Any]] = None,
                     user_message: Optional[str] = None) -> None:
        """Log exception with full context and stack trace."""
        error_data = {
            "event_type": "exception",
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "user_message": user_message
        }
        
        if context:
            error_data.update(context)
        
        self.logger.error(
            f"Exception occurred: {type(exception).__name__}",
            extra=error_data,
            exc_info=True
        )
    
    def log_validation_error(self,
                           field: str,
                           value: Any,
                           constraint: str,
                           user_message: Optional[str] = None) -> None:
        """Log validation error with field details."""
        self.logger.warning(
            f"Validation failed for field: {field}",
            extra={
                "event_type": "validation_error",
                "field": field,
                "value": str(value)[:100],  # Truncate long values
                "constraint": constraint,
                "user_message": user_message
            }
        )
    
    def log_http_error(self,
                      url: str,
                      method: str,
                      status_code: int,
                      response_text: Optional[str] = None,
                      request_id: Optional[str] = None) -> None:
        """Log HTTP error with request details."""
        self.logger.error(
            f"HTTP error {status_code} for {method} {url}",
            extra={
                "event_type": "http_error",
                "url": url,
                "method": method,
                "status_code": status_code,
                "response_text": response_text[:500] if response_text else None,
                "request_id": request_id
            }
        )


# Convenience functions for getting loggers
def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    factory = LoggerFactory()
    return factory.get_logger(name)


def get_module_logger(module_name: str) -> logging.Logger:
    """Get logger for a specific module."""
    factory = LoggerFactory()
    return factory.get_module_logger(module_name)


def get_performance_logger(module_name: str) -> PerformanceLogger:
    """Get performance logger for a module."""
    logger = get_module_logger(module_name)
    return PerformanceLogger(logger)


def get_error_logger(module_name: str) -> ErrorLogger:
    """Get error logger for a module."""
    logger = get_module_logger(module_name)
    return ErrorLogger(logger)


# Initialize logging on module import
factory = LoggerFactory()