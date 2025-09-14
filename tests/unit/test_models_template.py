"""
Test template for Qolaba API data models and validation.

This module provides test templates for testing Pydantic models, validation logic,
data conversion utilities, and exception handling.
"""

import pytest
from pydantic import ValidationError
import json
from pathlib import Path

# Import the models we want to test
from qolaba_mcp_server.models.api_models import (
    TextToImageRequest,
    ImageToImageRequest,
    ChatRequest,
    ChatMessage,
    TaskStatusResponse,
    QolabaException,
    ValidationException,
    create_error_from_http_status,
    validate_image_data,
    convert_image_to_base64,
    normalize_model_name
)


class TestTextToImageRequest:
    """Test template for TextToImageRequest model validation."""

    def test_valid_request_creation(self):
        """Test creating a valid text-to-image request."""
        request_data = {
            "prompt": "A beautiful landscape",
            "model": "flux",
            "width": 512,
            "height": 512,
            "steps": 20,
            "guidance_scale": 7.5
        }
        
        request = TextToImageRequest(**request_data)
        
        assert request.prompt == "A beautiful landscape"
        assert request.model == "flux"
        assert request.width == 512
        assert request.height == 512
        assert request.steps == 20
        assert request.guidance_scale == 7.5

    def test_prompt_validation_empty(self):
        """Test prompt validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            TextToImageRequest(prompt="", model="flux")
        
        assert "Prompt cannot be empty" in str(exc_info.value)

    def test_prompt_validation_too_long(self):
        """Test prompt validation with overly long string."""
        long_prompt = "A" * 1001  # Exceeds max length of 1000
        
        with pytest.raises(ValidationError) as exc_info:
            TextToImageRequest(prompt=long_prompt, model="flux")
        
        assert "Prompt too long" in str(exc_info.value)

    def test_width_height_bounds(self):
        """Test width and height boundary validation."""
        # Test minimum bounds
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", width=32)  # Below minimum 64
            
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", height=32)  # Below minimum 64
        
        # Test maximum bounds
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", width=4096)  # Above maximum 2048
            
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", height=4096)  # Above maximum 2048

    def test_steps_validation(self):
        """Test steps parameter validation."""
        # Test minimum
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", steps=0)
        
        # Test maximum
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", steps=101)
        
        # Test valid range
        request = TextToImageRequest(prompt="test", steps=50)
        assert request.steps == 50

    def test_guidance_scale_validation(self):
        """Test guidance scale parameter validation."""
        # Test minimum
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", guidance_scale=0.5)
        
        # Test maximum  
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", guidance_scale=25.0)
        
        # Test valid range
        request = TextToImageRequest(prompt="test", guidance_scale=10.0)
        assert request.guidance_scale == 10.0

    def test_seed_validation(self):
        """Test seed parameter validation."""
        # Test negative seed
        with pytest.raises(ValidationError):
            TextToImageRequest(prompt="test", seed=-1)
        
        # Test valid seed
        request = TextToImageRequest(prompt="test", seed=42)
        assert request.seed == 42
        
        # Test no seed (optional)
        request = TextToImageRequest(prompt="test")
        assert request.seed is None

    def test_default_values(self):
        """Test model default values."""
        request = TextToImageRequest(prompt="test")
        
        assert request.model == "flux"
        assert request.width == 512
        assert request.height == 512
        assert request.steps == 20
        assert request.guidance_scale == 7.5
        assert request.seed is None
        assert request.negative_prompt is None


class TestChatRequest:
    """Test template for ChatRequest model validation."""

    def test_valid_chat_request(self):
        """Test creating a valid chat request."""
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        request = ChatRequest(messages=messages)
        
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
        assert request.messages[0].content == "Hello"
        assert request.model == "gpt-4"
        assert request.temperature == 0.7

    def test_empty_messages_validation(self):
        """Test validation with empty messages list."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(messages=[])
        
        assert "Messages cannot be empty" in str(exc_info.value)

    def test_too_many_messages_validation(self):
        """Test validation with too many messages."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(51)]
        
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(messages=messages)
        
        assert "Too many messages" in str(exc_info.value)

    def test_message_role_validation(self):
        """Test message role validation."""
        with pytest.raises(ValidationError):
            ChatRequest(messages=[{"role": "invalid", "content": "test"}])

    def test_temperature_bounds(self):
        """Test temperature parameter bounds."""
        messages = [{"role": "user", "content": "test"}]
        
        # Test minimum
        with pytest.raises(ValidationError):
            ChatRequest(messages=messages, temperature=-0.1)
        
        # Test maximum
        with pytest.raises(ValidationError):
            ChatRequest(messages=messages, temperature=2.1)
        
        # Test valid range
        request = ChatRequest(messages=messages, temperature=1.0)
        assert request.temperature == 1.0


class TestTaskStatusResponse:
    """Test template for TaskStatusResponse model."""

    def test_valid_task_status(self):
        """Test creating a valid task status response."""
        data = {
            "task_id": "task_12345",
            "status": "completed",
            "progress": 100.0,
            "result": {"image_url": "https://example.com/image.jpg"}
        }
        
        response = TaskStatusResponse(**data)
        
        assert response.task_id == "task_12345"
        assert response.status == "completed"
        assert response.progress == 100.0
        assert response.result["image_url"] == "https://example.com/image.jpg"

    def test_status_validation(self):
        """Test status field validation."""
        with pytest.raises(ValidationError):
            TaskStatusResponse(
                task_id="test",
                status="invalid_status",
                progress=0.0
            )

    def test_progress_bounds(self):
        """Test progress percentage bounds."""
        # Test minimum
        with pytest.raises(ValidationError):
            TaskStatusResponse(
                task_id="test",
                status="pending",
                progress=-1.0
            )
        
        # Test maximum
        with pytest.raises(ValidationError):
            TaskStatusResponse(
                task_id="test",
                status="completed",
                progress=101.0
            )


class TestExceptionHandling:
    """Test template for exception classes and error handling."""

    def test_qolaba_exception_creation(self):
        """Test QolabaException creation and properties."""
        exception = QolabaException(
            message="Test error",
            error_code="TEST_ERROR",
            category="validation",
            http_status=400
        )
        
        assert exception.message == "Test error"
        assert exception.error_code == "TEST_ERROR"
        assert exception.category == "validation"
        assert exception.http_status == 400

    def test_validation_exception_creation(self):
        """Test ValidationException with field details."""
        exception = ValidationException(
            message="Invalid field",
            field="prompt",
            value="",
            constraint="required"
        )
        
        assert exception.category == "validation"
        assert exception.http_status == 400
        assert exception.field == "prompt"
        assert exception.details["field"] == "prompt"

    def test_create_error_from_http_status(self):
        """Test error creation from HTTP status codes."""
        # Test 400 - Bad Request
        error = create_error_from_http_status(400, "Bad request")
        assert isinstance(error, ValidationException)
        assert error.http_status == 400
        
        # Test 401 - Unauthorized
        error = create_error_from_http_status(401, "Unauthorized")
        assert error.http_status == 401
        assert error.category == "authentication"
        
        # Test 500 - Server Error
        error = create_error_from_http_status(500, "Internal error")
        assert error.http_status == 500
        assert error.category == "server_error"

    def test_exception_to_dict(self):
        """Test exception serialization to dictionary."""
        exception = QolabaException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        error_dict = exception.to_dict()
        
        assert error_dict["message"] == "Test error"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["details"]["key"] == "value"

    def test_exception_to_detailed_error(self):
        """Test exception conversion to DetailedQolabaError model."""
        exception = QolabaException(
            message="Test error",
            error_code="TEST_ERROR"
        )
        
        detailed_error = exception.to_detailed_error()
        
        assert detailed_error.message == "Test error"
        assert detailed_error.error_code == "TEST_ERROR"
        assert detailed_error.timestamp is not None


class TestDataConversionUtilities:
    """Test template for data conversion and validation utilities."""

    def test_validate_image_data_url(self):
        """Test image data validation with URL."""
        valid_url = "https://example.com/image.jpg"
        result = validate_image_data(valid_url)
        assert result is True

    def test_validate_image_data_base64(self):
        """Test image data validation with base64."""
        # TODO: Implement when validate_image_data is available
        pass

    def test_convert_image_to_base64(self):
        """Test image to base64 conversion."""
        # TODO: Implement when convert_image_to_base64 is available
        pass

    def test_normalize_model_name(self):
        """Test model name normalization."""
        assert normalize_model_name("FLUX", "image") == "flux"
        assert normalize_model_name("Stable-Diffusion", "image") == "stable-diffusion"
        assert normalize_model_name("  GPT-4  ", "text") == "gpt-4"

    def test_model_serialization(self):
        """Test model JSON serialization."""
        request = TextToImageRequest(
            prompt="test",
            width=1024,
            height=768
        )
        
        json_str = request.model_dump_json()
        data = json.loads(json_str)
        
        assert data["prompt"] == "test"
        assert data["width"] == 1024
        assert data["height"] == 768

    def test_model_deserialization(self):
        """Test model creation from JSON."""
        json_data = {
            "prompt": "A test image",
            "model": "flux",
            "width": 512,
            "height": 512
        }
        
        request = TextToImageRequest(**json_data)
        
        assert request.prompt == "A test image"
        assert request.model == "flux"


class TestModelLoadingFromFiles:
    """Test template for loading test data from files."""

    def test_load_text_to_image_request(self, test_data_dir):
        """Test loading text-to-image request from JSON file."""
        json_file = test_data_dir / "text_to_image_request.json"
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
            
            request = TextToImageRequest(**data)
            assert request.prompt is not None
            assert request.model is not None

    def test_load_error_response(self, test_data_dir):
        """Test loading error response from JSON file.""" 
        json_file = test_data_dir / "error_response.json"
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
            
            assert data["error_code"] is not None
            assert data["message"] is not None