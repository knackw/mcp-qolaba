"""
Pydantic models for Qolaba API requests and responses.

This module defines the data models used for API communication with the Qolaba platform.
All models include validation and serialization capabilities through Pydantic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class BaseQolabaRequest(BaseModel):
    """Base class for all Qolaba API requests."""

    class Config:
        extra = "forbid"  # Prevent additional fields
        validate_assignment = True


class BaseQolabaResponse(BaseModel):
    """Base class for all Qolaba API responses."""

    task_id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# =============================================================================
# Text-to-Image Models
# =============================================================================

class TextToImageRequest(BaseQolabaRequest):
    """Request model for text-to-image generation."""

    prompt: str = Field(..., description="Text description of the image to generate")
    model: str = Field(default="flux", description="Model to use for generation")
    width: int = Field(default=512, ge=64, le=2048, description="Image width in pixels")
    height: int = Field(default=512, ge=64, le=2048, description="Image height in pixels")
    steps: int = Field(default=20, ge=1, le=100, description="Number of inference steps")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Guidance scale")
    seed: Optional[int] = Field(None, ge=0, description="Random seed for reproducibility")
    negative_prompt: Optional[str] = Field(None, description="What to avoid in the image")

    @validator("prompt")
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        if len(v) > 1000:
            raise ValueError("Prompt too long (max 1000 characters)")
        return v.strip()


class ImageToImageRequest(BaseQolabaRequest):
    """Request model for image-to-image transformation."""

    image: str = Field(..., description="Source image URL or base64 data")
    prompt: str = Field(..., description="Text description of desired transformation")
    model: str = Field(default="flux", description="Model to use for transformation")
    strength: float = Field(default=0.8, ge=0.0, le=1.0, description="Transformation strength")
    steps: int = Field(default=20, ge=1, le=100, description="Number of inference steps")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Guidance scale")
    seed: Optional[int] = Field(None, ge=0, description="Random seed for reproducibility")

    @validator("prompt")
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


# =============================================================================
# Image Editing Models
# =============================================================================

class InpaintingRequest(BaseQolabaRequest):
    """Request model for image inpainting."""

    image: str = Field(..., description="Source image URL or base64 data")
    mask: str = Field(..., description="Mask image URL or base64 data")
    prompt: str = Field(..., description="Text description of what to paint")
    model: str = Field(default="flux", description="Model to use for inpainting")
    steps: int = Field(default=20, ge=1, le=100, description="Number of inference steps")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Guidance scale")
    seed: Optional[int] = Field(None, ge=0, description="Random seed for reproducibility")


class ReplaceBackgroundRequest(BaseQolabaRequest):
    """Request model for background replacement."""

    image: str = Field(..., description="Source image URL or base64 data")
    prompt: str = Field(..., description="Text description of new background")
    model: str = Field(default="flux", description="Model to use for background replacement")
    steps: int = Field(default=20, ge=1, le=100, description="Number of inference steps")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Guidance scale")
    seed: Optional[int] = Field(None, ge=0, description="Random seed for reproducibility")


# =============================================================================
# Audio Models
# =============================================================================

class TextToSpeechRequest(BaseQolabaRequest):
    """Request model for text-to-speech synthesis."""

    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="alloy", description="Voice to use")
    model: str = Field(default="tts-1", description="TTS model to use")
    response_format: str = Field(default="mp3", description="Audio format")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed")

    @validator("text")
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v) > 4000:
            raise ValueError("Text too long (max 4000 characters)")
        return v.strip()

    @validator("voice")
    def validate_voice(cls, v: str) -> str:
        allowed_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if v not in allowed_voices:
            raise ValueError(f"Voice must be one of: {', '.join(allowed_voices)}")
        return v

    @validator("response_format")
    def validate_format(cls, v: str) -> str:
        allowed_formats = ["mp3", "opus", "aac", "flac"]
        if v not in allowed_formats:
            raise ValueError(f"Format must be one of: {', '.join(allowed_formats)}")
        return v


# =============================================================================
# Chat Models
# =============================================================================

class ChatMessage(BaseModel):
    """A single chat message."""

    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")

    @validator("role")
    def validate_role(cls, v: str) -> str:
        allowed_roles = ["system", "user", "assistant"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class ChatRequest(BaseQolabaRequest):
    """Request model for chat completion."""

    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: str = Field(default="gpt-4", description="Chat model to use")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Maximum response tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response creativity")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Presence penalty")

    @validator("messages")
    def validate_messages(cls, v: List["ChatMessage"]) -> List["ChatMessage"]:
        if not v:
            raise ValueError("Messages cannot be empty")
        if len(v) > 50:
            raise ValueError("Too many messages (max 50)")
        return v


class StreamChatRequest(ChatRequest):
    """Request model for streaming chat completion."""

    stream: bool = Field(default=True, description="Enable streaming")


# =============================================================================
# Vector Database Models
# =============================================================================

class VectorStoreRequest(BaseQolabaRequest):
    """Request model for storing files in vector database."""

    file: str = Field(..., description="File URL or path to store")
    collection_name: str = Field(..., description="Vector collection name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")
    chunk_size: int = Field(default=1000, ge=100, le=4000, description="Text chunk size")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Chunk overlap")

    @validator("collection_name")
    def validate_collection_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Collection name cannot be empty")
        # Collection names should be alphanumeric with underscores/hyphens
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Collection name can only contain letters, numbers, underscores, and hyphens")
        return v.strip()

    @validator("chunk_overlap")
    def validate_chunk_overlap(cls, v: int, values: Dict[str, Any]) -> int:
        if "chunk_size" in values and v >= values["chunk_size"]:
            raise ValueError("Chunk overlap must be less than chunk size")
        return v


# =============================================================================
# Task Status Models
# =============================================================================

class TaskStatusResponse(BaseQolabaResponse):
    """Response model for task status queries."""

    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Task status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")

    @validator("status")
    def validate_status(cls, v: str) -> str:
        allowed_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


# =============================================================================
# Error Models and Exception Handling
# =============================================================================

class QolabaAPIError(BaseModel):
    """Model for API error responses."""

    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier for support")


# Enhanced Error Models with Categorization

class ErrorCategory:
    """Constants for error categories."""
    
    VALIDATION = "validation"
    AUTHENTICATION = "authentication" 
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    NETWORK = "network"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    PROCESSING = "processing"


class ErrorSeverity:
    """Constants for error severity levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetailedQolabaError(BaseModel):
    """Enhanced error model with categorization and metadata."""
    
    error_code: str = Field(..., description="Unique error code")
    message: str = Field(..., description="Human-readable error message")
    category: str = Field(..., description="Error category")
    severity: str = Field(default=ErrorSeverity.MEDIUM, description="Error severity level")
    http_status: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier for support")
    timestamp: Optional[str] = Field(None, description="Error occurrence timestamp")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")
    documentation_url: Optional[str] = Field(None, description="Link to error documentation")
    
    @validator("category")
    def validate_category(cls, v):
        allowed_categories = [
            ErrorCategory.VALIDATION,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION, 
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.API_ERROR,
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.SERVER_ERROR,
            ErrorCategory.CLIENT_ERROR,
            ErrorCategory.PROCESSING
        ]
        if v not in allowed_categories:
            raise ValueError(f"Category must be one of: {', '.join(allowed_categories)}")
        return v
    
    @validator("severity")
    def validate_severity(cls, v):
        allowed_severities = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        if v not in allowed_severities:
            raise ValueError(f"Severity must be one of: {', '.join(allowed_severities)}")
        return v
    
    @validator("http_status")
    def validate_http_status(cls, v):
        if not (100 <= v <= 599):
            raise ValueError("HTTP status must be between 100 and 599")
        return v


