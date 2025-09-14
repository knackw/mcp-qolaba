"""
Response serialization and JSON schema validation for MCP tools.

This module provides utilities for serializing API responses, validating
JSON schemas, and formatting responses for MCP clients in a consistent manner.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator

from ..models.api_models import BaseQolabaResponse, TaskStatusResponse

logger = logging.getLogger(__name__)


class ResponseStatus(str, Enum):
    """Standardized response status values."""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MCPResponseType(str, Enum):
    """Types of MCP responses."""
    TASK_CREATED = "task_created"
    TASK_STATUS = "task_status"
    CONTENT = "content"
    ERROR = "error"
    LIST = "list"
    HEALTH = "health"


class MCPResponseBase(BaseModel):
    """Base model for all MCP tool responses."""

    success: bool = Field(..., description="Indicates if the operation was successful")
    response_type: MCPResponseType = Field(..., description="Type of response")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")


class MCPTaskResponse(MCPResponseBase):
    """Response model for task-based operations (image generation, TTS, etc.)."""

    response_type: MCPResponseType = Field(default=MCPResponseType.TASK_CREATED)
    task_id: str = Field(..., description="Unique task identifier")
    status: ResponseStatus = Field(default=ResponseStatus.PENDING, description="Current task status")
    message: str = Field(..., description="Human-readable status message")
    estimated_completion: Optional[int] = Field(None, description="Estimated completion time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response_type": "task_created",
                "task_id": "task_12345",
                "status": "pending",
                "message": "Task created successfully. Use get_task_status to check progress.",
                "timestamp": "2024-01-01T12:00:00Z",
                "estimated_completion": 30
            }
        }


class MCPTaskStatusResponse(MCPResponseBase):
    """Response model for task status queries."""

    response_type: MCPResponseType = Field(default=MCPResponseType.TASK_STATUS)
    task_id: str = Field(..., description="Task identifier")
    status: ResponseStatus = Field(..., description="Current task status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result if completed")
    error_details: Optional[str] = Field(None, description="Error details if failed")
    created_at: Optional[datetime] = Field(None, description="Task creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    estimated_remaining: Optional[int] = Field(None, description="Estimated remaining seconds")

    @validator("progress")
    def validate_progress(cls, v):
        return max(0.0, min(100.0, v))


class MCPContentResponse(MCPResponseBase):
    """Response model for content-based operations (chat, direct results)."""

    response_type: MCPResponseType = Field(default=MCPResponseType.CONTENT)
    content: Union[str, Dict[str, Any], List[Any]] = Field(..., description="Response content")
    content_type: str = Field(default="text", description="Type of content (text, json, binary)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response_type": "content",
                "content": "Hello! This is a chat response.",
                "content_type": "text",
                "timestamp": "2024-01-01T12:00:00Z",
                "metadata": {"model": "gpt-4", "tokens_used": 15}
            }
        }


class MCPListResponse(MCPResponseBase):
    """Response model for list-based operations (available models, etc.)."""

    response_type: MCPResponseType = Field(default=MCPResponseType.LIST)
    items: List[Dict[str, Any]] = Field(..., description="List of items")
    total_count: int = Field(..., description="Total number of items")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Items per page")
    has_more: bool = Field(default=False, description="Whether more items are available")


class MCPErrorResponse(MCPResponseBase):
    """Response model for error conditions."""

    success: bool = Field(default=False)
    response_type: MCPResponseType = Field(default=MCPResponseType.ERROR)
    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions for fixing the error")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "response_type": "error",
                "error_code": "validation_error",
                "error_message": "Invalid parameters provided",
                "timestamp": "2024-01-01T12:00:00Z",
                "suggestions": ["Check your input parameters", "Refer to the API documentation"]
            }
        }


class MCPHealthResponse(MCPResponseBase):
    """Response model for health check operations."""

    response_type: MCPResponseType = Field(default=MCPResponseType.HEALTH)
    status: str = Field(..., description="Overall health status")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Individual component status")
    uptime: float = Field(..., description="Uptime in seconds")
    version: str = Field(..., description="Service version")


class ResponseSerializer:
    """Utility class for serializing and validating MCP responses."""

    @staticmethod
    def create_task_response(
        task_id: str,
        message: str,
        status: ResponseStatus = ResponseStatus.PENDING,
        estimated_completion: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> MCPTaskResponse:
        """Create a standardized task response."""
        return MCPTaskResponse(
            success=True,
            task_id=task_id,
            status=status,
            message=message,
            estimated_completion=estimated_completion,
            request_id=request_id
        )

    @staticmethod
    def create_task_status_response(
        task_id: str,
        status: ResponseStatus,
        progress: float = 0.0,
        result: Optional[Dict[str, Any]] = None,
        error_details: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        request_id: Optional[str] = None
    ) -> MCPTaskStatusResponse:
        """Create a standardized task status response."""
        return MCPTaskStatusResponse(
            success=status != ResponseStatus.FAILED,
            task_id=task_id,
            status=status,
            progress=progress,
            result=result,
            error_details=error_details,
            created_at=created_at,
            updated_at=updated_at,
            request_id=request_id
        )

    @staticmethod
    def create_content_response(
        content: Union[str, Dict[str, Any], List[Any]],
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> MCPContentResponse:
        """Create a standardized content response."""
        return MCPContentResponse(
            success=True,
            content=content,
            content_type=content_type,
            metadata=metadata,
            request_id=request_id
        )

    @staticmethod
    def create_list_response(
        items: List[Dict[str, Any]],
        total_count: Optional[int] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        has_more: bool = False,
        request_id: Optional[str] = None
    ) -> MCPListResponse:
        """Create a standardized list response."""
        return MCPListResponse(
            success=True,
            items=items,
            total_count=total_count or len(items),
            page=page,
            per_page=per_page,
            has_more=has_more,
            request_id=request_id
        )

    @staticmethod
    def create_error_response(
        error_code: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        request_id: Optional[str] = None
    ) -> MCPErrorResponse:
        """Create a standardized error response."""
        return MCPErrorResponse(
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
            suggestions=suggestions,
            request_id=request_id
        )

    @staticmethod
    def create_health_response(
        status: str,
        components: Dict[str, Dict[str, Any]],
        uptime: float,
        version: str,
        request_id: Optional[str] = None
    ) -> MCPHealthResponse:
        """Create a standardized health response."""
        return MCPHealthResponse(
            success=status == "healthy",
            status=status,
            components=components,
            uptime=uptime,
            version=version,
            request_id=request_id
        )

    @staticmethod
    def serialize_to_dict(response: MCPResponseBase) -> Dict[str, Any]:
        """Serialize response to dictionary format."""
        try:
            data = response.dict(exclude_none=True)
            # Backward-compat fields for error responses expected by some tests
            if data.get("response_type") in (MCPResponseType.ERROR, "error"):
                data.setdefault("error", data.get("error_code"))
                data.setdefault("message", data.get("error_message"))
            return data
        except Exception as e:
            logger.error(f"Failed to serialize response: {e}")
            return ResponseSerializer.create_error_response(
                "serialization_error",
                f"Failed to serialize response: {e}"
            ).dict(exclude_none=True)

    @staticmethod
    def serialize_to_json(response: MCPResponseBase, indent: Optional[int] = None) -> str:
        """Serialize response to JSON string."""
        try:
            return response.json(exclude_none=True, indent=indent)
        except Exception as e:
            logger.error(f"Failed to serialize response to JSON: {e}")
            error_response = ResponseSerializer.create_error_response(
                "json_serialization_error",
                f"Failed to serialize response to JSON: {e}"
            )
            return error_response.json(exclude_none=True)

    @staticmethod
    def validate_response_schema(response: Dict[str, Any], response_type: MCPResponseType) -> bool:
        """Validate response against expected schema."""
        try:
            model_map = {
                MCPResponseType.TASK_CREATED: MCPTaskResponse,
                MCPResponseType.TASK_STATUS: MCPTaskStatusResponse,
                MCPResponseType.CONTENT: MCPContentResponse,
                MCPResponseType.LIST: MCPListResponse,
                MCPResponseType.ERROR: MCPErrorResponse,
                MCPResponseType.HEALTH: MCPHealthResponse
            }

            model_class = model_map.get(response_type)
            if not model_class:
                logger.warning(f"Unknown response type: {response_type}")
                return False

            # Validate by creating model instance
            model_class(**response)
            return True

        except Exception as e:
            logger.error(f"Response schema validation failed: {e}")
            return False

    @staticmethod
    def get_json_schema(response_type: MCPResponseType) -> Dict[str, Any]:
        """Get JSON schema for a response type."""
        model_map = {
            MCPResponseType.TASK_CREATED: MCPTaskResponse,
            MCPResponseType.TASK_STATUS: MCPTaskStatusResponse,
            MCPResponseType.CONTENT: MCPContentResponse,
            MCPResponseType.LIST: MCPListResponse,
            MCPResponseType.ERROR: MCPErrorResponse,
            MCPResponseType.HEALTH: MCPHealthResponse
        }

        model_class = model_map.get(response_type)
        if not model_class:
            return {}

        return model_class.schema()


def process_qolaba_response(
    qolaba_response: Dict[str, Any],
    operation_type: str,
    request_id: Optional[str] = None
) -> MCPResponseBase:
    """
    Process a raw Qolaba API response into a structured MCP response.

    Args:
        qolaba_response: Raw response from Qolaba API
        operation_type: Type of operation (text_to_image, chat, etc.)
        request_id: Optional request identifier

    Returns:
        Structured MCP response
    """
    try:
        # Check if it's a task-based operation
        if "task_id" in qolaba_response:
            return ResponseSerializer.create_task_response(
                task_id=qolaba_response["task_id"],
                status=ResponseStatus(qolaba_response.get("status", "pending")),
                message=f"{operation_type} operation started. Use get_task_status to check progress.",
                request_id=request_id
            )

        # Check if it's direct content (like chat responses)
        elif "content" in qolaba_response or "choices" in qolaba_response:
            content = qolaba_response.get("content") or qolaba_response.get("choices", [])
            metadata = {k: v for k, v in qolaba_response.items() if k not in ["content", "choices"]}

            return ResponseSerializer.create_content_response(
                content=content,
                content_type="json" if isinstance(content, (dict, list)) else "text",
                metadata=metadata,
                request_id=request_id
            )

        # Default to content response for other cases
        else:
            return ResponseSerializer.create_content_response(
                content=qolaba_response,
                content_type="json",
                request_id=request_id
            )

    except Exception as e:
        logger.error(f"Failed to process Qolaba response: {e}")
        return ResponseSerializer.create_error_response(
            "response_processing_error",
            f"Failed to process API response: {e}",
            request_id=request_id
        )


# Export main components
__all__ = [
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