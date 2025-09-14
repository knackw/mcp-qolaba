"""
Example test file demonstrating the usage of mock strategies for TEST-002.

This file shows how to use the comprehensive mock strategies to test
the Qolaba API client without external dependencies.
"""

import pytest
from unittest.mock import patch, AsyncMock
from tests.utils.mock_strategies import (
    QolabaMockResponseGenerator,
    MockHTTPResponse,
    mock_qolaba_api_success,
    mock_qolaba_api_error,
    mock_qolaba_api_timeout,
    mock_qolaba_auth_failure,
    mock_qolaba_api_rate_limited,
    mock_qolaba_api_context,
    create_mock_api_client,
    create_test_scenarios
)


class TestMockStrategiesExamples:
    """Example tests demonstrating mock strategy usage."""
    
    @mock_qolaba_api_success(endpoint="text-to-image", model="flux", width=1024, height=1024)
    async def test_successful_text_to_image_with_decorator(self, mock_client):
        """Test successful text-to-image generation using success decorator."""
        # The decorator automatically mocks the API client
        response = await mock_client.text_to_image(
            prompt="A beautiful landscape",
            model="flux",
            width=1024,
            height=1024
        )
        
        # Verify response structure
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "completed"
        assert "image_url" in response_data["result"]
        assert response_data["result"]["metadata"]["model"] == "flux"
        assert response_data["result"]["metadata"]["width"] == 1024
    
    @mock_qolaba_api_error(status_code=400, error_code="VALIDATION_ERROR", 
                          message="Invalid prompt", details={"field": "prompt"})
    async def test_validation_error_with_decorator(self, mock_client):
        """Test API validation error using error decorator."""
        response = await mock_client.text_to_image(prompt="")
        
        # Verify error response
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "VALIDATION_ERROR"
        assert error_data["message"] == "Invalid prompt"
        assert error_data["details"]["field"] == "prompt"
    
    @mock_qolaba_api_timeout(timeout_duration=5.0)
    async def test_timeout_scenario(self, mock_client):
        """Test timeout handling using timeout decorator."""
        # The decorator configures the mock to raise TimeoutException
        with pytest.raises(Exception):  # httpx.TimeoutException
            await mock_client.text_to_image(prompt="Test prompt")
    
    @mock_qolaba_auth_failure(auth_error_type="invalid_key")
    async def test_authentication_failure(self, mock_client):
        """Test authentication failure using auth failure decorator."""
        response = await mock_client.text_to_image(prompt="Test prompt")
        
        assert response.status_code == 401
        error_data = response.json()
        assert error_data["error_code"] == "INVALID_API_KEY"
    
    @mock_qolaba_api_rate_limited(max_requests=2)
    async def test_rate_limiting_behavior(self, mock_client):
        """Test rate limiting behavior."""
        # First two requests should succeed
        await mock_client.text_to_image(prompt="First request")
        await mock_client.text_to_image(prompt="Second request")
        
        # Third request should fail with rate limit error
        with pytest.raises(Exception):  # HTTPStatusError with 429
            await mock_client.text_to_image(prompt="Third request")
    
    async def test_context_manager_usage(self):
        """Test using context manager for complex scenarios."""
        responses = {
            'text_to_image': MockHTTPResponse(
                200, QolabaMockResponseGenerator.text_to_image_success(model="custom_model")
            ),
            'chat': MockHTTPResponse(
                400, QolabaMockResponseGenerator.error_response("INVALID_INPUT", "Bad request")
            )
        }
        
        async with mock_qolaba_api_context(responses) as mock_client:
            # Text-to-image should succeed
            tti_response = await mock_client.text_to_image(prompt="Test")
            assert tti_response.status_code == 200
            
            # Chat should fail
            chat_response = await mock_client.chat(messages=[{"role": "user", "content": "Hi"}])
            assert chat_response.status_code == 400
    
    def test_mock_response_generator(self):
        """Test the mock response generator directly."""
        # Generate text-to-image success response
        response = QolabaMockResponseGenerator.text_to_image_success(
            model="test_model", width=512, height=512
        )
        
        assert response["status"] == "completed"
        assert response["result"]["metadata"]["model"] == "test_model"
        assert response["result"]["metadata"]["width"] == 512
        
        # Generate error response
        error = QolabaMockResponseGenerator.error_response(
            "TEST_ERROR", "Test error message", {"test_field": "test_value"}
        )
        
        assert error["error_code"] == "TEST_ERROR" 
        assert error["message"] == "Test error message"
        assert error["details"]["test_field"] == "test_value"
    
    def test_create_mock_api_client_helper(self):
        """Test the helper function for creating mock clients."""
        mock_client = create_mock_api_client()
        
        # Verify that default methods are configured
        assert hasattr(mock_client, 'text_to_image')
        assert hasattr(mock_client, 'chat')
        assert hasattr(mock_client, 'text_to_speech')
        
        # Test that mock responses are set up
        response = mock_client.text_to_image.return_value
        assert response.status_code == 200
    
    def test_test_scenarios_helper(self):
        """Test the test scenarios helper function."""
        scenarios = create_test_scenarios()
        
        # Verify all expected scenarios are present
        expected_scenarios = ["success", "validation_error", "auth_error", "rate_limit", "server_error"]
        for scenario in expected_scenarios:
            assert scenario in scenarios
            assert "status_code" in scenarios[scenario]
            assert "response_data" in scenarios[scenario]
        
        # Verify scenario data structure
        success_scenario = scenarios["success"]
        assert success_scenario["status_code"] == 200
        assert success_scenario["response_data"]["status"] == "completed"