class ValidationErrorDetail(BaseModel):
    """Model for validation error details."""
    
    field: str = Field(..., description="Field that failed validation")
    value: Any = Field(..., description="Invalid value")
    constraint: str = Field(..., description="Validation constraint that was violated")
    message: str = Field(..., description="Validation error message")


class BatchErrorResponse(BaseModel):
    """Model for batch operation errors."""
    
    total_items: int = Field(..., description="Total number of items processed")
    successful_items: int = Field(..., description="Number of successfully processed items")
    failed_items: int = Field(..., description="Number of failed items")
    errors: List[DetailedQolabaError] = Field(..., description="List of errors that occurred")
    partial_success: bool = Field(..., description="Whether operation was partially successful")


# Custom Exception Classes

class QolabaException(Exception):
    """Base exception class for Qolaba API errors."""
    
    def __init__(self, message: str, error_code: str = None, category: str = None, 
                 severity: str = ErrorSeverity.MEDIUM, http_status: int = 500, 
                 details: Dict[str, Any] = None, request_id: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.category = category or ErrorCategory.API_ERROR
        self.severity = severity
        self.http_status = http_status
        self.details = details or {}
        self.request_id = request_id
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category,
            "severity": self.severity,
            "http_status": self.http_status,
            "details": self.details,
            "request_id": self.request_id
        }
        
    def to_detailed_error(self) -> DetailedQolabaError:
        """Convert exception to DetailedQolabaError model."""
        from datetime import datetime
        return DetailedQolabaError(
            error_code=self.error_code,
            message=self.message,
            category=self.category,
            severity=self.severity,
            http_status=self.http_status,
            details=self.details,
            request_id=self.request_id,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )


class ValidationException(QolabaException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None, 
                 constraint: str = None, error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            http_status=400
        )
        self.field = field
        self.value = value
        self.constraint = constraint
        
        if field:
            self.details.update({
                "field": field,
                "value": value,
                "constraint": constraint
            })


class AuthenticationException(QolabaException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", 
                 error_code: str = "AUTH_FAILED"):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            http_status=401
        )


class AuthorizationException(QolabaException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Access denied", 
                 error_code: str = "ACCESS_DENIED"):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            http_status=403
        )


class RateLimitException(QolabaException):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", 
                 retry_after: int = None, error_code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            http_status=429
        )
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class NetworkException(QolabaException):
    """Exception for network-related errors."""
    
    def __init__(self, message: str, error_code: str = "NETWORK_ERROR"):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            http_status=503
        )


class TimeoutException(QolabaException):
    """Exception for timeout errors."""
    
    def __init__(self, message: str = "Request timeout", 
                 timeout_duration: float = None, error_code: str = "TIMEOUT"):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            http_status=408
        )
        if timeout_duration:
            self.details["timeout_duration"] = timeout_duration


class ProcessingException(QolabaException):
    """Exception for processing errors."""
    
    def __init__(self, message: str, task_id: str = None, 
                 error_code: str = "PROCESSING_ERROR"):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            http_status=422
        )
        if task_id:
            self.details["task_id"] = task_id


# =============================================================================
# Error Transformation and Utility Functions
# =============================================================================

def create_error_from_http_status(status_code: int, message: str = None, 
                                details: Dict[str, Any] = None) -> QolabaException:
    """
    Create appropriate exception based on HTTP status code.
    
    Args:
        status_code: HTTP status code
        message: Optional error message
        details: Optional error details
        
    Returns:
        Appropriate QolabaException subclass
    """
    details = details or {}
    
    if status_code == 400:
        return ValidationException(
            message=message or "Bad request - invalid input"
        )
    elif status_code == 401:
        return AuthenticationException(
            message=message or "Authentication required"
        )
    elif status_code == 403:
        return AuthorizationException(
            message=message or "Access forbidden"
        )
    elif status_code == 408:
        return TimeoutException(
            message=message or "Request timeout",
            timeout_duration=details.get("timeout_duration")
        )
    elif status_code == 422:
        return ProcessingException(
            message=message or "Processing error",
            task_id=details.get("task_id")
        )
    elif status_code == 429:
        return RateLimitException(
            message=message or "Rate limit exceeded",
            retry_after=details.get("retry_after")
        )
    elif 500 <= status_code < 600:
        return QolabaException(
            message=message or "Internal server error",
            category=ErrorCategory.SERVER_ERROR,
            severity=ErrorSeverity.HIGH,
            http_status=status_code,
            details=details
        )
    else:
        return QolabaException(
            message=message or f"HTTP error {status_code}",
            category=ErrorCategory.API_ERROR,
            http_status=status_code,
            details=details
        )


