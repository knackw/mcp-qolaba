"""
Mock strategies for external API calls using unittest.mock.

This module provides comprehensive mocking strategies for the Qolaba API client,
including mock decorators, response generators, error handlers, and context managers.
It follows the requirements from TEST-002 to enable testing without external dependencies.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
import uuid

import httpx
import pytest


# =============================================================================
# Mock Response Data Generators
# =============================================================================

class QolabaMockResponseGenerator:
    """Generator for mock Qolaba API responses."""
    
    @staticmethod
    def generate_task_id() -> str:
        """Generate a mock task ID."""
        return f"task_{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def generate_timestamp() -> str:
        """Generate ISO timestamp for mock responses."""
        return datetime.now(timezone.utc).isoformat()
    
    @classmethod
    def text_to_image_success(cls, task_id: str = None, **kwargs) -> Dict[str, Any]:
        """Generate successful text-to-image response."""
        task_id = task_id or cls.generate_task_id()
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "image_url": f"https://cdn.qolaba.ai/images/{task_id}.jpg",
                "metadata": {
                    "model": kwargs.get("model", "flux"),
                    "width": kwargs.get("width", 512),
                    "height": kwargs.get("height", 512),
                    "steps": kwargs.get("steps", 20),
                    "seed": kwargs.get("seed", 42)
                }
            },
            "created_at": cls.generate_timestamp(),
            "updated_at": cls.generate_timestamp()
        }
    
    @classmethod
    def text_to_image_pending(cls, task_id: str = None) -> Dict[str, Any]:
        """Generate pending text-to-image response."""
        task_id = task_id or cls.generate_task_id()
        return {
            "task_id": task_id,
            "status": "pending",
            "created_at": cls.generate_timestamp(),
            "updated_at": cls.generate_timestamp()
        }
    
    @classmethod
    def image_to_image_success(cls, task_id: str = None, **kwargs) -> Dict[str, Any]:
        """Generate successful image-to-image response."""
        task_id = task_id or cls.generate_task_id()
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "image_url": f"https://cdn.qolaba.ai/images/{task_id}.jpg",
                "metadata": {
                    "model": kwargs.get("model", "flux"),
                    "strength": kwargs.get("strength", 0.8),
                    "steps": kwargs.get("steps", 20)
                }
            },
            "created_at": cls.generate_timestamp(),
            "updated_at": cls.generate_timestamp()
        }
    
    @classmethod
    def text_to_speech_success(cls, task_id: str = None, **kwargs) -> Dict[str, Any]:
        """Generate successful text-to-speech response."""
        task_id = task_id or cls.generate_task_id()
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "audio_url": f"https://cdn.qolaba.ai/audio/{task_id}.mp3",
                "metadata": {
                    "voice": kwargs.get("voice", "alloy"),
                    "model": kwargs.get("model", "tts-1"),
                    "duration": kwargs.get("duration", 12.5)
                }
            },
            "created_at": cls.generate_timestamp(),
            "updated_at": cls.generate_timestamp()
        }
    
    @classmethod
    def chat_success(cls, task_id: str = None, **kwargs) -> Dict[str, Any]:
        """Generate successful chat response."""
        task_id = task_id or cls.generate_task_id()
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": kwargs.get("content", "Hello! How can I help you today?")
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": kwargs.get("prompt_tokens", 10),
                    "completion_tokens": kwargs.get("completion_tokens", 15),
                    "total_tokens": kwargs.get("total_tokens", 25)
                }
            },
            "created_at": cls.generate_timestamp(),
            "updated_at": cls.generate_timestamp()
        }
    
    @classmethod
    def task_status_response(cls, task_id: str, status: str = "completed", 
                           progress: float = 100.0, result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate task status response."""
        response = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "created_at": cls.generate_timestamp(),
            "updated_at": cls.generate_timestamp()
        }
        
        if result:
            response["result"] = result
            
        if status == "running":
            response["estimated_time_remaining"] = 30
            
        return response
    
    @classmethod
    def error_response(cls, error_code: str, message: str, 
                      details: Dict[str, Any] = None, request_id: str = None) -> Dict[str, Any]:
        """Generate error response."""
        return {
            "error_code": error_code,
            "message": message,
            "details": details or {},
            "request_id": request_id or f"req_{uuid.uuid4().hex[:8]}",
            "timestamp": cls.generate_timestamp()
        }


# =============================================================================
# Mock HTTP Response Classes
# =============================================================================

class MockHTTPResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] = None, 
                 headers: Dict[str, str] = None, text: str = None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {"content-type": "application/json"}
        self._text = text or json.dumps(self._json_data)
        
    def json(self) -> Dict[str, Any]:
        """Return JSON response data."""
        return self._json_data
    
    @property
    def text(self) -> str:
        """Return response text."""
        return self._text
    
    def raise_for_status(self):
        """Raise HTTPError for bad status codes."""
        if 400 <= self.status_code < 600:
            raise httpx.HTTPStatusError(
                message=f"HTTP {self.status_code}",
                request=None,
                response=self
            )


# =============================================================================
# Mock Strategy Decorators
# =============================================================================

def mock_qolaba_api_success(endpoint: str = "all", **response_kwargs):
    """
    Decorator to mock successful Qolaba API responses.
    
    Args:
        endpoint: Specific endpoint to mock ("text-to-image", "chat", etc.) or "all"
        **response_kwargs: Additional data for response generation
    """
    def decorator(test_func):
        @wraps(test_func)
        async def async_wrapper(*args, **kwargs):
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                # Configure successful responses based on endpoint
                mock_instance = AsyncMock()
                mock_client.return_value = mock_instance
                
                if endpoint == "text-to-image" or endpoint == "all":
                    mock_instance.text_to_image.return_value = MockHTTPResponse(
                        200, QolabaMockResponseGenerator.text_to_image_success(**response_kwargs)
                    )
                
                if endpoint == "image-to-image" or endpoint == "all":
                    mock_instance.image_to_image.return_value = MockHTTPResponse(
                        200, QolabaMockResponseGenerator.image_to_image_success(**response_kwargs)
                    )
                
                if endpoint == "text-to-speech" or endpoint == "all":
                    mock_instance.text_to_speech.return_value = MockHTTPResponse(
                        200, QolabaMockResponseGenerator.text_to_speech_success(**response_kwargs)
                    )
                
                if endpoint == "chat" or endpoint == "all":
                    mock_instance.chat.return_value = MockHTTPResponse(
                        200, QolabaMockResponseGenerator.chat_success(**response_kwargs)
                    )
                
                return await test_func(*args, mock_client=mock_instance, **kwargs)
        
        @wraps(test_func)
        def sync_wrapper(*args, **kwargs):
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                
                # Configure mock responses (sync version)
                if endpoint == "text-to-image" or endpoint == "all":
                    mock_instance.text_to_image.return_value = MockHTTPResponse(
                        200, QolabaMockResponseGenerator.text_to_image_success(**response_kwargs)
                    )
                
                return test_func(*args, mock_client=mock_instance, **kwargs)
        
        # Return appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(test_func) else sync_wrapper
    
    return decorator


