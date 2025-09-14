"""
Qolaba API MCP Server - Main Server Implementation

This module implements the MCP (Model Context Protocol) server that provides
a bridge between the MCP protocol and the Qolaba AI API platform.

Features:
- Text-to-image generation
- Image-to-image transformation
- Inpainting and background replacement
- Text-to-speech synthesis
- Chat and streaming chat
- Vector database file storage
- Task status monitoring
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from fastmcp import FastMCP
from fastmcp.server.context import Context

from qolaba_mcp_server.config.settings import get_settings
from qolaba_mcp_server.api.client import QolabaHTTPClient, HTTPResponse, HTTPClientError
from qolaba_mcp_server.models.api_models import (
    TextToImageRequest,
    ImageToImageRequest,
    InpaintingRequest,
    ReplaceBackgroundRequest,
    TextToSpeechRequest,
    ChatRequest,
    StreamChatRequest,
    VectorStoreRequest,
    TaskStatusResponse
)
from qolaba_mcp_server.mcp.validation import (
    validate_text_to_image_request,
    validate_image_to_image_request,
    validate_inpainting_request,
    validate_replace_background_request,
    validate_text_to_speech_request,
    validate_chat_request,
    validate_vector_store_request,
    format_validation_error,
    mcp_validate
)
from qolaba_mcp_server.mcp.responses import (
    ResponseSerializer,
    ResponseStatus,
    MCPResponseType,
    process_qolaba_response
)
# Business Logic Integration (MCP-004)
from qolaba_mcp_server.core.business_logic import (
    get_orchestrator,
    execute_text_to_image,
    get_task_status_unified
)

logger = logging.getLogger(__name__)

# Initialize settings and MCP server
settings = get_settings()

mcp = FastMCP(
    name="Qolaba API MCP Server",
    instructions="""
    This server provides access to Qolaba's AI API platform through MCP.

    Features integrated business logic orchestration (MCP-004) that unifies:
    - Request validation through Pydantic models
    - API client communication with error handling
    - Response serialization and JSON schema validation
    - Centralized logging and request tracing

    Available capabilities:
    - Text-to-image generation with various models
    - Image-to-image transformation
    - Inpainting and background replacement
    - Text-to-speech synthesis
    - Chat and streaming chat functionality
    - Vector database file storage
    - Task status monitoring

    All operations are asynchronous and may require polling for completion.
    """,
)


# =============================================================================
# Text-to-Image Generation Tools
# =============================================================================

@mcp.tool("text_to_image")
async def text_to_image(
    ctx: Context,
    prompt: str,
    model: str = "flux",
    width: int = 512,
    height: int = 512,
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None,
    negative_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an image from a text prompt using Qolaba's text-to-image API.

    Args:
        prompt: The text description of the image to generate
        model: The model to use (default: "flux")
        width: Width of the generated image (default: 512)
        height: Height of the generated image (default: 512)
        steps: Number of inference steps (default: 20)
        guidance_scale: How closely to follow the prompt (default: 7.5)
        seed: Random seed for reproducible results (optional)
        negative_prompt: What to avoid in the image (optional)

    Returns:
        Dict containing task_id and status information for polling
    """
    # Validate request parameters using Pydantic model
    validation_result = validate_text_to_image_request(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed,
        negative_prompt=negative_prompt
    )

    if not validation_result.success:
        logger.warning(f"Text-to-image validation failed: {validation_result.error}")
        return format_validation_error(validation_result)

    try:
        async with QolabaHTTPClient() as client:
            # Use the validated model for the API request
            validated_request = validation_result.data

            response = await client.post(
                "text-to-image",
                json=validated_request.dict(exclude_none=True)
            )

            logger.info(f"Text-to-image request submitted: {response.status_code}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                mcp_response = process_qolaba_response(
                    response.content,
                    "text_to_image",
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)
            else:
                # Fallback for unexpected response format
                return ResponseSerializer.serialize_to_dict(
                    ResponseSerializer.create_error_response(
                        "unexpected_response_format",
                        "Received unexpected response format from API"
                    )
                )

    except HTTPClientError as e:
        logger.error(f"Text-to-image request failed: {e}")
        error_response = ResponseSerializer.create_error_response(
            "api_error",
            str(e),
            error_details={"status_code": getattr(e, "status_code", None)}
        )
        return ResponseSerializer.serialize_to_dict(error_response)


