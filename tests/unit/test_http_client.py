import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from src.qolaba_mcp_server.api.client import (
    AuthenticationError,
    HTTPClientError,
    HTTPResponse,
    QolabaHTTPClient,
    RateLimitError,
    TimeoutError,
    create_client,
)
from src.qolaba_mcp_server.config.settings import QolabaSettings


@pytest.fixture
def api_key_settings():
    """Settings with API key authentication."""
    return QolabaSettings(
        env="test",
        api_base_url="https://api.test.com",
        api_key=SecretStr("test-api-key"),
        request_timeout=30.0,
        verify_ssl=True
    )


@pytest.fixture
def oauth_settings():
    """Settings with OAuth authentication."""
    return QolabaSettings(
        env="test",
        api_base_url="https://api.test.com",
        client_id="test-client-id",
        client_secret=SecretStr("test-client-secret"),
        token_url="https://auth.test.com/token",
        scope="read write",
        request_timeout=30.0,
        verify_ssl=True
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


class TestQolabaHTTPClient:
    """Test cases for QolabaHTTPClient."""
    
    def test_init_with_api_key_settings(self, api_key_settings):
        """Test client initialization with API key settings."""
        client = QolabaHTTPClient(api_key_settings)
        
        assert client.settings == api_key_settings
        assert client.settings.auth_method == "api_key"
        assert client.max_retries == 3
        assert client.base_delay == 1.0
        assert client.jitter is True
    
    def test_init_with_oauth_settings(self, oauth_settings):
        """Test client initialization with OAuth settings."""
        client = QolabaHTTPClient(oauth_settings)
        
        assert client.settings == oauth_settings
        assert client.settings.auth_method == "oauth"
    
    def test_create_client_function(self, api_key_settings):
        """Test create_client convenience function."""
        client = create_client(api_key_settings)
        assert isinstance(client, QolabaHTTPClient)
        assert client.settings == api_key_settings
    
    @pytest.mark.asyncio
    async def test_context_manager(self, api_key_settings):
        """Test async context manager functionality."""
        with patch.object(QolabaHTTPClient, '_ensure_client') as mock_ensure:
            mock_client = AsyncMock()
            mock_ensure.return_value = mock_client
            
            async with QolabaHTTPClient(api_key_settings) as client:
                assert isinstance(client, QolabaHTTPClient)
                mock_ensure.assert_called_once()
            
            # Verify close was called
            assert client._client is None
    
    @pytest.mark.asyncio
    async def test_ensure_client_initialization(self, api_key_settings):
        """Test HTTP client initialization."""
        client = QolabaHTTPClient(api_key_settings)
        
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_instance = AsyncMock()
            mock_httpx.return_value = mock_instance
            
            result = await client._ensure_client()
            
            assert result == mock_instance
            mock_httpx.assert_called_once()
            
            # Verify client configuration
            call_kwargs = mock_httpx.call_args[1]
            assert isinstance(call_kwargs['timeout'], httpx.Timeout)
            assert call_kwargs['verify'] == api_key_settings.verify_ssl
            assert isinstance(call_kwargs['limits'], httpx.Limits)
    
    @pytest.mark.asyncio
    async def test_ensure_client_with_proxies(self):
        """Test HTTP client initialization with proxy settings."""
        settings = QolabaSettings(
            env="test",
            api_key=SecretStr("test-key"),
            http_proxy="http://proxy:8080",
            https_proxy="https://proxy:8080"
        )
        
        client = QolabaHTTPClient(settings)
        
        with patch('httpx.AsyncClient') as mock_httpx:
            await client._ensure_client()
            
            call_kwargs = mock_httpx.call_args[1]
            expected_proxies = {
                "http://": "http://proxy:8080",
                "https://": "https://proxy:8080"
            }
            assert call_kwargs['proxies'] == expected_proxies
    
    @pytest.mark.asyncio
    async def test_close(self, api_key_settings):
        """Test client cleanup."""
        client = QolabaHTTPClient(api_key_settings)
        
        # Mock client
        mock_client = AsyncMock()
        client._client = mock_client
        client._oauth_token = "test-token"
        client._token_expires_at = datetime.utcnow()
        
        await client.close()
        
        mock_client.aclose.assert_called_once()
        assert client._client is None
        assert client._oauth_token is None
        assert client._token_expires_at is None
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_api_key(self, api_key_settings):
        """Test authentication header generation for API key."""
        client = QolabaHTTPClient(api_key_settings)
        
        headers = await client._get_auth_headers()
        
        assert headers == {"Authorization": "Bearer test-api-key"}
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_oauth(self, oauth_settings):
        """Test authentication header generation for OAuth."""
        client = QolabaHTTPClient(oauth_settings)
        client._oauth_token = "test-oauth-token"
        client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        headers = await client._get_auth_headers()
        
        assert headers == {"Authorization": "Bearer test-oauth-token"}
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_oauth_refresh_needed(self, oauth_settings):
        """Test OAuth token refresh when token is expired."""
        client = QolabaHTTPClient(oauth_settings)
        
        with patch.object(client, '_refresh_oauth_token') as mock_refresh:
            mock_refresh.return_value = None
            client._oauth_token = "refreshed-token"
            
            headers = await client._get_auth_headers()
            
            mock_refresh.assert_called_once()
            assert headers == {"Authorization": "Bearer refreshed-token"}
    
    def test_is_token_expired_no_token(self, oauth_settings):
        """Test token expiration check when no token exists."""
        client = QolabaHTTPClient(oauth_settings)
        assert client._is_token_expired() is True
    
    def test_is_token_expired_valid_token(self, oauth_settings):
        """Test token expiration check with valid token."""
        client = QolabaHTTPClient(oauth_settings)
        client._oauth_token = "valid-token"
        client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        assert client._is_token_expired() is False
    
    def test_is_token_expired_expired_token(self, oauth_settings):
        """Test token expiration check with expired token."""
        client = QolabaHTTPClient(oauth_settings)
        client._oauth_token = "expired-token"
        client._token_expires_at = datetime.utcnow() - timedelta(hours=1)
        
        assert client._is_token_expired() is True
    
    @pytest.mark.asyncio
    async def test_refresh_oauth_token_success(self, oauth_settings):
        """Test successful OAuth token refresh."""
        client = QolabaHTTPClient(oauth_settings)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-token",
            "token_type": "bearer",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        
        with patch.object(client, '_ensure_client', return_value=mock_client):
            await client._refresh_oauth_token()
            
            assert client._oauth_token == "new-token"
            assert client._token_expires_at is not None
            
            # Verify request was made correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == oauth_settings.token_url
    
    @pytest.mark.asyncio
    async def test_refresh_oauth_token_failure(self, oauth_settings):
        """Test OAuth token refresh failure."""
        client = QolabaHTTPClient(oauth_settings)
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid client"
        
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        
        with patch.object(client, '_ensure_client', return_value=mock_client):
            with pytest.raises(AuthenticationError, match="OAuth token refresh failed: 400"):
                await client._refresh_oauth_token()
    
    def test_calculate_delay(self, api_key_settings):
        """Test retry delay calculation."""
        client = QolabaHTTPClient(api_key_settings)
        
        # Test without jitter
        client.jitter = False
        assert client._calculate_delay(0) == 1.0
        assert client._calculate_delay(1) == 2.0
        assert client._calculate_delay(2) == 4.0
        
        # Test with jitter
        client.jitter = True
        delay = client._calculate_delay(0)
        assert 0.75 <= delay <= 1.25  # ±25% jitter
    
    def test_should_retry_exceptions(self, api_key_settings):
        """Test retry logic for exceptions."""
        client = QolabaHTTPClient(api_key_settings)
        
        # Should retry on network errors
        assert client._should_retry(None, httpx.ConnectError("Connection failed")) is True
        assert client._should_retry(None, httpx.TimeoutException("Timeout")) is True
        assert client._should_retry(None, httpx.NetworkError("Network error")) is True
        
        # Should not retry on other exceptions
        assert client._should_retry(None, ValueError("Invalid value")) is False
    
    def test_should_retry_status_codes(self, api_key_settings):
        """Test retry logic for HTTP status codes."""
        client = QolabaHTTPClient(api_key_settings)
        
        # Mock responses with different status codes
        def make_mock_response(status_code):
            mock_response = MagicMock()
            mock_response.status_code = status_code
            return mock_response
        
        # Should retry on server errors
        assert client._should_retry(make_mock_response(500), None) is True
        assert client._should_retry(make_mock_response(502), None) is True
        assert client._should_retry(make_mock_response(503), None) is True
        
        # Should retry on rate limit
        assert client._should_retry(make_mock_response(429), None) is True
        
        # Should retry on request timeout
        assert client._should_retry(make_mock_response(408), None) is True
        
        # Should not retry on client errors
        assert client._should_retry(make_mock_response(400), None) is False
        assert client._should_retry(make_mock_response(404), None) is False
        
        # Should not retry on success
        assert client._should_retry(make_mock_response(200), None) is False
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, api_key_settings):
        """Test successful HTTP request."""
        client = QolabaHTTPClient(api_key_settings)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json", "x-request-id": "req-123"}
        mock_response.json.return_value = {"result": "success"}
        
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        
        with patch.object(client, '_ensure_client', return_value=mock_client):
            response = await client._make_request("GET", "/test")
            
            assert isinstance(response, HTTPResponse)
            assert response.status_code == 200
            assert response.content == {"result": "success"}
            assert response.request_id == "req-123"
            assert response.response_time_ms is not None
            
            # Verify request was made with correct headers
            call_args = mock_client.request.call_args
            headers = call_args[1]['headers']
            assert "Authorization" in headers
            assert headers["User-Agent"] == "QolabaAPIClient/1.0"
    
    @pytest.mark.asyncio
    async def test_make_request_with_base_url(self, api_key_settings):
        """Test request URL construction with base URL."""
        client = QolabaHTTPClient(api_key_settings)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {}
        
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        
        with patch.object(client, '_ensure_client', return_value=mock_client):
            await client._make_request("GET", "endpoint")
            
            call_args = mock_client.request.call_args
            assert call_args[1]['url'] == "https://api.test.com/endpoint"
    
    @pytest.mark.asyncio
    async def test_make_request_authentication_error(self, api_key_settings):
        """Test handling of authentication errors."""
        client = QolabaHTTPClient(api_key_settings)
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"error": "Unauthorized"}
        
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        
        with patch.object(client, '_ensure_client', return_value=mock_client):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                await client._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_error(self, api_key_settings):
        """Test handling of rate limit errors."""
        client = QolabaHTTPClient(api_key_settings)

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"content-type": "application/json", "Retry-After": "1"}  # Short retry time
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_response.text = '{"error": "Rate limit exceeded"}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, '_ensure_client', return_value=mock_client):
            with patch('asyncio.sleep') as mock_sleep:  # Mock sleep to avoid actual waiting
                with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                    await client._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_with_retries(self, api_key_settings):
        """Test request retry mechanism."""
        client = QolabaHTTPClient(api_key_settings)
        client.max_retries = 2

        # First two calls fail, third succeeds
        responses = [
            MagicMock(status_code=500, headers={}, text='{"error": "Server error"}', content=b'{"error": "Server error"}', json=lambda: {"error": "Server error"}),
            MagicMock(status_code=500, headers={}, text='{"error": "Server error"}', content=b'{"error": "Server error"}', json=lambda: {"error": "Server error"}),
            MagicMock(status_code=200, headers={"content-type": "application/json"}, text='{"result": "success"}', content=b'{"result": "success"}', json=lambda: {"result": "success"})
        ]

        mock_client = AsyncMock()
        mock_client.request.side_effect = responses

        with patch.object(client, '_ensure_client', return_value=mock_client):
            with patch('asyncio.sleep') as mock_sleep:  # Speed up test
                response = await client._make_request("GET", "/test")

                assert response.status_code == 200
                assert response.content == {"result": "success"}
                assert mock_client.request.call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_make_request_network_error_with_retries(self, api_key_settings):
        """Test network error handling with retries."""
        client = QolabaHTTPClient(api_key_settings)
        client.max_retries = 2
        
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.ConnectError("Connection failed")
        
        with patch.object(client, '_ensure_client', return_value=mock_client):
            with patch('asyncio.sleep'):
                with pytest.raises(TimeoutError, match="Request failed after 3 attempts"):
                    await client._make_request("GET", "/test")
                
                assert mock_client.request.call_count == 3  # Original + 2 retries
    
    @pytest.mark.asyncio
    async def test_http_methods(self, api_key_settings):
        """Test all HTTP method convenience functions."""
        client = QolabaHTTPClient(api_key_settings)
        
        mock_response = HTTPResponse(
            status_code=200,
            headers={},
            content={"result": "success"}
        )
        
        with patch.object(client, '_make_request', return_value=mock_response) as mock_make_request:
            # Test GET
            await client.get("/test", params={"param": "value"})
            mock_make_request.assert_called_with("GET", "/test", params={"param": "value"})
            
            # Test POST
            await client.post("/test", json={"data": "value"})
            mock_make_request.assert_called_with("POST", "/test", json={"data": "value"}, data=None)
            
            # Test PUT
            await client.put("/test", json={"data": "value"})
            mock_make_request.assert_called_with("PUT", "/test", json={"data": "value"}, data=None)
            
            # Test PATCH
            await client.patch("/test", json={"data": "value"})
            mock_make_request.assert_called_with("PATCH", "/test", json={"data": "value"}, data=None)
            
            # Test DELETE
            await client.delete("/test")
            mock_make_request.assert_called_with("DELETE", "/test")