def transform_validation_errors(errors: List[Dict[str, Any]]) -> List[ValidationErrorDetail]:
    """
    Transform validation errors into structured format.
    
    Args:
        errors: List of validation error dictionaries
        
    Returns:
        List of ValidationErrorDetail objects
    """
    transformed_errors = []
    
    for error in errors:
        if isinstance(error, dict):
            transformed_errors.append(ValidationErrorDetail(
                field=error.get("field", "unknown"),
                value=error.get("value"),
                constraint=error.get("constraint", "validation_failed"),
                message=error.get("message", "Validation failed")
            ))
    
    return transformed_errors


def create_batch_error_response(total: int, errors: List[QolabaException]) -> BatchErrorResponse:
    """
    Create batch error response from list of exceptions.
    
    Args:
        total: Total number of items processed
        errors: List of exceptions that occurred
        
    Returns:
        BatchErrorResponse object
    """
    failed_count = len(errors)
    successful_count = total - failed_count
    
    detailed_errors = [error.to_detailed_error() for error in errors]
    
    return BatchErrorResponse(
        total_items=total,
        successful_items=successful_count,
        failed_items=failed_count,
        errors=detailed_errors,
        partial_success=successful_count > 0
    )


def handle_api_error_response(response_data: Dict[str, Any], status_code: int) -> QolabaException:
    """
    Convert API error response to appropriate exception.
    
    Args:
        response_data: Error response data from API
        status_code: HTTP status code
        
    Returns:
        Appropriate QolabaException subclass
    """
    error_code = response_data.get("error_code", "API_ERROR")
    message = response_data.get("message", "An error occurred")
    details = response_data.get("details", {})
    request_id = response_data.get("request_id")
    
    # Create exception based on error code patterns
    if "validation" in error_code.lower():
        return ValidationException(
            message=message,
            error_code=error_code,
            **details
        )
    elif "auth" in error_code.lower():
        if "forbidden" in error_code.lower() or "access" in error_code.lower():
            return AuthorizationException(message=message, error_code=error_code)
        else:
            return AuthenticationException(message=message, error_code=error_code)
    elif "rate" in error_code.lower() or "limit" in error_code.lower():
        return RateLimitException(
            message=message,
            error_code=error_code,
            retry_after=details.get("retry_after")
        )
    elif "timeout" in error_code.lower():
        return TimeoutException(
            message=message,
            error_code=error_code,
            timeout_duration=details.get("timeout_duration")
        )
    elif "network" in error_code.lower() or "connection" in error_code.lower():
        return NetworkException(message=message, error_code=error_code)
    elif "processing" in error_code.lower() or "task" in error_code.lower():
        return ProcessingException(
            message=message,
            error_code=error_code,
            task_id=details.get("task_id")
        )
    else:
        return create_error_from_http_status(status_code, message, details)


def format_error_for_logging(error: QolabaException) -> Dict[str, Any]:
    """
    Format error for structured logging.
    
    Args:
        error: QolabaException instance
        
    Returns:
        Dictionary formatted for logging
    """
    return {
        "error_code": error.error_code,
        "message": error.message,
        "category": error.category,
        "severity": error.severity,
        "http_status": error.http_status,
        "details": error.details,
        "request_id": error.request_id,
        "exception_type": type(error).__name__
    }


def is_retryable_error(error: QolabaException) -> bool:
    """
    Determine if an error is retryable.
    
    Args:
        error: QolabaException instance
        
    Returns:
        True if error is retryable, False otherwise
    """
    retryable_categories = [
        ErrorCategory.NETWORK,
        ErrorCategory.TIMEOUT,
        ErrorCategory.RATE_LIMIT,
        ErrorCategory.SERVER_ERROR
    ]
    
    # Don't retry authentication/authorization errors
    non_retryable_categories = [
        ErrorCategory.AUTHENTICATION,
        ErrorCategory.AUTHORIZATION,
        ErrorCategory.VALIDATION
    ]
    
    if error.category in non_retryable_categories:
        return False
    
    if error.category in retryable_categories:
        return True
    
    # Check HTTP status codes
    if error.http_status in [408, 429, 500, 502, 503, 504]:
        return True
    
    return False


