"""
Comprehensive unit tests for Qolaba API client.

This module provides complete test coverage for the QolabaHTTPClient class,
including all HTTP methods, authentication mechanisms, error handling,
retry logic, and edge cases.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import httpx
from pydantic import ValidationError

from qolaba_mcp_server.api.client import (
    QolabaHTTPClient,
    HTTPResponse,
    HTTPClientError,
    AuthenticationError,
    RateLimitError,
    TimeoutError
)
from qolaba_mcp_server.config.settings import QolabaSettings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.auth_method = "api_key"

    # Mock SecretStr api_key
    mock_api_key = MagicMock()
    mock_api_key.get_secret_value.return_value = "test_api_key"
    settings.api_key = mock_api_key

    settings.api_base_url = "https://api.qolaba.ai/v1"
    settings.request_timeout = 30.0
    settings.verify_ssl = True
    settings.http_proxy = None
    settings.https_proxy = None
    return settings


@pytest.fixture
def oauth_settings():
    """Create OAuth settings for testing."""
    settings = MagicMock()
    settings.auth_method = "oauth"
    settings.client_id = "test_client_id"

    # Mock SecretStr client_secret
    mock_client_secret = MagicMock()
    mock_client_secret.get_secret_value.return_value = "test_client_secret"
    settings.client_secret = mock_client_secret

    settings.token_url = "https://api.qolaba.ai/oauth/token"
    settings.scope = "api"
    settings.api_base_url = "https://api.qolaba.ai/v1"
    settings.request_timeout = 30.0
    settings.verify_ssl = True
    settings.http_proxy = None
    settings.https_proxy = None
    return settings


@pytest.fixture
def http_client(mock_settings):
    """Create HTTP client with mock settings."""
    return QolabaHTTPClient(mock_settings)


@pytest.fixture
def oauth_client(oauth_settings):
    """Create HTTP client with OAuth settings."""
    return QolabaHTTPClient(oauth_settings)


class TestHTTPResponse:
    """Test HTTPResponse model."""

    def test_http_response_creation(self):
        """Test creating HTTPResponse with all fields."""
        response = HTTPResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            content={"success": True},
            request_id="req_12345",
            response_time_ms=123.45
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.content["success"] is True
        assert response.request_id == "req_12345"
        assert response.response_time_ms == 123.45

    def test_http_response_minimal(self):
        """Test creating HTTPResponse with minimal fields."""
        response = HTTPResponse(
            status_code=404,
            headers={},
            content="Not found"
        )
        
        assert response.status_code == 404
        assert response.headers == {}
        assert response.content == "Not found"
        assert response.request_id is None
        assert response.response_time_ms is None

    def test_http_response_different_content_types(self):
        """Test HTTPResponse with different content types."""
        # JSON content
        json_response = HTTPResponse(status_code=200, headers={}, content={"data": "test"})
        assert isinstance(json_response.content, dict)
        
        # String content
        text_response = HTTPResponse(status_code=200, headers={}, content="plain text")
        assert isinstance(text_response.content, str)
        
        # Binary content (note: pydantic may convert bytes to str in some versions)
        binary_response = HTTPResponse(status_code=200, headers={}, content=b"binary data")
        # Accept both bytes and str since pydantic handling can vary
        assert isinstance(binary_response.content, (str, bytes))


class TestHTTPClientExceptions:
    """Test HTTP client exception classes."""

    def test_http_client_error_creation(self):
        """Test HTTPClientError with all parameters."""
        http_response = HTTPResponse(status_code=400, headers={}, content={"error": "bad request"})
        error = HTTPClientError("Test error", 400, http_response)
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.response == http_response

    def test_authentication_error(self):
        """Test AuthenticationError inheritance."""
        error = AuthenticationError("Auth failed", 401)
        
        assert isinstance(error, HTTPClientError)
        assert str(error) == "Auth failed"
        assert error.status_code == 401

    def test_rate_limit_error(self):
        """Test RateLimitError inheritance."""
        error = RateLimitError("Rate limit exceeded", 429)
        
        assert isinstance(error, HTTPClientError)
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429

    def test_timeout_error(self):
        """Test TimeoutError inheritance."""
        error = TimeoutError("Request timeout")
        
        assert isinstance(error, HTTPClientError)
        assert str(error) == "Request timeout"


class TestQolabaHTTPClient:
    """Test QolabaHTTPClient class."""

    def test_client_initialization(self, mock_settings):
        """Test client initialization with settings."""
        client = QolabaHTTPClient(mock_settings)
        
        assert client.settings == mock_settings
        assert client._client is None
        assert client._oauth_token is None
        assert client._token_expires_at is None
        assert client.max_retries == 3
        assert client.base_delay == 1.0
        assert client.max_delay == 60.0

    def test_client_initialization_default_settings(self):
        """Test client initialization with default settings."""
        with patch('qolaba_mcp_server.api.client.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings
            
            client = QolabaHTTPClient()
            
            assert client.settings == mock_settings
            mock_get_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, http_client):
        """Test async context manager functionality."""
        with patch.object(http_client, '_ensure_client') as mock_ensure:
            with patch.object(http_client, 'close') as mock_close:
                mock_ensure.return_value = AsyncMock()
                
                async with http_client as client:
                    assert client == http_client
                    mock_ensure.assert_called_once()
                
                mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_client_creation(self, http_client):
        """Test HTTP client creation."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            client = await http_client._ensure_client()
            
            assert client == mock_client
            assert http_client._client == mock_client
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_client_with_proxies(self, mock_settings):
        """Test HTTP client creation with proxy configuration."""
        mock_settings.http_proxy = "http://proxy:8080"
        mock_settings.https_proxy = "https://proxy:8443"
        
        client = QolabaHTTPClient(mock_settings)
        
        with patch('httpx.AsyncClient') as mock_client_class:
            await client._ensure_client()
            
            call_args = mock_client_class.call_args
            assert call_args.kwargs['proxies']['http://'] == "http://proxy:8080"
            assert call_args.kwargs['proxies']['https://'] == "https://proxy:8443"

    @pytest.mark.asyncio
    async def test_close_client(self, http_client):
        """Test closing HTTP client."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        http_client._oauth_token = "test_token"
        http_client._token_expires_at = datetime.utcnow()
        
        await http_client.close()
        
        mock_client.aclose.assert_called_once()
        assert http_client._client is None
        assert http_client._oauth_token is None
        assert http_client._token_expires_at is None

    @pytest.mark.asyncio
    async def test_get_auth_headers_api_key(self, http_client):
        """Test authentication headers with API key."""
        headers = await http_client._get_auth_headers()
        
        assert headers["Authorization"] == "Bearer test_api_key"

    @pytest.mark.asyncio
    async def test_get_auth_headers_oauth(self, oauth_client):
        """Test authentication headers with OAuth."""
        oauth_client._oauth_token = "oauth_token_123"
        oauth_client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        headers = await oauth_client._get_auth_headers()
        
        assert headers["Authorization"] == "Bearer oauth_token_123"

    def test_is_token_expired_no_token(self, oauth_client):
        """Test token expiration check with no token."""
        assert oauth_client._is_token_expired() is True

    def test_is_token_expired_expired_token(self, oauth_client):
        """Test token expiration check with expired token."""
        oauth_client._oauth_token = "token"
        oauth_client._token_expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        assert oauth_client._is_token_expired() is True

    def test_is_token_expired_valid_token(self, oauth_client):
        """Test token expiration check with valid token."""
        oauth_client._oauth_token = "token"
        oauth_client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        assert oauth_client._is_token_expired() is False

    def test_is_token_expired_near_expiry(self, oauth_client):
        """Test token expiration check near expiry (should refresh 5 minutes before)."""
        oauth_client._oauth_token = "token"
        oauth_client._token_expires_at = datetime.utcnow() + timedelta(minutes=3)
        
        assert oauth_client._is_token_expired() is True

    @pytest.mark.asyncio
    async def test_refresh_oauth_token_success(self, oauth_client):
        """Test successful OAuth token refresh."""
        mock_client = AsyncMock()
        oauth_client._client = mock_client

        # Use MagicMock for synchronous json() method
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_token_123",
            "expires_in": 3600,
            "token_type": "bearer"
        }
        mock_client.post.return_value = mock_response
        
        await oauth_client._refresh_oauth_token()
        
        assert oauth_client._oauth_token == "new_token_123"
        assert oauth_client._token_expires_at is not None
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_oauth_token_missing_credentials(self, oauth_settings):
        """Test OAuth token refresh with missing credentials."""
        oauth_settings.client_id = None
        client = QolabaHTTPClient(oauth_settings)
        
        with pytest.raises(AuthenticationError, match="OAuth credentials not properly configured"):
            await client._refresh_oauth_token()

    @pytest.mark.asyncio
    async def test_refresh_oauth_token_http_error(self, oauth_client):
        """Test OAuth token refresh with HTTP error."""
        mock_client = AsyncMock()
        oauth_client._client = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)
        mock_client.post.side_effect = error
        
        with pytest.raises(AuthenticationError, match="OAuth token refresh failed: 401"):
            await oauth_client._refresh_oauth_token()

    def test_calculate_delay(self, http_client):
        """Test retry delay calculation."""
        # Test exponential backoff
        delay_0 = http_client._calculate_delay(0)
        delay_1 = http_client._calculate_delay(1)
        delay_2 = http_client._calculate_delay(2)
        
        assert delay_0 >= 0
        assert delay_1 > delay_0
        assert delay_2 > delay_1

    def test_calculate_delay_max_cap(self, http_client):
        """Test retry delay maximum cap (with jitter consideration)."""
        # Disable jitter for precise testing
        http_client.jitter = False
        delay = http_client._calculate_delay(10)  # Very high attempt number
        assert delay <= http_client.max_delay

        # Test with jitter - should be within reasonable bounds (max + 25% jitter)
        http_client.jitter = True
        delay_with_jitter = http_client._calculate_delay(10)
        assert delay_with_jitter <= http_client.max_delay * 1.25

    def test_calculate_delay_without_jitter(self, http_client):
        """Test retry delay calculation without jitter."""
        http_client.jitter = False
        
        delay_0 = http_client._calculate_delay(0)
        delay_1 = http_client._calculate_delay(1)
        
        assert delay_0 == http_client.base_delay
        assert delay_1 == http_client.base_delay * http_client.backoff_factor

    def test_should_retry_network_errors(self, http_client):
        """Test retry decision for network errors."""
        connect_error = httpx.ConnectError("Connection failed")
        timeout_error = httpx.TimeoutException("Timeout")
        network_error = httpx.NetworkError("Network issue")
        
        assert http_client._should_retry(None, connect_error) is True
        assert http_client._should_retry(None, timeout_error) is True
        assert http_client._should_retry(None, network_error) is True

    def test_should_retry_server_errors(self, http_client):
        """Test retry decision for server errors."""
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_408 = MagicMock()
        mock_response_408.status_code = 408
        
        assert http_client._should_retry(mock_response_500, None) is True
        assert http_client._should_retry(mock_response_429, None) is True
        assert http_client._should_retry(mock_response_408, None) is True

    def test_should_not_retry_client_errors(self, http_client):
        """Test retry decision for client errors."""
        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400
        
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        
        assert http_client._should_retry(mock_response_400, None) is False
        assert http_client._should_retry(mock_response_404, None) is False

    @pytest.mark.asyncio
    async def test_make_request_success(self, http_client):
        """Test successful HTTP request."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json", "x-request-id": "req_123"}
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_client.request.return_value = mock_response
        
        with patch.object(http_client, '_get_auth_headers', return_value={"Authorization": "Bearer test"}):
            result = await http_client._make_request("GET", "/test")
        
        assert isinstance(result, HTTPResponse)
        assert result.status_code == 200
        assert result.content == {"success": True}
        assert result.request_id == "req_123"

    @pytest.mark.asyncio
    async def test_make_request_with_auth_retry(self, oauth_client):
        """Test request with authentication retry."""
        mock_client = AsyncMock()
        oauth_client._client = mock_client
        
        # First response: 401 Unauthorized
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        
        # Second response: Success after token refresh
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.headers = {"content-type": "application/json"}
        mock_response_200.json.return_value = {"success": True}
        
        mock_client.request.side_effect = [mock_response_401, mock_response_200]
        
        with patch.object(oauth_client, '_refresh_oauth_token') as mock_refresh:
            with patch.object(oauth_client, '_get_auth_headers', return_value={"Authorization": "Bearer new_token"}):
                result = await oauth_client._make_request("GET", "/test")
        
        assert result.status_code == 200
        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_retry(self, http_client):
        """Test request with rate limit retry."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        # First response: 429 Rate Limited
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "2"}
        
        # Second response: Success
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.headers = {"content-type": "application/json"}
        mock_response_200.json.return_value = {"success": True}
        
        mock_client.request.side_effect = [mock_response_429, mock_response_200]
        
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(http_client, '_get_auth_headers', return_value={}):
                result = await http_client._make_request("GET", "/test")
        
        assert result.status_code == 200
        mock_sleep.assert_called_with(2.0)

    @pytest.mark.asyncio
    async def test_make_request_network_error_retry(self, http_client):
        """Test request with network error retry."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        # First attempt: Network error
        network_error = httpx.NetworkError("Connection failed")
        
        # Second attempt: Success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"success": True}
        
        mock_client.request.side_effect = [network_error, mock_response]
        
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(http_client, '_get_auth_headers', return_value={}):
                result = await http_client._make_request("GET", "/test")
        
        assert result.status_code == 200
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self, http_client):
        """Test request failure after max retries."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        http_client.max_retries = 1  # Set low for faster test
        
        # Always return network error
        network_error = httpx.NetworkError("Connection failed")
        mock_client.request.side_effect = network_error
        
        with patch('asyncio.sleep'):
            with patch.object(http_client, '_get_auth_headers', return_value={}):
                with pytest.raises(TimeoutError, match="Request failed after 2 attempts"):
                    await http_client._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_http_error(self, http_client):
        """Test request with HTTP error."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"message": "Not found"}
        mock_client.request.return_value = mock_response
        
        with patch.object(http_client, '_get_auth_headers', return_value={}):
            with pytest.raises(HTTPClientError, match="HTTP 404: Not found"):
                await http_client._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_different_content_types(self, http_client):
        """Test request with different response content types."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        # Test text response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Plain text response"
        mock_client.request.return_value = mock_response
        
        with patch.object(http_client, '_get_auth_headers', return_value={}):
            result = await http_client._make_request("GET", "/test")
        
        assert result.content == "Plain text response"

    @pytest.mark.asyncio
    async def test_http_methods(self, http_client):
        """Test all HTTP method convenience functions."""
        with patch.object(http_client, '_make_request') as mock_make_request:
            mock_make_request.return_value = HTTPResponse(status_code=200, headers={}, content={})
            
            # Test GET
            await http_client.get("/test", params={"key": "value"})
            mock_make_request.assert_called_with("GET", "/test", params={"key": "value"})
            
            # Test POST
            await http_client.post("/test", json={"data": "test"})
            mock_make_request.assert_called_with("POST", "/test", json={"data": "test"}, data=None)
            
            # Test PUT
            await http_client.put("/test", data={"field": "value"})
            mock_make_request.assert_called_with("PUT", "/test", json=None, data={"field": "value"})
            
            # Test PATCH
            await http_client.patch("/test", json={"update": "data"})
            mock_make_request.assert_called_with("PATCH", "/test", json={"update": "data"}, data=None)
            
            # Test DELETE
            await http_client.delete("/test")
            mock_make_request.assert_called_with("DELETE", "/test")


class TestQolabaHTTPClientIntegration:
    """Integration tests for QolabaHTTPClient."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_request_workflow(self):
        """Test complete request workflow with real HTTP client."""
        # This would be an integration test that uses real HTTP requests
        # For now, we'll skip this as it requires actual API access
        pytest.skip("Integration test requires real API access")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_workflow(self):
        """Test complete OAuth authentication workflow."""
        # This would test the full OAuth flow with a real OAuth server
        pytest.skip("Integration test requires real OAuth server")


class TestQolabaHTTPClientEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_malformed_json_response(self, http_client):
        """Test handling of malformed JSON response."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid JSON response"
        mock_client.request.return_value = mock_response
        
        with patch.object(http_client, '_get_auth_headers', return_value={}):
            result = await http_client._make_request("GET", "/test")
        
        assert result.content == "Invalid JSON response"

    @pytest.mark.asyncio
    async def test_missing_retry_after_header(self, http_client):
        """Test rate limit handling without Retry-After header."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}  # No Retry-After header
        mock_client.request.return_value = mock_response
        
        with patch.object(http_client, '_get_auth_headers', return_value={}):
            with pytest.raises(RateLimitError):
                await http_client._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_url_building(self, http_client):
        """Test URL building with base URL."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {}
        mock_client.request.return_value = mock_response
        
        with patch.object(http_client, '_get_auth_headers', return_value={}):
            await http_client._make_request("GET", "endpoint")
        
        # Check that the URL was built correctly
        call_args = mock_client.request.call_args
        assert call_args.kwargs['url'] == "https://api.qolaba.ai/v1/endpoint"

    def test_custom_retry_configuration(self, mock_settings):
        """Test custom retry configuration."""
        client = QolabaHTTPClient(mock_settings)
        client.max_retries = 5
        client.base_delay = 0.5
        client.max_delay = 30.0
        client.backoff_factor = 1.5
        
        assert client.max_retries == 5
        assert client.base_delay == 0.5
        assert client.max_delay == 30.0
        assert client.backoff_factor == 1.5