@mcp.tool("image_to_image")
async def image_to_image(
    ctx: Context,
    image_url: str,
    prompt: str,
    model: str = "flux",
    strength: float = 0.8,
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Transform an existing image based on a text prompt.

    Args:
        image_url: URL or base64 encoded image to transform
        prompt: Text description of desired transformation
        model: The model to use (default: "flux")
        strength: How much to transform the image (0.0-1.0, default: 0.8)
        steps: Number of inference steps (default: 20)
        guidance_scale: How closely to follow the prompt (default: 7.5)
        seed: Random seed for reproducible results (optional)

    Returns:
        Dict containing task_id and status information for polling
    """
    # Validate request parameters using Pydantic model
    validation_result = validate_image_to_image_request(
        image_url=image_url,
        prompt=prompt,
        model=model,
        strength=strength,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed
    )

    if not validation_result.success:
        logger.warning(f"Image-to-image validation failed: {validation_result.error}")
        return format_validation_error(validation_result)

    try:
        async with QolabaHTTPClient() as client:
            # Use the validated model for the API request
            validated_request = validation_result.data

            response = await client.post(
                "image-to-image",
                json=validated_request.dict(exclude_none=True)
            )

            logger.info(f"Image-to-image request submitted: {response.status_code}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                mcp_response = process_qolaba_response(
                    response.content,
                    "image_to_image",
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)

            # Fallback for unexpected response format
            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_error_response(
                    "unexpected_response_format",
                    "Received unexpected response format from API"
                )
            )

    except HTTPClientError as e:
        logger.error(f"Image-to-image request failed: {e}")
        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_error_response(
                "api_client_error",
                f"Image-to-image request failed: {e}",
                error_details={"status_code": getattr(e, "status_code", None)}
            )
        )


# =============================================================================
# Image Editing Tools
# =============================================================================

@mcp.tool("inpainting")
async def inpainting(
    ctx: Context,
    image_url: str,
    mask_url: str,
    prompt: str,
    model: str = "flux",
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fill in masked areas of an image based on a text prompt.

    Args:
        image_url: URL or base64 encoded source image
        mask_url: URL or base64 encoded mask image (white = inpaint, black = keep)
        prompt: Text description of what to paint in masked areas
        model: The model to use (default: "flux")
        steps: Number of inference steps (default: 20)
        guidance_scale: How closely to follow the prompt (default: 7.5)
        seed: Random seed for reproducible results (optional)

    Returns:
        Dict containing task_id and status information for polling
    """
    logger.info(f"Processing inpainting request: {prompt[:50]}...")

    # Validate request using MCP validation
    validation_result = validate_inpainting_request(
        image=image_url,
        mask=mask_url,
        prompt=prompt,
        model=model,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed
    )

    if not validation_result.success:
        logger.warning(f"Inpainting validation failed: {validation_result.error}")
        return format_validation_error(validation_result)

    try:
        async with QolabaHTTPClient() as client:
            # Use the validated model for the API request
            validated_request = validation_result.data

            response = await client.post(
                "inpainting",
                json=validated_request.dict(exclude_none=True)
            )

            logger.info(f"Inpainting request submitted: {response.status_code}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                mcp_response = process_qolaba_response(
                    response.content,
                    "inpainting",
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)

            # Fallback for unexpected response format
            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_error_response(
                    "unexpected_response_format",
                    "Received unexpected response format from API"
                )
            )

    except HTTPClientError as e:
        logger.error(f"Inpainting request failed: {e}")
        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_error_response(
                "api_client_error",
                f"Inpainting request failed: {e}",
                error_details={"status_code": getattr(e, "status_code", None)}
            )
        )