def get_retry_delay(error: QolabaException, attempt: int = 1) -> float:
    """
    Calculate retry delay for an error.
    
    Args:
        error: QolabaException instance
        attempt: Retry attempt number (1-based)
        
    Returns:
        Delay in seconds
    """
    if not is_retryable_error(error):
        return 0.0
    
    # For rate limiting, use the retry_after if available
    if isinstance(error, RateLimitException) and error.retry_after:
        return float(error.retry_after)
    
    # Exponential backoff with jitter
    base_delay = 1.0
    max_delay = 60.0
    
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    
    # Add jitter (±25%)
    import random
    jitter_factor = 0.25
    jitter = random.uniform(-jitter_factor, jitter_factor)
    delay = delay * (1 + jitter)
    
    return max(0.1, delay)  # Minimum 100ms delay


# =============================================================================
# Success Response Models
# =============================================================================

class TaskCreatedResponse(BaseQolabaResponse):
    """Response model for successfully created tasks."""

    task_id: str = Field(..., description="Created task identifier")
    status: str = Field(default="pending", description="Initial task status")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated completion in seconds")


class ChatResponse(BaseModel):
    """Response model for chat completions."""

    id: str = Field(..., description="Response identifier")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")


# =============================================================================
# Utility Functions
# =============================================================================

def validate_image_data(image_data: str) -> bool:
    """
    Validate that image data is either a valid URL or base64 encoded image.

    Args:
        image_data: Image URL or base64 string

    Returns:
        True if valid, False otherwise
    """
    import re

    # Check if it's a URL
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if url_pattern.match(image_data):
        return True

    # Check if it's base64 data
    if image_data.startswith('data:image/'):
        return True

    # Check if it's raw base64
    try:
        import base64
        base64.b64decode(image_data, validate=True)
        return True
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe use in file systems.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re
    import unicodedata

    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)

    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]

    return filename


# =============================================================================
# Advanced Data Type Conversion and Validation Utilities
# =============================================================================

def convert_image_to_base64(image_input: Union[str, bytes]) -> str:
    """
    Convert various image input formats to base64 string.
    
    Args:
        image_input: Image as URL, file path, or bytes
        
    Returns:
        Base64 encoded image string with data URI prefix
        
    Raises:
        ValueError: If image conversion fails
    """
    import base64
    import requests
    from pathlib import Path
    from typing import BinaryIO
    
    try:
        if isinstance(image_input, bytes):
            # Direct bytes conversion
            image_data = image_input
        elif isinstance(image_input, str):
            if image_input.startswith(('http://', 'https://')):
                # URL - download image
                response = requests.get(image_input, timeout=30)
                response.raise_for_status()
                image_data = response.content
            elif image_input.startswith('data:image/'):
                # Already base64 data URI
                return image_input
            elif Path(image_input).exists():
                # File path
                with open(image_input, 'rb') as f:
                    image_data = f.read()
            else:
                # Try as base64 string
                image_data = base64.b64decode(image_input)
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
            
        # Convert to base64 with data URI
        b64_string = base64.b64encode(image_data).decode('utf-8')
        
        # Detect image format (simple detection)
        if image_data.startswith(b'\xFF\xD8\xFF'):
            mime_type = 'image/jpeg'
        elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime_type = 'image/png'
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            mime_type = 'image/gif'
        elif image_data.startswith(b'WEBP', 8):
            mime_type = 'image/webp'
        else:
            mime_type = 'image/jpeg'  # Default fallback
            
        return f"data:{mime_type};base64,{b64_string}"
        
    except Exception as e:
        raise ValueError(f"Failed to convert image to base64: {str(e)}")