class TestMockHTTPResponse:
    """Test the MockHTTPResponse class."""
    
    def test_mock_http_response_creation(self):
        """Test creating MockHTTPResponse instances."""
        # Test with JSON data
        response_data = {"status": "success", "data": "test"}
        response = MockHTTPResponse(200, response_data)
        
        assert response.status_code == 200
        assert response.json() == response_data
        assert response.headers["content-type"] == "application/json"
    
    def test_mock_http_response_error_status(self):
        """Test MockHTTPResponse with error status codes."""
        error_data = {"error": "Not found"}
        response = MockHTTPResponse(404, error_data)
        
        assert response.status_code == 404
        
        # Test that raise_for_status works
        with pytest.raises(Exception):  # httpx.HTTPStatusError
            response.raise_for_status()
    
    def test_mock_http_response_text_property(self):
        """Test the text property of MockHTTPResponse."""
        response_data = {"message": "hello"}
        response = MockHTTPResponse(200, response_data)
        
        # Text should be JSON string representation
        import json
        expected_text = json.dumps(response_data)
        assert response.text == expected_text


class TestAdvancedMockScenarios:
    """Test advanced mocking scenarios."""
    
    async def test_progressive_responses(self):
        """Test progressive API responses (pending -> completed)."""
        from tests.utils.mock_strategies import mock_qolaba_api_progressive_responses
        
        pending_response = MockHTTPResponse(
            200, QolabaMockResponseGenerator.text_to_image_pending()
        )
        completed_response = MockHTTPResponse(
            200, QolabaMockResponseGenerator.text_to_image_success()
        )
        
        with mock_qolaba_api_progressive_responses('text_to_image', 
                                                 [pending_response, completed_response]) as mock_client:
            # First call should return pending
            first_response = await mock_client.text_to_image(prompt="Test")
            assert first_response.json()["status"] == "pending"
            
            # Second call should return completed
            second_response = await mock_client.text_to_image(prompt="Test")
            assert second_response.json()["status"] == "completed"
    
    async def test_streaming_chat_mock(self):
        """Test streaming chat mock functionality."""
        from tests.utils.mock_strategies import mock_qolaba_streaming_chat
        
        messages = ["Hello", " there", "!"]
        
        async with mock_qolaba_streaming_chat(messages) as mock_client:
            stream = mock_client.stream_chat.return_value
            
            collected_messages = []
            async for chunk in stream:
                import json
                message_data = json.loads(chunk.decode('utf-8'))
                if message_data.get("delta", {}).get("content"):
                    collected_messages.append(message_data["delta"]["content"])
            
            assert collected_messages == messages
    
    def test_rate_limiter_class_directly(self):
        """Test the MockRateLimiter class directly."""
        from tests.utils.mock_strategies import MockRateLimiter
        
        rate_limiter = MockRateLimiter(max_requests=2)
        
        # First two requests should pass
        import asyncio
        
        async def run_test():
            await rate_limiter.check_rate_limit()  # 1st request
            await rate_limiter.check_rate_limit()  # 2nd request
            
            # 3rd request should raise exception
            with pytest.raises(Exception):
                await rate_limiter.check_rate_limit()
        
        asyncio.run(run_test())


# Integration test with actual server components (if they exist)
class TestMockIntegrationExamples:
    """Examples of how to use mocks with actual server components."""
    
    @mock_qolaba_api_success(endpoint="text-to-image")
    async def test_mcp_server_text_to_image_integration(self, mock_client):
        """Example of testing MCP server with mocked API client."""
        # This would test the actual MCP server handlers
        # with the API client being mocked
        
        # Mock API client is automatically configured by decorator
        # In a real integration test, you would:
        # 1. Create MCP server instance
        # 2. Call MCP handler method  
        # 3. Verify that handler calls the mocked API client correctly
        # 4. Verify MCP response format
        
        # For now, just verify the mock works as expected
        response = await mock_client.text_to_image(prompt="Integration test")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
    
    def test_mock_configuration_validation(self):
        """Test that mocks properly handle configuration scenarios."""
        # Test different configuration scenarios that might affect API client behavior
        mock_client = create_mock_api_client()
        
        # Mock client should have all expected methods
        expected_methods = ['text_to_image', 'image_to_image', 'text_to_speech', 'chat']
        for method_name in expected_methods:
            assert hasattr(mock_client, method_name)
            method = getattr(mock_client, method_name)
            assert callable(method)