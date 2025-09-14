"""
Request validation layer for MCP tools.

This module provides validation utilities that integrate Pydantic models
with FastMCP tool handlers to ensure proper data validation and error handling.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Type, TypeVar, Union
from functools import wraps

from pydantic import BaseModel, ValidationError

from ..models.api_models import (
    BaseQolabaRequest,
    TextToImageRequest,
    ImageToImageRequest,
    InpaintingRequest,
    ReplaceBackgroundRequest,
    TextToSpeechRequest,
    ChatRequest,
    VectorStoreRequest,
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class ValidationResult:
    """Result of a validation operation."""

    def __init__(self, success: bool, data: Optional[BaseModel] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error


def validate_request_data(data: Dict[str, Any], model_class: Type[T]) -> ValidationResult:
    """
    Validate request data using a Pydantic model.

    Args:
        data: Dictionary of data to validate
        model_class: The Pydantic model class to use for validation

    Returns:
        ValidationResult with success status, validated data, or error message
    """
    try:
        # Remove None values to let Pydantic handle defaults
        cleaned_data = {k: v for k, v in data.items() if v is not None}

        # Validate using Pydantic model
        validated_model = model_class(**cleaned_data)

        logger.debug(f"Successfully validated {model_class.__name__} with data: {list(cleaned_data.keys())}")
        return ValidationResult(success=True, data=validated_model)

    except ValidationError as e:
        error_msg = f"Validation failed for {model_class.__name__}: {e}"
        logger.warning(error_msg)
        return ValidationResult(success=False, error=error_msg)

    except Exception as e:
        error_msg = f"Unexpected validation error for {model_class.__name__}: {e}"
        logger.error(error_msg)
        return ValidationResult(success=False, error=error_msg)


def format_validation_error(validation_result: ValidationResult) -> Dict[str, Any]:
    """
    Format validation error for MCP response.

    Args:
        validation_result: Failed validation result

    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "error": "validation_error",
        "message": validation_result.error,
        "details": "Please check your input parameters and try again."
    }


def validate_text_to_image_request(
    prompt: str,
    model: str = "flux",
    width: int = 512,
    height: int = 512,
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None,
    negative_prompt: Optional[str] = None
) -> ValidationResult:
    """Validate text-to-image request parameters."""
    data = {
        "prompt": prompt,
        "model": model,
        "width": width,
        "height": height,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed,
        "negative_prompt": negative_prompt
    }
    return validate_request_data(TextToImageRequest, data)


def validate_image_to_image_request(
    image_url: str,
    prompt: str,
    model: str = "flux",
    strength: float = 0.8,
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None
) -> ValidationResult:
    """Validate image-to-image request parameters."""
    data = {
        "image": image_url,
        "prompt": prompt,
        "model": model,
        "strength": strength,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed
    }
    return validate_request_data(ImageToImageRequest, data)


def validate_inpainting_request(
    image_url: str,
    mask_url: str,
    prompt: str,
    model: str = "flux",
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None
) -> ValidationResult:
    """Validate inpainting request parameters."""
    data = {
        "image": image_url,
        "mask": mask_url,
        "prompt": prompt,
        "model": model,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed
    }
    return validate_request_data(InpaintingRequest, data)


def validate_replace_background_request(
    image_url: str,
    prompt: str,
    model: str = "flux",
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None
) -> ValidationResult:
    """Validate replace background request parameters."""
    data = {
        "image": image_url,
        "prompt": prompt,
        "model": model,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed
    }
    return validate_request_data(ReplaceBackgroundRequest, data)


def validate_text_to_speech_request(
    text: str,
    voice: str = "alloy",
    model: str = "tts-1",
    response_format: str = "mp3",
    speed: float = 1.0
) -> ValidationResult:
    """Validate text-to-speech request parameters."""
    data = {
        "text": text,
        "voice": voice,
        "model": model,
        "response_format": response_format,
        "speed": speed
    }
    return validate_request_data(TextToSpeechRequest, data)


def validate_chat_request(
    message: str,
    model: str = "gpt-4",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    system_message: Optional[str] = None
) -> ValidationResult:
    """Validate chat request parameters."""
    # Build messages array
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": message})

    data = {
        "messages": messages,
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    return validate_request_data(ChatRequest, data)


def validate_vector_store_request(
    file_url: str,
    collection_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> ValidationResult:
    """Validate vector store request parameters."""
    data = {
        "file": file_url,
        "collection_name": collection_name,
        "metadata": metadata or {},
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }
    return validate_request_data(VectorStoreRequest, data)


def mcp_validate(validator_func):
    """
    Decorator for MCP tools that adds Pydantic validation.

    Usage:
        @mcp_validate(validate_text_to_image_request)
        async def text_to_image_tool(ctx, **kwargs):
            # kwargs contains validated data
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx, **kwargs):
            # Extract the validation function arguments
            validation_result = validator_func(**kwargs)

            if not validation_result.success:
                logger.warning(f"Validation failed for {func.__name__}: {validation_result.error}")
                return format_validation_error(validation_result)

            # Add validated model to context for the tool function
            kwargs['_validated_model'] = validation_result.data

            # Call original function with validated data
            return await func(ctx, **kwargs)

        return wrapper
    return decorator


# Export validation functions for direct use
__all__ = [
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
]