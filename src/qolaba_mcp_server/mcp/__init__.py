"""
MCP (Model Context Protocol) package for Qolaba API integration.

This package contains MCP-specific utilities including request validation,
response handling, and tool decorators.
"""

from .validation import (
    ValidationResult,
    validate_request_data,
    format_validation_error,
    validate_text_to_image_request,
    validate_image_to_image_request,
    validate_inpainting_request,
    validate_replace_background_request,
    validate_text_to_speech_request,
    validate_chat_request,
    validate_vector_store_request,
    mcp_validate,
)

from .responses import (
    ResponseStatus,
    MCPResponseType,
    MCPResponseBase,
    MCPTaskResponse,
    MCPTaskStatusResponse,
    MCPContentResponse,
    MCPListResponse,
    MCPErrorResponse,
    MCPHealthResponse,
    ResponseSerializer,
    process_qolaba_response,
)

__all__ = [
    # Validation components
    "ValidationResult",
    "validate_request_data",
    "format_validation_error",
    "validate_text_to_image_request",
    "validate_image_to_image_request",
    "validate_inpainting_request",
    "validate_replace_background_request",
    "validate_text_to_speech_request",
    "validate_chat_request",
    "validate_vector_store_request",
    "mcp_validate",

    # Response components
    "ResponseStatus",
    "MCPResponseType",
    "MCPResponseBase",
    "MCPTaskResponse",
    "MCPTaskStatusResponse",
    "MCPContentResponse",
    "MCPListResponse",
    "MCPErrorResponse",
    "MCPHealthResponse",
    "ResponseSerializer",
    "process_qolaba_response",
]