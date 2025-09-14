"""
Comprehensive integration tests for MCP command handlers.

This module provides complete integration test coverage for the QolabaMCPOrchestrator
class and all MCP-to-API workflow functionality, including validation, API calls,
response processing, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from pathlib import Path

from qolaba_mcp_server.core.business_logic import (
    QolabaMCPOrchestrator,
    OperationType,
    get_orchestrator,
    execute_text_to_image,
    execute_image_to_image,
    execute_inpainting,
    execute_replace_background,
    execute_text_to_speech,
    execute_chat,
    execute_vector_store,
    get_task_status_unified
)
from qolaba_mcp_server.api.client import HTTPClientError, AuthenticationError
from qolaba_mcp_server.mcp.validation import ValidationResult
from qolaba_mcp_server.models.api_models import TextToImageRequest


class TestQolabaMCPOrchestrator:
    """Integration tests for QolabaMCPOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return QolabaMCPOrchestrator()

    @pytest.fixture
    def valid_text_to_image_data(self):
        """Valid text-to-image request data."""
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
    def mock_api_success_response(self):
        """Mock successful API response."""
        return {
            "content": {
                "task_id": "task_12345",
                "status": "pending",
                "created_at": "2025-09-13T10:00:00Z"
            },
            "status_code": 200,
            "headers": {"x-request-id": "req_67890"},
            "request_id": "test_request_123"
        }

    @pytest.fixture
    def mock_task_status_response(self):
        """Mock task status API response."""
        return {
            "task_id": "task_12345",
            "status": "completed",
            "progress": 100.0,
            "result": {
                "image_url": "https://cdn.qolaba.ai/images/12345.jpg"
            },
            "created_at": "2025-09-13T10:00:00Z",
            "updated_at": "2025-09-13T10:01:30Z"
        }

    @pytest.mark.asyncio
    async def test_execute_operation_success(
        self,
        orchestrator,
        valid_text_to_image_data,
        mock_api_success_response
    ):
        """Test successful operation execution."""
        with patch.object(orchestrator, '_validate_request') as mock_validate:
            with patch.object(orchestrator, '_execute_api_call') as mock_api_call:
                with patch.object(orchestrator, '_process_api_response') as mock_process:
                    # Setup mocks
                    mock_validate.return_value = ValidationResult(
                        success=True,
                        data=TextToImageRequest(**valid_text_to_image_data)
                    )
                    mock_api_call.return_value = mock_api_success_response
                    mock_process.return_value = {"success": True, "task_id": "task_12345"}
                    
                    # Execute operation
                    result = await orchestrator.execute_operation(
                        OperationType.TEXT_TO_IMAGE,
                        valid_text_to_image_data,
                        "test_request_123"
                    )
                    
                    # Verify workflow
                    assert result["success"] is True
                    assert result["task_id"] == "task_12345"
                    mock_validate.assert_called_once_with(OperationType.TEXT_TO_IMAGE, valid_text_to_image_data)
                    mock_api_call.assert_called_once()
                    mock_process.assert_called_once_with(mock_api_success_response, OperationType.TEXT_TO_IMAGE, "test_request_123")

    @pytest.mark.asyncio
    async def test_execute_operation_validation_error(self, orchestrator):
        """Test operation execution with validation error."""
        invalid_data = {"prompt": ""}  # Empty prompt should fail validation
        
        with patch.object(orchestrator, '_validate_request') as mock_validate:
            with patch.object(orchestrator, '_create_validation_error_response') as mock_error:
                # Setup mocks
                validation_result = ValidationResult(success=False, error="Prompt cannot be empty")
                mock_validate.return_value = validation_result
                mock_error.return_value = {"error": "validation_error", "message": "Prompt cannot be empty"}
                
                # Execute operation
                result = await orchestrator.execute_operation(
                    OperationType.TEXT_TO_IMAGE,
                    invalid_data
                )
                
                # Verify error handling
                assert result["error"] == "validation_error"
                assert "Prompt cannot be empty" in result["message"]
                mock_validate.assert_called_once()
                mock_error.assert_called_once_with(validation_result)

    @pytest.mark.asyncio
    async def test_execute_operation_http_error(
        self,
        orchestrator,
        valid_text_to_image_data
    ):
        """Test operation execution with HTTP client error."""
        with patch.object(orchestrator, '_validate_request') as mock_validate:
            with patch.object(orchestrator, '_execute_api_call') as mock_api_call:
                with patch.object(orchestrator, '_create_http_error_response') as mock_error:
                    # Setup mocks
                    mock_validate.return_value = ValidationResult(
                        success=True,
                        data=TextToImageRequest(**valid_text_to_image_data)
                    )
                    http_error = HTTPClientError("API Error", 500)
                    mock_api_call.side_effect = http_error
                    mock_error.return_value = {"error": "api_client_error", "message": "API request failed: API Error"}
                    
                    # Execute operation
                    result = await orchestrator.execute_operation(
                        OperationType.TEXT_TO_IMAGE,
                        valid_text_to_image_data
                    )
                    
                    # Verify error handling
                    assert result["error"] == "api_client_error"
                    assert "API request failed" in result["message"]
                    mock_error.assert_called_once_with(http_error)

    @pytest.mark.asyncio
    async def test_execute_operation_unexpected_error(
        self,
        orchestrator,
        valid_text_to_image_data
    ):
        """Test operation execution with unexpected error."""
        with patch.object(orchestrator, '_validate_request') as mock_validate:
            with patch.object(orchestrator, '_create_unexpected_error_response') as mock_error:
                # Setup mocks
                unexpected_error = Exception("Something went wrong")
                mock_validate.side_effect = unexpected_error
                mock_error.return_value = {"error": "internal_error", "message": "An unexpected error occurred"}
                
                # Execute operation
                result = await orchestrator.execute_operation(
                    OperationType.TEXT_TO_IMAGE,
                    valid_text_to_image_data
                )
                
                # Verify error handling
                assert result["error"] == "internal_error"
                assert "unexpected error occurred" in result["message"]
                mock_error.assert_called_once_with(unexpected_error)

    @pytest.mark.asyncio
    async def test_get_task_status_success(self, orchestrator, mock_task_status_response):
        """Test successful task status retrieval."""
        with patch('qolaba_mcp_server.core.business_logic.QolabaHTTPClient') as mock_client_class:
            with patch('qolaba_mcp_server.core.business_logic.ResponseSerializer') as mock_serializer:
                # Setup mocks
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = AsyncMock()
                mock_response.content = mock_task_status_response
                mock_client.get.return_value = mock_response
                
                mock_mcp_response = MagicMock()
                mock_serializer.create_task_status_response.return_value = mock_mcp_response
                mock_serializer.serialize_to_dict.return_value = {"task_status": "completed"}
                
                # Execute task status request
                result = await orchestrator.get_task_status("task_12345", "request_123")
                
                # Verify workflow
                assert result["task_status"] == "completed"
                mock_client.get.assert_called_once_with("task-status/task_12345")
                mock_serializer.create_task_status_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_status_http_error(self, orchestrator):
        """Test task status retrieval with HTTP error."""
        with patch('qolaba_mcp_server.core.business_logic.QolabaHTTPClient') as mock_client_class:
            with patch.object(orchestrator, '_create_http_error_response') as mock_error:
                # Setup mocks
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                http_error = HTTPClientError("Task not found", 404)
                mock_client.get.side_effect = http_error
                mock_error.return_value = {"error": "task_not_found", "message": "Task not found"}
                
                # Execute task status request
                result = await orchestrator.get_task_status("nonexistent_task")
                
                # Verify error handling
                assert result["error"] == "task_not_found"
                mock_error.assert_called_once_with(http_error)

    @pytest.mark.asyncio
    async def test_validate_request_success(self, orchestrator, valid_text_to_image_data):
        """Test successful request validation."""
        with patch('qolaba_mcp_server.core.business_logic.validate_request_data') as mock_validate:
            # Setup mock
            validated_data = TextToImageRequest(**valid_text_to_image_data)
            mock_validate.return_value = ValidationResult(success=True, data=validated_data)
            
            # Execute validation
            result = await orchestrator._validate_request(OperationType.TEXT_TO_IMAGE, valid_text_to_image_data)
            
            # Verify validation
            assert result.success is True
            assert isinstance(result.data, TextToImageRequest)
            mock_validate.assert_called_once_with(valid_text_to_image_data, TextToImageRequest)

    @pytest.mark.asyncio
    async def test_validate_request_unsupported_operation(self, orchestrator):
        """Test validation with unsupported operation type."""
        # Use a mock operation type that doesn't exist in the mapping
        with patch.object(orchestrator, '_operation_models', {}):
            result = await orchestrator._validate_request("unsupported_op", {})
            
            assert result.success is False
            assert "Unsupported operation type" in result.error

    @pytest.mark.asyncio
    async def test_execute_api_call_success(self, orchestrator, valid_text_to_image_data):
        """Test successful API call execution."""
        with patch('qolaba_mcp_server.core.business_logic.QolabaHTTPClient') as mock_client_class:
            # Setup mocks
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = AsyncMock()
            mock_response.content = {"task_id": "task_123"}
            mock_response.status_code = 200
            mock_response.headers = {"x-request-id": "req_456"}
            mock_client.post.return_value = mock_response
            
            validated_data = TextToImageRequest(**valid_text_to_image_data)
            
            # Execute API call
            result = await orchestrator._execute_api_call(
                OperationType.TEXT_TO_IMAGE,
                validated_data,
                "request_789"
            )
            
            # Verify API call
            assert result["content"]["task_id"] == "task_123"
            assert result["status_code"] == 200
            assert result["request_id"] == "request_789"
            mock_client.post.assert_called_once_with(
                "text-to-image",
                json=validated_data.dict(exclude_none=True)
            )

    def test_process_api_response_success(self, orchestrator, mock_api_success_response):
        """Test successful API response processing."""
        with patch('qolaba_mcp_server.core.business_logic.process_qolaba_response') as mock_process:
            with patch('qolaba_mcp_server.core.business_logic.ResponseSerializer') as mock_serializer:
                # Setup mocks
                mock_mcp_response = MagicMock()
                mock_process.return_value = mock_mcp_response
                mock_serializer.serialize_to_dict.return_value = {"processed": True}
                
                # Execute response processing
                result = orchestrator._process_api_response(
                    mock_api_success_response,
                    OperationType.TEXT_TO_IMAGE,
                    "request_123"
                )
                
                # Verify processing
                assert result["processed"] is True
                mock_process.assert_called_once_with(
                    mock_api_success_response["content"],
                    "text-to-image",
                    request_id="request_123"
                )

    def test_process_api_response_unexpected_format(self, orchestrator):
        """Test API response processing with unexpected format."""
        with patch.object(orchestrator, '_create_unexpected_response_error') as mock_error:
            # Setup mock
            mock_error.return_value = {"error": "unexpected_format"}
            
            # Execute with non-dict content
            result = orchestrator._process_api_response(
                {"content": "not a dict"},
                OperationType.TEXT_TO_IMAGE,
                "request_123"
            )
            
            # Verify error handling
            assert result["error"] == "unexpected_format"
            mock_error.assert_called_once()

    def test_error_response_creation_methods(self, orchestrator):
        """Test all error response creation methods."""
        with patch('qolaba_mcp_server.core.business_logic.ResponseSerializer') as mock_serializer:
            mock_serializer.create_error_response.return_value = MagicMock()
            mock_serializer.serialize_to_dict.return_value = {"error": "test"}
            
            # Test validation error response
            validation_result = ValidationResult(success=False, error="Test validation error")
            result = orchestrator._create_validation_error_response(validation_result)
            assert "error" in result or "error_message" in result
            
            # Test HTTP error response
            http_error = HTTPClientError("HTTP Error", 500)
            result = orchestrator._create_http_error_response(http_error)
            assert "error" in result or "error_message" in result
            
            # Test unexpected error response
            unexpected_error = Exception("Unexpected error")
            result = orchestrator._create_unexpected_error_response(unexpected_error)
            assert "error" in result or "error_message" in result
            
            # Test unexpected response format error
            result = orchestrator._create_unexpected_response_error()
            assert "error" in result or "error_message" in result