@mcp.tool("replace_background")
async def replace_background(
    ctx: Context,
    image_url: str,
    prompt: str,
    model: str = "flux",
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Replace the background of an image while keeping the main subject.

    Args:
        image_url: URL or base64 encoded source image
        prompt: Text description of the new background
        model: The model to use (default: "flux")
        steps: Number of inference steps (default: 20)
        guidance_scale: How closely to follow the prompt (default: 7.5)
        seed: Random seed for reproducible results (optional)

    Returns:
        Dict containing task_id and status information for polling
    """
    logger.info(f"Processing replace background request: {prompt[:50]}...")

    # Validate request using MCP validation
    validation_result = validate_replace_background_request(
        image=image_url,
        prompt=prompt,
        model=model,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed
    )

    if not validation_result.success:
        logger.warning(f"Replace background validation failed: {validation_result.error}")
        return format_validation_error(validation_result)

    try:
        async with QolabaHTTPClient() as client:
            # Use the validated model for the API request
            validated_request = validation_result.data

            response = await client.post(
                "replace-background",
                json=validated_request.dict(exclude_none=True)
            )

            logger.info(f"Background replacement request submitted: {response.status_code}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                mcp_response = process_qolaba_response(
                    response.content,
                    "replace_background",
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)

            # Fallback for unexpected response format
            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_error_response(
                    "unexpected_response_format",
                    "Received unexpected response format from API"
                )
            )

    except HTTPClientError as e:
        logger.error(f"Background replacement request failed: {e}")
        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_error_response(
                "api_client_error",
                f"Background replacement request failed: {e}",
                error_details={"status_code": getattr(e, "status_code", None)}
            )
        )


# =============================================================================
# Audio Generation Tools
# =============================================================================

@mcp.tool("text_to_speech")
async def text_to_speech(
    ctx: Context,
    text: str,
    voice: str = "alloy",
    model: str = "tts-1",
    response_format: str = "mp3",
    speed: float = 1.0
) -> Dict[str, Any]:
    """
    Convert text to speech using Qolaba's text-to-speech API.

    Args:
        text: The text to convert to speech
        voice: Voice to use (default: "alloy")
        model: TTS model to use (default: "tts-1")
        response_format: Audio format (default: "mp3")
        speed: Speech speed (0.25-4.0, default: 1.0)

    Returns:
        Dict containing task_id and status information for polling
    """
    # Validate request parameters using Pydantic model
    validation_result = validate_text_to_speech_request(
        text=text,
        voice=voice,
        model=model,
        response_format=response_format,
        speed=speed
    )

    if not validation_result.success:
        logger.warning(f"Text-to-speech validation failed: {validation_result.error}")
        return format_validation_error(validation_result)

    try:
        async with QolabaHTTPClient() as client:
            # Use the validated model for the API request
            validated_request = validation_result.data

            response = await client.post(
                "text-to-speech",
                json=validated_request.dict(exclude_none=True)
            )

            logger.info(f"Text-to-speech request submitted: {response.status_code}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                mcp_response = process_qolaba_response(
                    response.content,
                    "text_to_speech",
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)

            # Fallback for unexpected response format
            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_error_response(
                    "unexpected_response_format",
                    "Received unexpected response format from API"
                )
            )

    except HTTPClientError as e:
        logger.error(f"Text-to-speech request failed: {e}")
        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_error_response(
                "api_client_error",
                f"Text-to-speech request failed: {e}",
                error_details={"status_code": getattr(e, "status_code", None)}
            )
        )


# =============================================================================
# Chat and Conversation Tools
# =============================================================================

@mcp.tool("chat")
async def chat(
    ctx: Context,
    message: str,
    model: str = "gpt-4",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a chat message and get a response from Qolaba's chat API.

    Args:
        message: The message to send to the AI
        model: The chat model to use (default: "gpt-4")
        max_tokens: Maximum tokens in response (optional)
        temperature: Response creativity (0.0-2.0, default: 0.7)
        system_message: System prompt to set behavior (optional)

    Returns:
        Dict containing the AI response and metadata
    """
    logger.info(f"Processing chat request: {message[:50]}...")

    # Build messages list
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": message})

    # Validate request using MCP validation
    validation_result = validate_chat_request(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature
    )

    if not validation_result.success:
        logger.warning(f"Chat validation failed: {validation_result.error}")
        return format_validation_error(validation_result)

    try:
        async with QolabaHTTPClient() as client:
            # Use the validated model for the API request
            validated_request = validation_result.data

            response = await client.post(
                "chat",
                json=validated_request.dict(exclude_none=True)
            )

            logger.info(f"Chat request completed: {response.status_code}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                mcp_response = process_qolaba_response(
                    response.content,
                    "chat",
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)

            # Fallback for unexpected response format
            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_error_response(
                    "unexpected_response_format",
                    "Received unexpected response format from API"
                )
            )

    except HTTPClientError as e:
        logger.error(f"Chat request failed: {e}")
        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_error_response(
                "api_client_error",
                f"Chat request failed: {e}",
                error_details={"status_code": getattr(e, "status_code", None)}
            )
        )