def mock_qolaba_api_error(status_code: int = 400, error_code: str = "VALIDATION_ERROR", 
                         message: str = "Invalid request", details: Dict[str, Any] = None):
    """
    Decorator to mock Qolaba API error responses.
    
    Args:
        status_code: HTTP status code for the error
        error_code: API error code
        message: Error message
        details: Additional error details
    """
    def decorator(test_func):
        @wraps(test_func)
        async def async_wrapper(*args, **kwargs):
            error_response = QolabaMockResponseGenerator.error_response(
                error_code, message, details
            )
            
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value = mock_instance
                
                # Configure all methods to return error
                for method in ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']:
                    getattr(mock_instance, method).return_value = MockHTTPResponse(
                        status_code, error_response
                    )
                
                return await test_func(*args, mock_client=mock_instance, **kwargs)
        
        @wraps(test_func)  
        def sync_wrapper(*args, **kwargs):
            error_response = QolabaMockResponseGenerator.error_response(
                error_code, message, details
            )
            
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                
                # Configure all methods to return error
                for method in ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']:
                    getattr(mock_instance, method).return_value = MockHTTPResponse(
                        status_code, error_response
                    )
                
                return test_func(*args, mock_client=mock_instance, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(test_func) else sync_wrapper
    
    return decorator


def mock_qolaba_api_timeout(timeout_duration: float = 5.0):
    """
    Decorator to mock Qolaba API timeout scenarios.
    
    Args:
        timeout_duration: Timeout duration in seconds
    """
    def decorator(test_func):
        @wraps(test_func)
        async def async_wrapper(*args, **kwargs):
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value = mock_instance
                
                # Configure all methods to raise timeout
                timeout_error = httpx.TimeoutException(f"Timeout after {timeout_duration}s")
                for method in ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']:
                    getattr(mock_instance, method).side_effect = timeout_error
                
                return await test_func(*args, mock_client=mock_instance, **kwargs)
        
        @wraps(test_func)
        def sync_wrapper(*args, **kwargs):
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                
                timeout_error = httpx.TimeoutException(f"Timeout after {timeout_duration}s")
                for method in ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']:
                    getattr(mock_instance, method).side_effect = timeout_error
                
                return test_func(*args, mock_client=mock_instance, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(test_func) else sync_wrapper
    
    return decorator


# =============================================================================
# Context Managers for Advanced Mock Scenarios
# =============================================================================

@asynccontextmanager
async def mock_qolaba_api_context(responses: Dict[str, MockHTTPResponse]):
    """
    Async context manager for complex API mocking scenarios.
    
    Args:
        responses: Dictionary mapping method names to mock responses
    
    Example:
        async with mock_qolaba_api_context({
            'text_to_image': MockHTTPResponse(200, success_data),
            'chat': MockHTTPResponse(400, error_data)
        }) as mock_client:
            # Test code here
    """
    with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        
        # Configure specific responses for each method
        for method_name, response in responses.items():
            if hasattr(mock_instance, method_name):
                getattr(mock_instance, method_name).return_value = response
        
        yield mock_instance


@contextmanager
def mock_qolaba_api_progressive_responses(method: str, responses: List[MockHTTPResponse]):
    """
    Context manager for progressive API responses (e.g., pending -> completed).
    
    Args:
        method: API method name to mock
        responses: List of responses to return in sequence
    
    Example:
        with mock_qolaba_api_progressive_responses('text_to_image', [
            MockHTTPResponse(200, pending_response),
            MockHTTPResponse(200, completed_response)
        ]) as mock_client:
            # First call returns pending, second returns completed
    """
    with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        
        # Configure method to return responses in sequence
        if hasattr(mock_instance, method):
            getattr(mock_instance, method).side_effect = responses
        
        yield mock_instance


# =============================================================================
# Rate Limiting Mock Utilities
# =============================================================================

class MockRateLimiter:
    """Mock rate limiter for testing rate limiting scenarios."""
    
    def __init__(self, max_requests: int = 5, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_count = 0
        
    async def check_rate_limit(self):
        """Check if rate limit is exceeded."""
        self.request_count += 1
        if self.request_count > self.max_requests:
            raise httpx.HTTPStatusError(
                message="Rate limit exceeded",
                request=None,
                response=MockHTTPResponse(429, {
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "retry_after": 60
                })
            )


def mock_qolaba_api_rate_limited(max_requests: int = 3):
    """
    Decorator to mock rate limiting behavior.
    
    Args:
        max_requests: Maximum requests before rate limiting
    """
    def decorator(test_func):
        @wraps(test_func)
        async def async_wrapper(*args, **kwargs):
            rate_limiter = MockRateLimiter(max_requests)
            
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value = mock_instance
                
                # Configure methods to check rate limit
                async def rate_limited_call(*call_args, **call_kwargs):
                    await rate_limiter.check_rate_limit()
                    return MockHTTPResponse(200, {"status": "success"})
                
                for method in ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']:
                    getattr(mock_instance, method).side_effect = rate_limited_call
                
                return await test_func(*args, mock_client=mock_instance, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(test_func) else test_func
    
    return decorator


# =============================================================================
# Authentication Mock Utilities
# =============================================================================

def mock_qolaba_auth_failure(auth_error_type: str = "invalid_key"):
    """
    Decorator to mock authentication failures.
    
    Args:
        auth_error_type: Type of auth error ('invalid_key', 'expired_token', 'missing_auth')
    """
    def decorator(test_func):
        @wraps(test_func)
        async def async_wrapper(*args, **kwargs):
            error_responses = {
                "invalid_key": {"error_code": "INVALID_API_KEY", "message": "Invalid API key"},
                "expired_token": {"error_code": "EXPIRED_TOKEN", "message": "Token has expired"},
                "missing_auth": {"error_code": "MISSING_AUTHENTICATION", "message": "Authentication required"}
            }
            
            error_data = error_responses.get(auth_error_type, error_responses["invalid_key"])
            
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value = mock_instance
                
                # Configure all methods to return auth error
                for method in ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']:
                    getattr(mock_instance, method).return_value = MockHTTPResponse(401, error_data)
                
                return await test_func(*args, mock_client=mock_instance, **kwargs)
        
        @wraps(test_func)
        def sync_wrapper(*args, **kwargs):
            error_responses = {
                "invalid_key": {"error_code": "INVALID_API_KEY", "message": "Invalid API key"},
                "expired_token": {"error_code": "EXPIRED_TOKEN", "message": "Token has expired"},
                "missing_auth": {"error_code": "MISSING_AUTHENTICATION", "message": "Authentication required"}
            }
            
            error_data = error_responses.get(auth_error_type, error_responses["invalid_key"])
            
            with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                
                for method in ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']:
                    getattr(mock_instance, method).return_value = MockHTTPResponse(401, error_data)
                
                return test_func(*args, mock_client=mock_instance, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(test_func) else sync_wrapper
    
    return decorator


# =============================================================================
# Streaming Response Mock Utilities
# =============================================================================

class MockStreamingResponse:
    """Mock streaming response for chat streaming scenarios."""
    
    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = messages
        self._index = 0
    
    async def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self._index >= len(self.messages):
            raise StopAsyncIteration
        
        message = self.messages[self._index]
        self._index += 1
        
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        return json.dumps(message).encode('utf-8')


@asynccontextmanager
async def mock_qolaba_streaming_chat(messages: List[str]):
    """
    Mock streaming chat responses.
    
    Args:
        messages: List of message contents to stream
    """
    streaming_messages = []
    for i, content in enumerate(messages):
        streaming_messages.append({
            "delta": {
                "content": content,
                "role": "assistant" if i == 0 else None
            },
            "finish_reason": "stop" if i == len(messages) - 1 else None
        })
    
    with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        
        mock_instance.stream_chat.return_value = MockStreamingResponse(streaming_messages)
        
        yield mock_instance


# =============================================================================
# Test Helper Functions
# =============================================================================

def create_mock_api_client(**config_overrides) -> AsyncMock:
    """
    Create a mock API client with default configuration.
    
    Args:
        **config_overrides: Configuration overrides for testing
    
    Returns:
        Configured AsyncMock instance
    """
    mock_client = AsyncMock()
    
    # Default successful responses
    mock_client.text_to_image.return_value = MockHTTPResponse(
        200, QolabaMockResponseGenerator.text_to_image_success()
    )
    mock_client.image_to_image.return_value = MockHTTPResponse(
        200, QolabaMockResponseGenerator.image_to_image_success()
    )
    mock_client.text_to_speech.return_value = MockHTTPResponse(
        200, QolabaMockResponseGenerator.text_to_speech_success()
    )
    mock_client.chat.return_value = MockHTTPResponse(
        200, QolabaMockResponseGenerator.chat_success()
    )
    
    return mock_client


def assert_api_call_made(mock_client: AsyncMock, method: str, expected_args: Dict[str, Any] = None):
    """
    Assert that a specific API call was made with expected arguments.
    
    Args:
        mock_client: Mock client instance
        method: API method name
        expected_args: Expected call arguments
    """
    mock_method = getattr(mock_client, method)
    assert mock_method.called, f"Expected {method} to be called"
    
    if expected_args:
        call_args, call_kwargs = mock_method.call_args
        for key, expected_value in expected_args.items():
            if key in call_kwargs:
                assert call_kwargs[key] == expected_value, f"Expected {key}={expected_value}, got {call_kwargs[key]}"


def create_test_scenarios() -> Dict[str, Dict[str, Any]]:
    """
    Create common test scenarios for API testing.
    
    Returns:
        Dictionary of test scenarios with mock configurations
    """
    return {
        "success": {
            "status_code": 200,
            "response_data": QolabaMockResponseGenerator.text_to_image_success()
        },
        "validation_error": {
            "status_code": 400,
            "response_data": QolabaMockResponseGenerator.error_response(
                "VALIDATION_ERROR", "Invalid input parameters"
            )
        },
        "auth_error": {
            "status_code": 401,
            "response_data": QolabaMockResponseGenerator.error_response(
                "INVALID_API_KEY", "Authentication failed"
            )
        },
        "rate_limit": {
            "status_code": 429,
            "response_data": QolabaMockResponseGenerator.error_response(
                "RATE_LIMIT_EXCEEDED", "Too many requests"
            )
        },
        "server_error": {
            "status_code": 500,
            "response_data": QolabaMockResponseGenerator.error_response(
                "INTERNAL_SERVER_ERROR", "Server error occurred"
            )
        }
    }


# Export all utilities for easy importing
__all__ = [
    "QolabaMockResponseGenerator",
    "MockHTTPResponse", 
    "MockStreamingResponse",
    "MockRateLimiter",
    "mock_qolaba_api_success",
    "mock_qolaba_api_error",
    "mock_qolaba_api_timeout",
    "mock_qolaba_api_rate_limited",
    "mock_qolaba_auth_failure",
    "mock_qolaba_api_context",
    "mock_qolaba_api_progressive_responses",
    "mock_qolaba_streaming_chat",
    "create_mock_api_client",
    "assert_api_call_made", 
    "create_test_scenarios"
]