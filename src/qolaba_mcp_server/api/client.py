from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, Type
from types import TracebackType
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from ..config.settings import QolabaSettings, get_settings
from ..core.logging_config import (
    get_module_logger, 
    get_performance_logger, 
    get_error_logger,
    RequestContext,
    request_id_var
)
from ..core.metrics import get_metrics_collector, MetricLabels


logger = get_module_logger("api.client")
perf_logger = get_performance_logger("api.client")
error_logger = get_error_logger("api.client")
metrics_collector = get_metrics_collector()


class HTTPResponse(BaseModel):
    """Standardized HTTP response model."""
    status_code: int
    headers: Dict[str, str]
    content: Union[Dict[str, Any], str, bytes]
    request_id: Optional[str] = None
    response_time_ms: Optional[float] = None


class HTTPClientError(Exception):
    """Base exception for HTTP client errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[HTTPResponse] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(HTTPClientError):
    """Raised when authentication fails."""
    pass


class RateLimitError(HTTPClientError):
    """Raised when rate limit is exceeded."""
    pass


class TimeoutError(HTTPClientError):
    """Raised when request times out."""
    pass


class QolabaHTTPClient:
    """
    Async HTTP client for Qolaba API with comprehensive error handling,
    authentication management, and retry mechanisms.
    
    Features:
    - Automatic authentication handling (API Key & OAuth)
    - Exponential backoff with jitter for retries
    - Connection pooling and session management
    - Rate limiting awareness
    - Comprehensive error handling
    - Request/response logging
    - SSL verification and proxy support
    """
    
    def __init__(self, settings: Optional[QolabaSettings] = None):
        self.settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = None
        self._oauth_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0  # seconds
        self.backoff_factor = 2.0
        self.jitter = True
        
        logger.info("Qolaba HTTP Client initialized", extra={
            "auth_method": self.settings.auth_method,
            "base_url": self.settings.api_base_url,
            "timeout": self.settings.request_timeout
        })
    
    async def __aenter__(self) -> "QolabaHTTPClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            # Build proxy configuration
            proxies = {}
            if self.settings.http_proxy:
                proxies["http://"] = self.settings.http_proxy
            if self.settings.https_proxy:
                proxies["https://"] = self.settings.https_proxy
            
            # Configure client with connection pooling
            limits = httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0
            )
            
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.request_timeout),
                verify=self.settings.verify_ssl,
                proxies=proxies if proxies else None,
                limits=limits,
                follow_redirects=True
            )
            
            logger.debug("HTTP client initialized", extra={
                "verify_ssl": self.settings.verify_ssl,
                "proxies_configured": bool(proxies),
                "timeout": self.settings.request_timeout
            })
        
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._oauth_token = None
            self._token_expires_at = None
            logger.debug("HTTP client closed")
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on configured auth method."""
        headers = {}
        
        if self.settings.auth_method == "api_key":
            api_key = self.settings.api_key.get_secret_value()
            headers["Authorization"] = f"Bearer {api_key}"
            
        elif self.settings.auth_method == "oauth":
            token = await self._get_oauth_token()
            headers["Authorization"] = f"Bearer {token}"
            
        return headers
    
    async def _get_oauth_token(self) -> str:
        """Get OAuth access token, refreshing if necessary."""
        if self._is_token_expired():
            await self._refresh_oauth_token()
        
        if not self._oauth_token:
            raise AuthenticationError("Failed to obtain OAuth token")
            
        return self._oauth_token
    
    def _is_token_expired(self) -> bool:
        """Check if current OAuth token is expired."""
        if not self._oauth_token or not self._token_expires_at:
            return True
        
        # Refresh 5 minutes before expiration
        buffer_time = timedelta(minutes=5)
        return datetime.utcnow() + buffer_time >= self._token_expires_at
    
    async def _refresh_oauth_token(self) -> None:
        """Refresh OAuth access token."""
        if not all([self.settings.client_id, self.settings.client_secret, self.settings.token_url]):
            raise AuthenticationError("OAuth credentials not properly configured")
        
        client = await self._ensure_client()
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret.get_secret_value()
        }
        
        if self.settings.scope:
            data["scope"] = self.settings.scope
        
        try:
            response = await client.post(
                self.settings.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._oauth_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info("OAuth token refreshed successfully", extra={
                "expires_in": expires_in,
                "token_type": token_data.get("token_type", "bearer")
            })
            
        except httpx.HTTPStatusError as e:
            logger.error("OAuth token refresh failed", extra={
                "status_code": e.response.status_code,
                "response": e.response.text
            })
            raise AuthenticationError(f"OAuth token refresh failed: {e.response.status_code}")
        except Exception as e:
            logger.error("OAuth token refresh error", extra={"error": str(e)})
            raise AuthenticationError(f"OAuth token refresh error: {e}")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry with exponential backoff and jitter."""
        delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
        
        if self.jitter:
            # Add random jitter of ±25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def _should_retry(self, response: Optional[httpx.Response], exception: Optional[Exception]) -> bool:
        """Determine if request should be retried."""
        if exception:
            # Retry on network errors, timeouts
            if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
                return True
            return False
        
        if response:
            # Retry on server errors (5xx) and certain client errors
            if response.status_code >= 500:
                return True
            if response.status_code == 429:  # Rate limit
                return True
            if response.status_code == 408:  # Request timeout
                return True
        
        return False
    
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HTTPResponse:
        """Make HTTP request with retry logic."""
        client = await self._ensure_client()
        request_headers = headers or {}
        
        # Add authentication headers
        auth_headers = await self._get_auth_headers()
        request_headers.update(auth_headers)
        
        # Add tracing header if available
        try:
            current_request_id = request_id_var.get(None)
        except Exception:
            current_request_id = None
        if current_request_id and "X-Request-ID" not in {k.title(): v for k, v in request_headers.items()}:
            request_headers["X-Request-ID"] = current_request_id

        # Add default headers
        request_headers.setdefault("User-Agent", "QolabaAPIClient/1.0")
        request_headers.setdefault("Accept", "application/json")
        
        # Build full URL
        if self.settings.api_base_url:
            full_url = urljoin(self.settings.api_base_url.rstrip("/") + "/", url.lstrip("/"))
        else:
            full_url = url
        
        # Calculate request size for performance logging
        request_size = 0
        if 'json' in kwargs:
            import json
            request_size = len(json.dumps(kwargs['json']).encode('utf-8'))
        elif 'data' in kwargs:
            request_size = len(str(kwargs['data']).encode('utf-8'))
        
        last_exception = None
        last_response = None
        
        logger.info(f"Starting API request: {method.upper()} {full_url}", extra={
            "method": method.upper(),
            "url": full_url,
            "request_size_bytes": request_size,
            "request_id": current_request_id
        })
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                logger.debug("Making HTTP request", extra={
                    "method": method.upper(),
                    "url": full_url,
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries + 1
                })
                
                response = await client.request(
                    method=method.upper(),
                    url=full_url,
                    headers=request_headers,
                    **kwargs
                )
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Handle authentication errors
                if response.status_code == 401:
                    if self.settings.auth_method == "oauth":
                        # Try to refresh token once
                        if attempt == 0:
                            logger.info("Received 401, refreshing OAuth token")
                            await self._refresh_oauth_token()
                            auth_headers = await self._get_auth_headers()
                            request_headers.update(auth_headers)
                            continue
                    raise AuthenticationError("Authentication failed", response.status_code)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and attempt < self.max_retries:
                        delay = float(retry_after)
                        logger.warning("Rate limit exceeded, waiting", extra={
                            "retry_after": delay,
                            "attempt": attempt + 1
                        })
                        await asyncio.sleep(delay)
                        continue
                    raise RateLimitError("Rate limit exceeded", response.status_code)
                
                # Parse response content
                content_type = response.headers.get("content-type", "").lower()
                response_size = 0
                if "application/json" in content_type:
                    try:
                        content = response.json()
                        response_size = len(response.text.encode('utf-8'))
                    except Exception as e:
                        content = response.text
                        response_size = len(content.encode('utf-8'))
                        logger.warning("Failed to parse JSON response", extra={
                            "error": str(e),
                            "content_preview": content[:200]
                        })
                elif content_type.startswith("text/"):
                    content = response.text
                    response_size = len(content.encode('utf-8'))
                else:
                    content = response.content
                    response_size = len(content) if isinstance(content, bytes) else len(str(content))
                
                http_response = HTTPResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=content,
                    request_id=response.headers.get("x-request-id"),
                    response_time_ms=response_time_ms
                )
                
                # Log successful response with performance metrics
                logger.info("HTTP request completed", extra={
                    "method": method.upper(),
                    "url": full_url,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "request_id": http_response.request_id,
                    "response_size_bytes": response_size
                })
                
                # Log performance metrics
                perf_logger.log_api_call(
                    endpoint=url,
                    method=method.upper(),
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    request_size=request_size,
                    response_size=response_size,
                    error=None
                )
                
                # Record metrics for monitoring
                metrics_collector.record_api_request(
                    endpoint=url,
                    method=method.upper(),
                    status_code=response.status_code,
                    duration_seconds=response_time_ms / 1000.0,
                    error_type=None
                )
                
                # Check for HTTP errors (4xx, 5xx)
                if response.status_code >= 400:
                    # Log HTTP error with detailed information
                    error_logger.log_http_error(
                        url=full_url,
                        method=method.upper(),
                        status_code=response.status_code,
                        response_text=content if isinstance(content, str) else str(content),
                        request_id=http_response.request_id
                    )
                    
                    # Log performance metrics for failed requests
                    error_message = content.get('message', 'HTTP Error') if isinstance(content, dict) else str(content)
                    perf_logger.log_api_call(
                        endpoint=url,
                        method=method.upper(),
                        status_code=response.status_code,
                        response_time_ms=response_time_ms,
                        request_size=request_size,
                        response_size=response_size,
                        error=error_message
                    )
                    
                    # Record error metrics for monitoring
                    error_type = "http_error"
                    if response.status_code == 429:
                        error_type = "rate_limit"
                    elif response.status_code == 401:
                        error_type = "authentication"
                    elif response.status_code == 403:
                        error_type = "authorization"
                    elif response.status_code >= 500:
                        error_type = "server_error"
                    elif response.status_code >= 400:
                        error_type = "client_error"
                    
                    metrics_collector.record_api_request(
                        endpoint=url,
                        method=method.upper(),
                        status_code=response.status_code,
                        duration_seconds=response_time_ms / 1000.0,
                        error_type=error_type
                    )
                    
                    if self._should_retry(response, None) and attempt < self.max_retries:
                        last_response = response
                        delay = self._calculate_delay(attempt)
                        logger.warning("Request failed, retrying", extra={
                            "status_code": response.status_code,
                            "attempt": attempt + 1,
                            "delay": delay,
                            "error_message": error_message
                        })
                        await asyncio.sleep(delay)
                        continue
                    
                    # Raise appropriate error
                    error_msg = f"HTTP {response.status_code}"
                    if isinstance(content, dict) and "message" in content:
                        error_msg += f": {content['message']}"
                    
                    raise HTTPClientError(error_msg, response.status_code, http_response)
                
                return http_response
                
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                response_time_ms = (time.time() - start_time) * 1000
                
                # Log network exception with detailed context
                error_logger.log_exception(
                    exception=e,
                    context={
                        "url": full_url,
                        "method": method.upper(),
                        "attempt": attempt + 1,
                        "response_time_ms": response_time_ms,
                        "request_size_bytes": request_size
                    },
                    user_message=f"Network error during API request to {url}"
                )
                
                # Log performance metrics for network errors
                perf_logger.log_api_call(
                    endpoint=url,
                    method=method.upper(),
                    status_code=0,  # No HTTP status for network errors
                    response_time_ms=response_time_ms,
                    request_size=request_size,
                    response_size=0,
                    error=f"{type(e).__name__}: {str(e)}"
                )
                
                # Record network error metrics for monitoring
                error_type = "network_error"
                if isinstance(e, httpx.TimeoutException):
                    error_type = "timeout"
                elif isinstance(e, httpx.ConnectError):
                    error_type = "connection_error"
                elif isinstance(e, httpx.NetworkError):
                    error_type = "network_error"
                
                metrics_collector.record_api_request(
                    endpoint=url,
                    method=method.upper(),
                    status_code=0,  # No HTTP status for network errors
                    duration_seconds=response_time_ms / 1000.0,
                    error_type=error_type
                )
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning("Network error, retrying", extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1,
                        "delay": delay,
                        "url": full_url
                    })
                    await asyncio.sleep(delay)
                    continue
                
                raise TimeoutError(f"Request failed after {attempt + 1} attempts: {e}")
        
        # If we get here, all retries failed
        if last_exception:
            raise TimeoutError(f"Request failed after {self.max_retries + 1} attempts: {last_exception}")
        elif last_response:
            raise HTTPClientError(f"Request failed with status {last_response.status_code}", last_response.status_code)
        else:
            raise HTTPClientError("Request failed for unknown reason")
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> HTTPResponse:
        """Make GET request."""
        return await self._make_request("GET", url, params=params, **kwargs)
    
    async def post(self, url: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, **kwargs) -> HTTPResponse:
        """Make POST request."""
        return await self._make_request("POST", url, json=json, data=data, **kwargs)
    
    async def put(self, url: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, **kwargs) -> HTTPResponse:
        """Make PUT request."""
        return await self._make_request("PUT", url, json=json, data=data, **kwargs)
    
    async def patch(self, url: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, **kwargs) -> HTTPResponse:
        """Make PATCH request."""
        return await self._make_request("PATCH", url, json=json, data=data, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> HTTPResponse:
        """Make DELETE request."""
        return await self._make_request("DELETE", url, **kwargs)


# Convenience function to create client instance
def create_client(settings: Optional[QolabaSettings] = None) -> QolabaHTTPClient:
    """Create a new QolabaHTTPClient instance."""
    return QolabaHTTPClient(settings)