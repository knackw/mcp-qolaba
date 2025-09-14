from typing import Any, Callable, Dict
from unittest.mock import AsyncMock, MagicMock
import json
import pytest
import httpx
from pathlib import Path


def pytest_collection_modifyitems(items):
    """Automatically mark tests in integration_tests folder with 'integration' marker."""
    for item in items:
        # Check if the test is in the integration_tests folder
        if "integration_tests" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def import_rich_rule():
    # What a hack
    import rich.rule  # noqa: F401

    yield


def get_fn_name(fn: Callable[..., Any]) -> str:
    return fn.__name__  # ty: ignore[unresolved-attribute]


# =============================================================================
# Qolaba MCP Server Test Fixtures
# =============================================================================

# Import mock strategies for easy access in tests
from tests.utils.mock_strategies import (
    QolabaMockResponseGenerator,
    MockHTTPResponse,
    mock_qolaba_api_success,
    mock_qolaba_api_error,
    mock_qolaba_api_timeout,
    mock_qolaba_auth_failure,
    create_mock_api_client,
    create_test_scenarios
)

@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def qolaba_api_key():
    """Mock Qolaba API key for testing."""
    return "test_api_key_12345"


@pytest.fixture
def qolaba_base_url():
    """Qolaba API base URL for testing."""
    return "https://api.qolaba.ai/v1"


@pytest.fixture
def mock_qolaba_config():
    """Mock Qolaba configuration for testing."""
    return {
        "api_key": "test_api_key_12345",
        "base_url": "https://api.qolaba.ai/v1",
        "timeout": 30,
        "max_retries": 3,
        "rate_limit": 100
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for API testing."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


@pytest.fixture
def sample_text_to_image_request():
    """Sample text-to-image request data."""
    return {
        "prompt": "A beautiful sunset over mountains",
        "model": "flux",
        "width": 512,
        "height": 512,
        "steps": 20,
        "guidance_scale": 7.5,
        "seed": 42
    }


@pytest.fixture
def sample_text_to_image_response():
    """Sample text-to-image response data."""
    return {
        "task_id": "task_12345",
        "status": "completed",
        "result": {
            "image_url": "https://cdn.qolaba.ai/images/12345.jpg",
            "metadata": {
                "model": "flux",
                "steps": 20,
                "seed": 42
            }
        },
        "created_at": "2025-09-13T10:00:00Z",
        "updated_at": "2025-09-13T10:01:30Z"
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request data."""
    return {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "model": "gpt-4",
        "max_tokens": 150,
        "temperature": 0.7
    }


@pytest.fixture
def sample_chat_response():
    """Sample chat response data."""
    return {
        "task_id": "chat_67890",
        "status": "completed",
        "result": {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
    }


@pytest.fixture
def sample_error_response():
    """Sample API error response."""
    return {
        "error_code": "VALIDATION_ERROR",
        "message": "Invalid input parameters",
        "details": {
            "field": "prompt",
            "constraint": "required"
        },
        "request_id": "req_error_123"
    }


@pytest.fixture
def mock_qolaba_api_responses():
    """Mock API responses for different endpoints."""
    return {
        "text-to-image": {
            "success": {
                "status_code": 200,
                "json": {
                    "task_id": "task_12345",
                    "status": "pending",
                    "created_at": "2025-09-13T10:00:00Z"
                }
            },
            "error": {
                "status_code": 400,
                "json": {
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid prompt"
                }
            }
        },
        "task-status": {
            "success": {
                "status_code": 200,
                "json": {
                    "task_id": "task_12345",
                    "status": "completed",
                    "progress": 100.0,
                    "result": {"image_url": "https://cdn.qolaba.ai/images/12345.jpg"}
                }
            },
            "not_found": {
                "status_code": 404,
                "json": {
                    "error_code": "TASK_NOT_FOUND",
                    "message": "Task not found"
                }
            }
        },
        "chat": {
            "success": {
                "status_code": 200,
                "json": {
                    "task_id": "chat_67890",
                    "status": "completed",
                    "result": {
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": "Hello! How can I help you?"
                                }
                            }
                        ]
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_qolaba_client():
    """Mock Qolaba API client for testing."""
    from unittest.mock import AsyncMock
    
    mock_client = AsyncMock()
    
    # Mock common API methods
    mock_client.text_to_image = AsyncMock()
    mock_client.image_to_image = AsyncMock()
    mock_client.inpainting = AsyncMock()
    mock_client.replace_background = AsyncMock()
    mock_client.text_to_speech = AsyncMock()
    mock_client.chat = AsyncMock()
    mock_client.stream_chat = AsyncMock()
    mock_client.store_in_vector_db = AsyncMock()
    mock_client.get_task_status = AsyncMock()
    
    return mock_client


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server instance for testing."""
    from unittest.mock import MagicMock
    
    mock_server = MagicMock()
    return mock_server


@pytest.fixture
async def async_mock_httpx_response():
    """Create async mock httpx response."""
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.headers = {"content-type": "application/json"}
    return mock_response