# =============================================================================
# Vector Database Tools
# =============================================================================

@mcp.tool("store_file_in_vector_db")
async def store_file_in_vector_db(
    ctx: Context,
    file_url: str,
    collection_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> Dict[str, Any]:
    """
    Store a file in Qolaba's vector database for semantic search.

    Args:
        file_url: URL or path to the file to store
        collection_name: Name of the vector collection
        metadata: Optional metadata to associate with the file
        chunk_size: Size of text chunks (default: 1000)
        chunk_overlap: Overlap between chunks (default: 200)

    Returns:
        Dict containing task_id and status information for polling
    """
    logger.info(f"Processing vector store request: {collection_name}")

    # Validate request using MCP validation
    validation_result = validate_vector_store_request(
        file=file_url,
        collection_name=collection_name,
        metadata=metadata or {},
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    if not validation_result.success:
        logger.warning(f"Vector store validation failed: {validation_result.error}")
        return format_validation_error(validation_result)

    try:
        async with QolabaHTTPClient() as client:
            # Use the validated model for the API request
            validated_request = validation_result.data

            response = await client.post(
                "store-file-in-vector-database",
                json=validated_request.dict(exclude_none=True)
            )

            logger.info(f"Vector store request submitted: {response.status_code}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                mcp_response = process_qolaba_response(
                    response.content,
                    "store_file_in_vector_db",
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)

            # Fallback for unexpected response format
            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_error_response(
                    "unexpected_response_format",
                    "Received unexpected response format from API"
                )
            )

    except HTTPClientError as e:
        logger.error(f"Vector store request failed: {e}")
        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_error_response(
                "api_client_error",
                f"Vector store request failed: {e}",
                error_details={"status_code": getattr(e, "status_code", None)}
            )
        )


# =============================================================================
# Task Management Tools
# =============================================================================