def validate_audio_format(format_type: str) -> str:
    """
    Validate and normalize audio format.
    
    Args:
        format_type: Audio format string
        
    Returns:
        Normalized format string
        
    Raises:
        ValueError: If format is not supported
    """
    format_mapping = {
        'mp3': 'mp3',
        'mpeg': 'mp3',
        'opus': 'opus',
        'ogg': 'opus',
        'aac': 'aac',
        'm4a': 'aac',
        'flac': 'flac',
        'wav': 'flac',  # Convert WAV to FLAC for API compatibility
    }
    
    format_lower = format_type.lower()
    if format_lower not in format_mapping:
        supported = ', '.join(format_mapping.keys())
        raise ValueError(f"Unsupported audio format '{format_type}'. Supported: {supported}")
    
    return format_mapping[format_lower]


def convert_file_size_to_bytes(size_str: str) -> int:
    """
    Convert file size string to bytes.
    
    Args:
        size_str: Size string like '10MB', '1.5GB', '500KB'
        
    Returns:
        Size in bytes
        
    Raises:
        ValueError: If size string is invalid
    """
    import re
    
    if isinstance(size_str, (int, float)):
        return int(size_str)
    
    # Parse size string
    pattern = r'^(\d+(?:\.\d+)?)\s*([KMGT]?B?)$'
    match = re.match(pattern, size_str.upper().strip())
    
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")
    
    size_value = float(match.group(1))
    unit = match.group(2)
    
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'K': 1024,
        'M': 1024**2,
        'G': 1024**3,
        'T': 1024**4,
        '': 1,  # No unit means bytes
    }
    
    return int(size_value * multipliers.get(unit, 1))


def validate_color_value(color: Union[str, tuple, list]) -> str:
    """
    Validate and normalize color values.
    
    Args:
        color: Color as hex string, RGB tuple, or named color
        
    Returns:
        Normalized hex color string
        
    Raises:
        ValueError: If color format is invalid
    """
    import re
    
    # Named colors mapping
    named_colors = {
        'red': '#FF0000',
        'green': '#00FF00',
        'blue': '#0000FF',
        'white': '#FFFFFF',
        'black': '#000000',
        'yellow': '#FFFF00',
        'cyan': '#00FFFF',
        'magenta': '#FF00FF',
        'orange': '#FFA500',
        'purple': '#800080',
        'pink': '#FFC0CB',
        'brown': '#A52A2A',
        'gray': '#808080',
        'grey': '#808080',
    }
    
    if isinstance(color, str):
        color = color.lower().strip()
        
        # Check named colors
        if color in named_colors:
            return named_colors[color]
        
        # Check hex format
        if re.match(r'^#[0-9a-f]{6}$', color):
            return color.upper()
        elif re.match(r'^#[0-9a-f]{3}$', color):
            # Convert 3-digit hex to 6-digit
            return f"#{color[1]*2}{color[2]*2}{color[3]*2}".upper()
        elif re.match(r'^[0-9a-f]{6}$', color):
            return f"#{color}".upper()
        elif re.match(r'^[0-9a-f]{3}$', color):
            return f"#{color[0]*2}{color[1]*2}{color[2]*2}".upper()
    
    elif isinstance(color, (tuple, list)):
        if len(color) == 3:
            r, g, b = color
            if all(0 <= c <= 255 for c in [r, g, b]):
                return f"#{int(r):02X}{int(g):02X}{int(b):02X}"
        elif len(color) == 4:
            # RGBA - ignore alpha for now
            r, g, b, a = color
            if all(0 <= c <= 255 for c in [r, g, b]) and 0 <= a <= 1:
                return f"#{int(r):02X}{int(g):02X}{int(b):02X}"
    
    raise ValueError(f"Invalid color format: {color}")


