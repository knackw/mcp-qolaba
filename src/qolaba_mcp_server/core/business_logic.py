"""
Core business logic for Qolaba API MCP Server.

This module implements the central business logic layer that coordinates
between MCP handlers and the Qolaba API client. It provides unified
request processing, validation orchestration, and response handling.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Optional, Union, Type
from enum import Enum

from ..api.client import QolabaHTTPClient, HTTPClientError
from ..core.logging_config import (
    get_module_logger,
    get_performance_logger,
    get_error_logger,
    RequestContext
)
from ..core.metrics import get_metrics_collector
from ..models.api_models import (
    BaseQolabaRequest,
    TextToImageRequest,
    ImageToImageRequest,
    InpaintingRequest,
    ReplaceBackgroundRequest,
    TextToSpeechRequest,
    ChatRequest,
    VectorStoreRequest
)
from ..mcp.validation import ValidationResult, validate_request_data
from ..mcp.responses import (
    ResponseSerializer,
    MCPResponseBase,
    MCPErrorResponse,
    process_qolaba_response
)

logger = get_module_logger("core.business_logic")
perf_logger = get_performance_logger("core.business_logic")
error_logger = get_error_logger("core.business_logic")
metrics_collector = get_metrics_collector()


class OperationType(str, Enum):
    """Supported Qolaba API operation types."""
    TEXT_TO_IMAGE = "text-to-image"
    IMAGE_TO_IMAGE = "image-to-image"
    INPAINTING = "inpainting"
    REPLACE_BACKGROUND = "replace-background"
    TEXT_TO_SPEECH = "text-to-speech"
    CHAT = "chat"
    STORE_VECTOR_DB = "store-file-in-vector-database"
    TASK_STATUS = "task-status"


class QolabaMCPOrchestrator:
    """
    Central orchestrator for Qolaba API operations through MCP.

    This class provides a unified interface for processing MCP requests,
    validating them, calling the Qolaba API, and returning structured responses.
    """

    def __init__(self) -> None:
        """Initialize the orchestrator."""
        self.client = None
        self._operation_models = {
            OperationType.TEXT_TO_IMAGE: TextToImageRequest,
            OperationType.IMAGE_TO_IMAGE: ImageToImageRequest,
            OperationType.INPAINTING: InpaintingRequest,
            OperationType.REPLACE_BACKGROUND: ReplaceBackgroundRequest,
            OperationType.TEXT_TO_SPEECH: TextToSpeechRequest,
            OperationType.CHAT: ChatRequest,
            OperationType.STORE_VECTOR_DB: VectorStoreRequest,
        }

    async def execute_operation(
        self,
        operation: OperationType,
        request_data: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete Qolaba API operation with validation and response processing.

        Args:
            operation: The type of operation to execute
            request_data: Raw request data from MCP
            request_id: Optional request identifier for tracing

        Returns:
            Serialized MCP response dictionary
        """
        start_time = time.time()
        
        # Use request context for tracing
        with RequestContext(request_id=request_id, operation=operation.value) as ctx:
            logger.info(f"Starting operation execution", extra={
                "operation": operation.value,
                "request_id": ctx.request_id,
                "request_data_keys": list(request_data.keys()) if request_data else []
            })

            try:
                # Step 1: Validate request data
                validation_start = time.time()
                validation_result = await self._validate_request(operation, request_data)
                validation_time = (time.time() - validation_start) * 1000
                
                perf_logger.log_operation_timing(
                    operation=f"{operation.value}_validation",
                    duration_ms=validation_time,
                    success=validation_result.success,
                    metadata={
                        "request_data_size": len(str(request_data)),
                        "request_id": ctx.request_id,
                    }
                )
                
                if not validation_result.success:
                    error_logger.log_validation_error(
                        field="request_data",
                        value=request_data,
                        constraint="business_rules",
                        user_message=validation_result.error
                    )
                    return self._create_validation_error_response(validation_result)

                # Step 2: Execute API call
                api_start = time.time()
                api_response = await self._execute_api_call(operation, validation_result.data, ctx.request_id)
                api_time = (time.time() - api_start) * 1000
                
                perf_logger.log_operation_timing(
                    operation=f"{operation.value}_api_call",
                    duration_ms=api_time,
                    success=True,
                    metadata={
                        "status_code": api_response.get("status_code"),
                        "request_id": ctx.request_id,
                    }
                )

                # Step 3: Process and serialize response
                processing_start = time.time()
                result = self._process_api_response(api_response, operation, ctx.request_id)
                processing_time = (time.time() - processing_start) * 1000
                
                perf_logger.log_operation_timing(
                    operation=f"{operation.value}_processing",
                    duration_ms=processing_time,
                    success=True,
                    metadata={"request_id": ctx.request_id}
                )
                
                total_time = (time.time() - start_time) * 1000
                perf_logger.log_operation_timing(
                    operation=f"{operation.value}_total",
                    duration_ms=total_time,
                    success=True,
                    metadata={
                        "validation_ms": validation_time,
                        "api_call_ms": api_time,
                        "processing_ms": processing_time,
                        "request_id": ctx.request_id,
                    }
                )
                
                logger.info(f"Operation completed successfully", extra={
                    "operation": operation.value,
                    "total_duration_ms": total_time,
                    "success": True
                })
                
                # Record successful MCP operation metrics
                metrics_collector.record_mcp_operation(
                    operation=operation.value,
                    duration_seconds=total_time / 1000.0,
                    success=True,
                    model=getattr(validation_result.data, 'model', None),
                    user_id=ctx.request_id  # Using request_id as user identifier
                )
                
                return result

            except HTTPClientError as e:
                total_time = (time.time() - start_time) * 1000
                error_logger.log_exception(
                    exception=e,
                    context={
                        "operation": operation.value,
                        "request_id": ctx.request_id,
                        "total_duration_ms": total_time,
                        "http_status": getattr(e, 'status_code', None)
                    },
                    user_message=f"HTTP client error during {operation.value} operation"
                )
                
                perf_logger.log_operation_timing(
                    operation=f"{operation.value}_total",
                    duration_ms=total_time,
                    success=False,
                    metadata={"error_type": "HTTPClientError", "status_code": getattr(e, 'status_code', None)}
                )
                
                # Record failed MCP operation metrics for HTTP client errors
                metrics_collector.record_mcp_operation(
                    operation=operation.value,
                    duration_seconds=total_time / 1000.0,
                    success=False,
                    model=None,  # May not be available in error case
                    user_id=ctx.request_id
                )
                
                return self._create_http_error_response(e)
                
            except Exception as e:
                total_time = (time.time() - start_time) * 1000
                error_logger.log_exception(
                    exception=e,
                    context={
                        "operation": operation.value,
                        "request_id": ctx.request_id,
                        "total_duration_ms": total_time
                    },
                    user_message=f"Unexpected error during {operation.value} operation"
                )
                
                perf_logger.log_operation_timing(
                    operation=f"{operation.value}_total",
                    duration_ms=total_time,
                    success=False,
                    metadata={"error_type": type(e).__name__}
                )
                
                # Record failed MCP operation metrics for unexpected errors
                metrics_collector.record_mcp_operation(
                    operation=operation.value,
                    duration_seconds=total_time / 1000.0,
                    success=False,
                    model=None,  # May not be available in error case
                    user_id=ctx.request_id
                )
                
                return self._create_unexpected_error_response(e)

    async def get_task_status(
        self,
        task_id: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get status for a specific task.

        Args:
            task_id: The task identifier
            request_id: Optional request identifier for tracing

        Returns:
            Serialized task status response
        """
        logger.info(f"Getting task status for {task_id}")

        try:
            async with QolabaHTTPClient() as client:
                response = await client.get(f"task-status/{task_id}")

                if isinstance(response.content, dict):
                    # Create task status response from API data
                    from ..mcp.responses import ResponseStatus

                    mcp_response = ResponseSerializer.create_task_status_response(
                        task_id=task_id,
                        status=ResponseStatus(response.content.get("status", "pending")),
                        progress=float(response.content.get("progress", 0.0)),
                        result=response.content.get("result"),
                        error_details=response.content.get("error"),
                        created_at=response.content.get("created_at"),
                        updated_at=response.content.get("updated_at"),
                        request_id=request_id
                    )
                    return ResponseSerializer.serialize_to_dict(mcp_response)
                else:
                    return self._create_unexpected_response_error()

        except HTTPClientError as e:
            logger.error(f"Task status request failed: {e}")
            return self._create_http_error_response(e)

    async def _validate_request(
        self,
        operation: OperationType,
        request_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate request data using the appropriate model."""
        model_class = self._operation_models.get(operation)
        if not model_class:
            return ValidationResult(
                success=False,
                error=f"Unsupported operation type: {operation}"
            )

        return validate_request_data(request_data, model_class)

    async def _execute_api_call(
        self,
        operation: OperationType,
        validated_data: BaseQolabaRequest,
        request_id: Optional[str]
    ) -> Dict[str, Any]:
        """Execute the actual API call."""
        endpoint = operation.value

        async with QolabaHTTPClient() as client:
            response = await client.post(
                endpoint,
                json=validated_data.dict(exclude_none=True)
            )

            logger.info(f"API call to {endpoint} completed: {response.status_code}")

            return {
                "content": response.content,
                "status_code": response.status_code,
                "headers": response.headers,
                "request_id": request_id
            }

    def _process_api_response(
        self,
        api_response: Dict[str, Any],
        operation: OperationType,
        request_id: Optional[str]
    ) -> Dict[str, Any]:
        """Process API response and create structured MCP response."""
        content = api_response.get("content", {})

        if isinstance(content, dict):
            mcp_response = process_qolaba_response(
                content,
                operation.value,
                request_id=request_id
            )
            return ResponseSerializer.serialize_to_dict(mcp_response)
        else:
            return self._create_unexpected_response_error()

    def _create_validation_error_response(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Create a validation error response."""
        error_response = ResponseSerializer.create_error_response(
            "validation_error",
            validation_result.error or "Request validation failed",
            suggestions=["Check your input parameters", "Refer to the API documentation"]
        )
        return ResponseSerializer.serialize_to_dict(error_response)

    def _create_http_error_response(self, error: HTTPClientError) -> Dict[str, Any]:
        """Create an HTTP error response."""
        # Maintain legacy fields expected by some tests
        error_response = ResponseSerializer.create_error_response(
            "api_client_error",
            f"API request failed: {error}",
            error_details={"status_code": getattr(error, "status_code", None)}
        )
        data = ResponseSerializer.serialize_to_dict(error_response)
        data["error"] = data.get("error_code")
        data["message"] = data.get("error_message")
        return data

    def _create_unexpected_error_response(self, error: Exception) -> Dict[str, Any]:
        """Create an unexpected error response."""
        error_response = ResponseSerializer.create_error_response(
            "internal_error",
            f"An unexpected error occurred: {error}",
            suggestions=["Please try again later", "Contact support if the issue persists"]
        )
        return ResponseSerializer.serialize_to_dict(error_response)

    def _create_unexpected_response_error(self) -> Dict[str, Any]:
        """Create an error response for unexpected API response format."""
        error_response = ResponseSerializer.create_error_response(
            "unexpected_response_format",
            "Received unexpected response format from API"
        )
        return ResponseSerializer.serialize_to_dict(error_response)


# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> QolabaMCPOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = QolabaMCPOrchestrator()
    return _orchestrator


# Convenience functions for common operations

async def execute_text_to_image(request_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute text-to-image operation."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_operation(OperationType.TEXT_TO_IMAGE, request_data, request_id)


async def execute_image_to_image(request_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute image-to-image operation."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_operation(OperationType.IMAGE_TO_IMAGE, request_data, request_id)


async def execute_inpainting(request_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute inpainting operation."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_operation(OperationType.INPAINTING, request_data, request_id)


async def execute_replace_background(request_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute background replacement operation."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_operation(OperationType.REPLACE_BACKGROUND, request_data, request_id)


async def execute_text_to_speech(request_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute text-to-speech operation."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_operation(OperationType.TEXT_TO_SPEECH, request_data, request_id)


async def execute_chat(request_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute chat operation."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_operation(OperationType.CHAT, request_data, request_id)


async def execute_vector_store(request_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute vector store operation."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_operation(OperationType.STORE_VECTOR_DB, request_data, request_id)


async def get_task_status_unified(task_id: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Get task status using unified business logic."""
    orchestrator = get_orchestrator()
    return await orchestrator.get_task_status(task_id, request_id)