@mcp.tool("get_task_status")
async def get_task_status(
    ctx: Context,
    task_id: str
) -> Dict[str, Any]:
    """
    Check the status of a previously submitted task.

    Args:
        task_id: The task ID returned from other operations

    Returns:
        Dict containing task status, progress, and results if completed
    """
    logger.info(f"Checking task status: {task_id}")

    try:
        async with QolabaHTTPClient() as client:
            response = await client.get(f"task-status/{task_id}")

            logger.info(f"Task status checked: {task_id}")

            # Process response using the new serialization system
            if isinstance(response.content, dict):
                # Create task status response from API data
                mcp_response = ResponseSerializer.create_task_status_response(
                    task_id=task_id,
                    status=ResponseStatus(response.content.get("status", "pending")),
                    progress=float(response.content.get("progress", 0.0)),
                    result=response.content.get("result"),
                    error_details=response.content.get("error"),
                    created_at=response.content.get("created_at"),
                    updated_at=response.content.get("updated_at"),
                    request_id=response.headers.get("x-request-id")
                )
                return ResponseSerializer.serialize_to_dict(mcp_response)

            # Fallback for unexpected response format
            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_error_response(
                    "unexpected_response_format",
                    "Received unexpected response format from API"
                )
            )

    except HTTPClientError as e:
        logger.error(f"Task status check failed: {e}")
        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_error_response(
                "api_client_error",
                f"Task status check failed: {e}",
                error_details={"status_code": getattr(e, "status_code", None)}
            )
        )


# =============================================================================
# Utility Tools
# =============================================================================

@mcp.tool("list_available_models")
async def list_available_models(ctx: Context) -> Dict[str, Any]:
    """
    Get a list of available models for different Qolaba API endpoints.

    Returns:
        Dict containing available models organized by capability
    """
    logger.info("Listing available models")

    models_data = {
        "models": {
            "text_to_image": ["flux", "stable-diffusion-xl", "stable-diffusion-v2"],
            "image_to_image": ["flux", "stable-diffusion-xl", "stable-diffusion-v2"],
            "inpainting": ["flux", "stable-diffusion-xl"],
            "replace_background": ["flux", "stable-diffusion-xl"],
            "text_to_speech": ["tts-1", "tts-1-hd"],
            "chat": ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2"]
        },
        "voices": {
            "text_to_speech": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        }
    }

    return ResponseSerializer.serialize_to_dict(
        ResponseSerializer.create_content_response(
            content=models_data,
            content_type="json",
            metadata={"total_models": sum(len(v) for v in models_data["models"].values())}
        )
    )


@mcp.tool("server_health")
async def server_health(ctx: Context) -> Dict[str, Any]:
    """
    Check the health status of the Qolaba MCP Server and API connectivity.

    Returns:
        Dict containing server health information
    """
    logger.info("Checking server health")

    try:
        async with QolabaHTTPClient() as client:
            # Simple health check - try to get task status for a non-existent task
            # This should return a 404 but confirms API connectivity
            response = await client.get("task-status/health-check-test")

        # If we get here without exception, API is accessible
        components = {
            "api_connectivity": {"status": "healthy", "message": "API is accessible"},
            "configuration": {"status": "healthy", "message": "Settings loaded successfully"}
        }

        return ResponseSerializer.serialize_to_dict(
            ResponseSerializer.create_health_response(
                status="healthy",
                components=components,
                uptime=0.0,  # Could be calculated from server start time
                version="1.0.0"
            )
        )

    except HTTPClientError as e:
        # Expected 404 for non-existent task is actually a good sign
        if getattr(e, "status_code", None) == 404:
            components = {
                "api_connectivity": {"status": "healthy", "message": "API is accessible (404 expected)"},
                "configuration": {"status": "healthy", "message": "Settings loaded successfully"}
            }

            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_health_response(
                    status="healthy",
                    components=components,
                    uptime=0.0,
                    version="1.0.0"
                )
            )
        else:
            components = {
                "api_connectivity": {"status": "unhealthy", "message": f"API error: {e}"},
                "configuration": {"status": "healthy", "message": "Settings loaded successfully"}
            }

            return ResponseSerializer.serialize_to_dict(
                ResponseSerializer.create_health_response(
                    status="unhealthy",
                    components=components,
                    uptime=0.0,
                    version="1.0.0"
                )
            )


# Export the server instance
__all__ = ["mcp"]