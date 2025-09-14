"""
Models package for Qolaba MCP Server.

This package contains all Pydantic models used for API communication,
data validation, and serialization.
"""

from .api_models import (
    # Base models
    BaseQolabaRequest,
    BaseQolabaResponse,

    # Text-to-image models
    TextToImageRequest,
    ImageToImageRequest,

    # Image editing models
    InpaintingRequest,
    ReplaceBackgroundRequest,

    # Audio models
    TextToSpeechRequest,

    # Chat models
    ChatMessage,
    ChatRequest,
    StreamChatRequest,
    ChatResponse,

    # Vector database models
    VectorStoreRequest,

    # Task management models
    TaskStatusResponse,
    TaskCreatedResponse,

    # Basic error models
    QolabaAPIError,
    
    # Enhanced error models and constants
    ErrorCategory,
    ErrorSeverity,
    DetailedQolabaError,
    ValidationErrorDetail,
    BatchErrorResponse,
    
    # Exception classes
    QolabaException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    RateLimitException,
    NetworkException,
    TimeoutException,
    ProcessingException,

    # Basic utility functions
    validate_image_data,
    sanitize_filename,
    
    # Advanced data conversion and validation utilities
    convert_image_to_base64,
    validate_audio_format,
    convert_file_size_to_bytes,
    validate_color_value,
    normalize_model_name,
    validate_url_or_path,
    convert_duration_to_seconds,
    validate_json_schema,
    
    # Error handling and transformation utilities
    create_error_from_http_status,
    transform_validation_errors,
    create_batch_error_response,
    handle_api_error_response,
    format_error_for_logging,
    is_retryable_error,
    get_retry_delay,
)

__all__ = [
    "BaseQolabaRequest",
    "BaseQolabaResponse",
    "TextToImageRequest",
    "ImageToImageRequest",
    "InpaintingRequest",
    "ReplaceBackgroundRequest",
    "TextToSpeechRequest",
    "ChatMessage",
    "ChatRequest",
    "StreamChatRequest",
    "ChatResponse",
    "VectorStoreRequest",
    "TaskStatusResponse",
    "TaskCreatedResponse",
    "QolabaAPIError",
    "ErrorCategory",
    "ErrorSeverity",
    "DetailedQolabaError",
    "ValidationErrorDetail",
    "BatchErrorResponse",
    "QolabaException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "RateLimitException",
    "NetworkException",
    "TimeoutException",
    "ProcessingException",
    "validate_image_data",
    "sanitize_filename",
    "convert_image_to_base64",
    "validate_audio_format",
    "convert_file_size_to_bytes",
    "validate_color_value",
    "normalize_model_name",
    "validate_url_or_path",
    "convert_duration_to_seconds",
    "validate_json_schema",
    "create_error_from_http_status",
    "transform_validation_errors",
    "create_batch_error_response",
    "handle_api_error_response",
    "format_error_for_logging",
    "is_retryable_error",
    "get_retry_delay",
]