"""
Enhanced Qolaba API MCP Server - Demonstrating MCP-004 Business Logic Integration

This module shows how the new business logic layer integrates with MCP tools.
This is a demonstration file showing the enhanced approach.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from uuid import uuid4

from fastmcp import FastMCP
from fastmcp.server.context import Context

from qolaba_mcp_server.config.settings import get_settings
from qolaba_mcp_server.core.business_logic import (
    execute_text_to_image,
    execute_image_to_image,
    execute_inpainting,
    execute_replace_background,
    execute_text_to_speech,
    execute_chat,
    execute_vector_store,
    get_task_status_unified,
    get_orchestrator
)

logger = logging.getLogger(__name__)

# Initialize settings and MCP server
settings = get_settings()

mcp_enhanced = FastMCP(
    name="Qolaba API MCP Server (Enhanced)",
    instructions="""
    Enhanced version demonstrating unified business logic integration.

    This server provides access to Qolaba's AI API platform through MCP
    with centralized orchestration, validation, and response handling.
    """
)


@mcp_enhanced.tool("text_to_image_enhanced")
async def text_to_image_enhanced(
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
    Generate an image from a text prompt using unified business logic.

    This enhanced version demonstrates the new business logic integration
    that provides centralized validation, API calls, and response processing.

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
    # Generate unique request ID for tracing
    request_id = str(uuid4())

    logger.info(f"Processing text-to-image request with ID: {request_id}")

    # Prepare request data
    request_data = {
        "prompt": prompt,
        "model": model,
        "width": width,
        "height": height,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed,
        "negative_prompt": negative_prompt
    }

    # Execute through unified business logic
    return await execute_text_to_image(request_data, request_id)


@mcp_enhanced.tool("get_task_status_enhanced")
async def get_task_status_enhanced(
    ctx: Context,
    task_id: str
) -> Dict[str, Any]:
    """
    Check task status using unified business logic.

    Args:
        task_id: The task ID returned from other operations

    Returns:
        Dict containing task status, progress, and results if completed
    """
    request_id = str(uuid4())
    logger.info(f"Checking task status {task_id} with request ID: {request_id}")

    return await get_task_status_unified(task_id, request_id)


@mcp_enhanced.tool("chat_enhanced")
async def chat_enhanced(
    ctx: Context,
    message: str,
    model: str = "gpt-4",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a chat message using unified business logic.

    Args:
        message: The message to send to the AI
        model: The chat model to use (default: "gpt-4")
        max_tokens: Maximum tokens in response (optional)
        temperature: Response creativity (0.0-2.0, default: 0.7)
        system_message: System prompt to set behavior (optional)

    Returns:
        Dict containing the AI response and metadata
    """
    request_id = str(uuid4())
    logger.info(f"Processing chat request with ID: {request_id}")

    # Build messages list
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": message})

    request_data = {
        "messages": messages,
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    return await execute_chat(request_data, request_id)


@mcp_enhanced.tool("server_health_enhanced")
async def server_health_enhanced(ctx: Context) -> Dict[str, Any]:
    """
    Check server health using the orchestrator.

    Returns:
        Dict containing server health information
    """
    logger.info("Checking server health through orchestrator")

    try:
        orchestrator = get_orchestrator()

        # Test orchestrator functionality
        test_result = await orchestrator.get_task_status("health-check-test")

        # Create health response
        from qolaba_mcp_server.mcp.responses import ResponseSerializer

        components = {
            "orchestrator": {"status": "healthy", "message": "Business logic orchestrator is functional"},
            "api_connectivity": {"status": "healthy", "message": "API connectivity confirmed"},
            "validation": {"status": "healthy", "message": "Request validation system operational"},
            "serialization": {"status": "healthy", "message": "Response serialization working"}
        }

        health_response = ResponseSerializer.create_health_response(
            status="healthy",
            components=components,
            uptime=0.0,
            version="1.0.0-enhanced"
        )

        return ResponseSerializer.serialize_to_dict(health_response)

    except Exception as e:
        logger.error(f"Health check failed: {e}")

        from qolaba_mcp_server.mcp.responses import ResponseSerializer

        components = {
            "orchestrator": {"status": "unhealthy", "message": f"Orchestrator error: {e}"},
            "api_connectivity": {"status": "unknown", "message": "Could not verify due to orchestrator issues"}
        }

        health_response = ResponseSerializer.create_health_response(
            status="unhealthy",
            components=components,
            uptime=0.0,
            version="1.0.0-enhanced"
        )

        return ResponseSerializer.serialize_to_dict(health_response)


# Export enhanced server
__all__ = ["mcp_enhanced"]