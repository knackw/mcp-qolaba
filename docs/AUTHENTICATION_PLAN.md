# Authentication Mechanism Implementation Plan

## Overview
This document defines the implementation strategy for authentication mechanisms in the Qolaba API MCP Server, building on the existing configuration system and API documentation.

## Current Configuration Status
The `QolabaSettings` class in `src/qolaba_mcp_server/config/settings.py` already supports both authentication methods:

### API Key Authentication
- Environment Variable: `QOLABA_API_KEY`
- Secure handling via `SecretStr` 
- Detection via `auth_method` property

### OAuth 2.0 Client Credentials Flow
- Environment Variables: 
  - `QOLABA_CLIENT_ID`
  - `QOLABA_CLIENT_SECRET` (SecretStr)
  - `QOLABA_TOKEN_URL`
  - `QOLABA_SCOPE` (optional)
- Automatic detection when all required fields are present

## Authentication Implementation Strategy

### 1. Authentication Integration (aktuelle Implementierung)

Die Authentifizierung ist im `QolabaHTTPClient` integriert (`src/qolaba_mcp_server/api/client.py`).

- API-Key: Header `Authorization: Bearer <API_KEY>` wird automatisch gesetzt.
- OAuth2 Client Credentials: Token-Refresh, Expiry-Puffer (5 Min), Header-Setzung integriert.
- Backoff/Retry auf 401 (einmaliger Refresh) und 429 berücksichtigt.

Ein separater `AuthenticationManager` ist derzeit nicht erforderlich. Falls künftige Projekte Auth als Cross-Cutting-Concern isolieren möchten, kann ein dedizierter Manager extrahiert werden, der von `QolabaHTTPClient` genutzt wird.

### 2. Authentication Flow Design

#### API Key Flow
1. Load API key from environment via settings
2. Include in Authorization header: `Bearer <API_KEY>`
3. No token refresh required

#### OAuth Flow
1. Check if access token exists and is valid
2. If expired/missing, request new token from `/auth/token`
3. Store token with expiration time
4. Include in Authorization header: `Bearer <ACCESS_TOKEN>`
5. Implement automatic token refresh

### 3. Error Handling Strategy

#### Authentication Errors
- **401 Unauthorized**: Invalid credentials
- **403 Forbidden**: Valid credentials but insufficient permissions
- **429 Rate Limited**: Too many authentication requests

#### Retry Logic
- OAuth token refresh on 401 errors
- Exponential backoff for rate limiting
- Maximum retry attempts: 3
- Log authentication failures appropriately

### 4. Security Considerations

#### Credential Protection
- Use SecretStr for all sensitive data
- Never log credentials or tokens
- Implement secure token storage in memory
- Clear tokens on application shutdown

#### Token Lifecycle Management
- Refresh tokens 5 minutes before expiration
- Handle token refresh failures gracefully
- Implement token revocation on logout/shutdown

### 5. Integration Points

#### Settings Integration
```python
# Authentication method detection (bereits implementiert)
@property
def auth_method(self) -> Literal["api_key", "oauth", "none"]:
    if self.client_id and self.client_secret and self.token_url:
        return "oauth"
    if self.api_key and self.api_key.get_secret_value():
        return "api_key"
    return "none"
```

#### HTTP Client Integration
- Inject authentication headers automatically
- Handle authentication errors transparently
- Support for authentication middleware

### 6. Configuration Validation

#### Environment Validation
`src/qolaba_mcp_server/config/settings.py` nutzt jetzt Pydantic v2 mit `BaseSettings` und `model_post_init`.

Auszug:

```python
class QolabaSettings(BaseSettings):
    ...
    def model_post_init(self, __context: Any) -> None:
        env = self.env
        if env in ("production", "staging"):
            is_api_key_auth = bool(self.api_key and self.api_key.get_secret_value())
            is_oauth = bool(self.client_id and self.client_secret and self.token_url)
            if is_api_key_auth and is_oauth:
                raise ValueError("Both API key and OAuth credentials are configured. Please provide only one.")
            if not is_api_key_auth and not is_oauth:
                raise ValueError("No authentication configured...")
```

#### Additional Validation Requirements
- Validate OAuth URL format
- Verify API key format if known
- Check network connectivity to OAuth endpoints

### 7. Testing Strategy

#### Unit Tests Required
- Authentication manager initialization
- API key header generation
- OAuth token request/refresh flow
- Token expiration handling
- Error scenarios and retries

#### Integration Tests Required
- End-to-end authentication flow
- Token refresh during long-running operations
- Authentication error handling
- Rate limiting behavior

#### Mock Strategy
- Mock OAuth token endpoint responses
- Simulate various error conditions
- Test token expiration scenarios

### 8. Monitoring and Logging

#### Authentication Metrics
- Authentication success/failure rates
- Token refresh frequency
- Authentication latency
- Rate limiting incidents

#### Logging Requirements
- Authentication attempts (without credentials)
- Token refresh events
- Authentication failures with error codes
- Rate limiting warnings

#### Log Format Example
```python
logger.info("Authentication successful", extra={
    "auth_method": "oauth",
    "token_expires_in": 3600,
    "request_id": "uuid"
})

logger.warning("Authentication failed", extra={
    "auth_method": "api_key", 
    "error_code": 401,
    "retry_attempt": 1
})
```

### 9. Performance Considerations

#### Token Caching
- In-memory token storage
- Thread-safe token access
- Minimal token refresh overhead

#### Connection Reuse
- Reuse HTTP connections for token requests
- Connection pooling for OAuth endpoints
- Timeout configuration for auth requests

### 10. Implementation Phases

#### Phase 1: Basic Authentication
- Implement AuthenticationManager class
- Add API key authentication support
- Basic error handling

#### Phase 2: OAuth Implementation  
- Add OAuth token request flow
- Implement token refresh logic
- Enhanced error handling and retries

#### Phase 3: Advanced Features
- Token lifecycle management
- Comprehensive logging and monitoring
- Performance optimizations

## Dependencies

### Required Libraries
- `aiohttp` or `httpx`: HTTP client for OAuth requests
- `datetime`: Token expiration handling
- `asyncio`: Asynchronous operation support

### Integration Dependencies
- `QolabaSettings` from config module
- HTTP client module (to be implemented in API-003)
- Logging configuration

## Validation Criteria

### API-002 Task Completion
- [x] Authentication mechanisms identified (API Key + OAuth)
- [x] Implementation strategy documented
- [x] Integration with existing configuration planned
- [x] Error handling strategy defined
- [x] Security considerations addressed
- [x] Testing approach outlined

### Success Metrics
- All authentication methods properly detected
- Secure credential handling implemented
- Automatic token refresh working
- Comprehensive error handling
- Zero credential leakage in logs
- Authentication latency < 200ms (excluding network)

This plan provides the foundation for implementing robust authentication handling in the subsequent API client development phase (API-003).