def normalize_model_name(model_name: str, api_type: str) -> str:
    """
    Normalize model names for different API endpoints.
    
    Args:
        model_name: Original model name
        api_type: API type ('image', 'chat', 'audio', 'vector')
        
    Returns:
        Normalized model name
        
    Raises:
        ValueError: If model is not supported for the API type
    """
    model_mappings = {
        'image': {
            'flux': 'flux',
            'flux-dev': 'flux',
            'stable-diffusion': 'stable-diffusion',
            'sd': 'stable-diffusion',
            'dall-e': 'dalle',
            'dalle': 'dalle',
            'dalle-2': 'dalle',
            'dalle-3': 'dalle-3',
        },
        'chat': {
            'gpt-4': 'gpt-4',
            'gpt-4o': 'gpt-4o',
            'gpt-3.5': 'gpt-3.5-turbo',
            'gpt-3.5-turbo': 'gpt-3.5-turbo',
            'claude': 'claude-3-opus',
            'claude-3': 'claude-3-opus',
            'claude-opus': 'claude-3-opus',
            'llama': 'llama-2-70b',
            'llama-2': 'llama-2-70b',
        },
        'audio': {
            'tts-1': 'tts-1',
            'tts-2': 'tts-1-hd',
            'tts-1-hd': 'tts-1-hd',
            'whisper': 'whisper-1',
            'whisper-1': 'whisper-1',
        },
        'vector': {
            'text-embedding-ada': 'text-embedding-ada-002',
            'ada': 'text-embedding-ada-002',
            'embedding': 'text-embedding-ada-002',
        }
    }
    
    model_lower = model_name.lower().strip()
    api_models = model_mappings.get(api_type, {})
    
    if model_lower in api_models:
        return api_models[model_lower]
    
    # If no mapping found, return normalized version (stripped and lowercased)
    return model_lower


def validate_url_or_path(input_value: str, allow_local: bool = False) -> str:
    """
    Validate URL or file path.
    
    Args:
        input_value: URL or file path to validate
        allow_local: Whether to allow local file paths
        
    Returns:
        Validated URL or path
        
    Raises:
        ValueError: If URL/path is invalid
    """
    import re
    from pathlib import Path
    from urllib.parse import urlparse
    
    if not input_value or not input_value.strip():
        raise ValueError("URL or path cannot be empty")
    
    input_value = input_value.strip()
    
    # Check if it's a URL
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if url_pattern.match(input_value):
        # Validate URL structure
        try:
            parsed = urlparse(input_value)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("Invalid URL structure")
            return input_value
        except Exception:
            raise ValueError(f"Invalid URL: {input_value}")
    
    # Check if it's a local path
    if allow_local:
        try:
            path = Path(input_value)
            if path.exists():
                return str(path.resolve())
            else:
                raise ValueError(f"File not found: {input_value}")
        except Exception as e:
            raise ValueError(f"Invalid file path: {input_value} - {str(e)}")
    
    raise ValueError(f"Invalid URL or path: {input_value}")


def convert_duration_to_seconds(duration: Union[str, int, float]) -> float:
    """
    Convert duration string to seconds.
    
    Args:
        duration: Duration as string ('1:30', '90s', '1.5m') or numeric value
        
    Returns:
        Duration in seconds
        
    Raises:
        ValueError: If duration format is invalid
    """
    if isinstance(duration, (int, float)):
        return float(duration)
    
    if not isinstance(duration, str):
        raise ValueError(f"Invalid duration type: {type(duration)}")
    
    duration = duration.strip().lower()
    
    # Format: MM:SS or HH:MM:SS
    if ':' in duration:
        parts = duration.split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = parts
            return float(minutes) * 60 + float(seconds)
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = parts
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    
    # Format with units (90s, 1.5m, 2h)
    import re
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([smh]?)$', duration)
    if match:
        value = float(match.group(1))
        unit = match.group(2) or 's'  # Default to seconds
        
        multipliers = {'s': 1, 'm': 60, 'h': 3600}
        return value * multipliers[unit]
    
    raise ValueError(f"Invalid duration format: {duration}")


def validate_json_schema(data: Dict[str, Any], required_fields: List[str] = None) -> Dict[str, Any]:
    """
    Validate JSON data structure with optional required fields.
    
    Args:
        data: JSON data to validate
        required_fields: List of required field names
        
    Returns:
        Validated data
        
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Remove None values and empty strings
    cleaned_data = {}
    for key, value in data.items():
        if value is not None and value != '':
            cleaned_data[key] = value
    
    return cleaned_data