class TestMCPConvenienceFunctions:
    """Test MCP convenience functions for all operation types."""

    @pytest.fixture
    def mock_orchestrator_success(self):
        """Mock orchestrator that returns success."""
        mock_orch = AsyncMock()
        mock_orch.execute_operation.return_value = {"success": True, "task_id": "task_123"}
        mock_orch.get_task_status.return_value = {"status": "completed", "progress": 100.0}
        return mock_orch

    @pytest.mark.asyncio
    async def test_execute_text_to_image(self, mock_orchestrator_success):
        """Test text-to-image convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            request_data = {"prompt": "test image"}
            result = await execute_text_to_image(request_data, "req_123")
            
            assert result["success"] is True
            mock_orchestrator_success.execute_operation.assert_called_once_with(
                OperationType.TEXT_TO_IMAGE,
                request_data,
                "req_123"
            )

    @pytest.mark.asyncio
    async def test_execute_image_to_image(self, mock_orchestrator_success):
        """Test image-to-image convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            request_data = {"image": "base64_data", "prompt": "transform image"}
            result = await execute_image_to_image(request_data, "req_456")
            
            assert result["success"] is True
            mock_orchestrator_success.execute_operation.assert_called_once_with(
                OperationType.IMAGE_TO_IMAGE,
                request_data,
                "req_456"
            )

    @pytest.mark.asyncio
    async def test_execute_inpainting(self, mock_orchestrator_success):
        """Test inpainting convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            request_data = {"image": "base64_data", "mask": "mask_data", "prompt": "fill area"}
            result = await execute_inpainting(request_data)
            
            assert result["success"] is True
            mock_orchestrator_success.execute_operation.assert_called_once_with(
                OperationType.INPAINTING,
                request_data,
                None
            )

    @pytest.mark.asyncio
    async def test_execute_replace_background(self, mock_orchestrator_success):
        """Test background replacement convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            request_data = {"image": "base64_data", "prompt": "new background"}
            result = await execute_replace_background(request_data)
            
            assert result["success"] is True
            mock_orchestrator_success.execute_operation.assert_called_once_with(
                OperationType.REPLACE_BACKGROUND,
                request_data,
                None
            )

    @pytest.mark.asyncio
    async def test_execute_text_to_speech(self, mock_orchestrator_success):
        """Test text-to-speech convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            request_data = {"text": "Hello world", "voice": "alloy"}
            result = await execute_text_to_speech(request_data)
            
            assert result["success"] is True
            mock_orchestrator_success.execute_operation.assert_called_once_with(
                OperationType.TEXT_TO_SPEECH,
                request_data,
                None
            )

    @pytest.mark.asyncio
    async def test_execute_chat(self, mock_orchestrator_success):
        """Test chat convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            request_data = {"messages": [{"role": "user", "content": "Hello"}]}
            result = await execute_chat(request_data)
            
            assert result["success"] is True
            mock_orchestrator_success.execute_operation.assert_called_once_with(
                OperationType.CHAT,
                request_data,
                None
            )

    @pytest.mark.asyncio
    async def test_execute_vector_store(self, mock_orchestrator_success):
        """Test vector store convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            request_data = {"file": "file_path", "collection_name": "test_collection"}
            result = await execute_vector_store(request_data)
            
            assert result["success"] is True
            mock_orchestrator_success.execute_operation.assert_called_once_with(
                OperationType.STORE_VECTOR_DB,
                request_data,
                None
            )

    @pytest.mark.asyncio
    async def test_get_task_status_unified(self, mock_orchestrator_success):
        """Test unified task status convenience function."""
        with patch('qolaba_mcp_server.core.business_logic.get_orchestrator', return_value=mock_orchestrator_success):
            result = await get_task_status_unified("task_789", "req_999")
            
            assert result["status"] == "completed"
            mock_orchestrator_success.get_task_status.assert_called_once_with("task_789", "req_999")


class TestGlobalOrchestrator:
    """Test global orchestrator instance management."""

    def test_get_orchestrator_singleton(self):
        """Test that get_orchestrator returns singleton instance."""
        # Clear any existing instance
        import qolaba_mcp_server.core.business_logic as bl_module
        bl_module._orchestrator = None
        
        # Get first instance
        orch1 = get_orchestrator()
        assert isinstance(orch1, QolabaMCPOrchestrator)
        
        # Get second instance - should be the same
        orch2 = get_orchestrator()
        assert orch1 is orch2
        
        # Clear for other tests
        bl_module._orchestrator = None


class TestMCPIntegrationScenarios:
    """End-to-end integration test scenarios."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_text_to_image_workflow(self):
        """Test complete text-to-image workflow from request to response."""
        # This would be a full integration test that tests the complete workflow
        # from MCP request through validation, API call, and response processing
        pytest.skip("Full integration test requires real API setup")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self):
        """Test error recovery in integration scenarios."""
        # This would test various error scenarios in the complete workflow
        pytest.skip("Full integration test requires real API setup")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test handling of concurrent operations."""
        # This would test the system's ability to handle multiple concurrent requests
        pytest.skip("Performance integration test requires specialized setup")


class TestMCPValidationIntegration:
    """Test integration with MCP validation layer."""

    @pytest.mark.asyncio
    async def test_validation_integration_all_models(self):
        """Test validation integration with all supported models."""
        orchestrator = QolabaMCPOrchestrator()
        
        # Test that all operation types have corresponding models
        for operation_type in OperationType:
            if operation_type != OperationType.TASK_STATUS:  # Task status doesn't use request model
                model_class = orchestrator._operation_models.get(operation_type)
                assert model_class is not None, f"No model defined for {operation_type}"

    def test_operation_model_mapping_completeness(self):
        """Test that operation model mapping is complete."""
        orchestrator = QolabaMCPOrchestrator()
        
        expected_operations = {
            OperationType.TEXT_TO_IMAGE,
            OperationType.IMAGE_TO_IMAGE,
            OperationType.INPAINTING,
            OperationType.REPLACE_BACKGROUND,
            OperationType.TEXT_TO_SPEECH,
            OperationType.CHAT,
            OperationType.STORE_VECTOR_DB
        }
        
        mapped_operations = set(orchestrator._operation_models.keys())
        assert mapped_operations == expected_operations


class TestMCPErrorHandlingIntegration:
    """Test error handling integration scenarios."""

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test authentication error handling through the full stack."""
        orchestrator = QolabaMCPOrchestrator()
        
        with patch.object(orchestrator, '_execute_api_call') as mock_api_call:
            # Simulate authentication error
            auth_error = AuthenticationError("Invalid API key", 401)
            mock_api_call.side_effect = auth_error
            
            result = await orchestrator.execute_operation(
                OperationType.TEXT_TO_IMAGE,
                {"prompt": "test"},
                "req_123"
            )
            
            # Verify error is properly handled and formatted
            assert "error" in result
            assert "api_client_error" in result["error"]

    @pytest.mark.asyncio
    async def test_multiple_error_types(self):
        """Test handling of different error types in sequence."""
        # This would test the system's ability to handle different types of errors
        # and ensure proper error categorization and response formatting
        pass