class TestHTTPResponse:
    """Test cases for HTTPResponse model."""
    
    def test_http_response_creation(self):
        """Test HTTPResponse model creation."""
        response = HTTPResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            content={"result": "success"},
            request_id="req-123",
            response_time_ms=150.5
        )
        
        assert response.status_code == 200
        assert response.headers == {"content-type": "application/json"}
        assert response.content == {"result": "success"}
        assert response.request_id == "req-123"
        assert response.response_time_ms == 150.5
    
    def test_http_response_optional_fields(self):
        """Test HTTPResponse with optional fields."""
        response = HTTPResponse(
            status_code=404,
            headers={},
            content="Not Found"
        )
        
        assert response.status_code == 404
        assert response.request_id is None
        assert response.response_time_ms is None


class TestHTTPClientExceptions:
    """Test cases for HTTP client exceptions."""
    
    def test_http_client_error(self):
        """Test HTTPClientError exception."""
        response = HTTPResponse(status_code=400, headers={}, content="Bad Request")
        error = HTTPClientError("Test error", status_code=400, response=response)
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.response == response
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError("Auth failed", status_code=401)
        
        assert str(error) == "Auth failed"
        assert error.status_code == 401
        assert isinstance(error, HTTPClientError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        error = RateLimitError("Rate limit exceeded", status_code=429)
        
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429
        assert isinstance(error, HTTPClientError)
    
    def test_timeout_error(self):
        """Test TimeoutError exception."""
        error = TimeoutError("Request timeout")
        
        assert str(error) == "Request timeout"
        assert isinstance(error, HTTPClientError)