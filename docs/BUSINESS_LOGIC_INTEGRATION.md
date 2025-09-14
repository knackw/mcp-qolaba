# MCP-004: Business Logic Integration Documentation

## Overview

This document describes the implementation of **MCP-004: Hauptgeschäftslogik zwischen MCP und API-Client verbinden** (Main business logic connection between MCP and API Client).

## Architecture

The business logic integration creates a unified orchestration layer that connects all previously implemented components:

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   MCP Tools     │    │  Business Logic      │    │  Qolaba API     │
│                 │────│   Orchestrator       │────│   Client        │
│ - text_to_image │    │                      │    │                 │
│ - chat          │    │ - Validation         │    │ - HTTP Client   │
│ - task_status   │    │ - API Coordination   │    │ - Rate Limiting │
│ - etc.          │    │ - Response Processing│    │ - Error Handling│
└─────────────────┘    └──────────────────────┘    └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │   Validation    │
                       │   Layer         │
                       │ - Pydantic      │
                       │ - Error Format  │
                       └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │   Response      │
                       │   Serialization │
                       │ - JSON Schema   │
                       │ - MCP Responses │
                       └─────────────────┘
```

## Components Integration

### 1. QolabaMCPOrchestrator

**Location:** `src/qolaba_mcp_server/core/business_logic.py`

Central orchestrator class that provides:

- **Unified Operation Execution**: Single entry point for all API operations
- **Request Validation**: Automatic validation using appropriate Pydantic models
- **API Communication**: Coordinated HTTP client usage with error handling
- **Response Processing**: Structured response creation and serialization
- **Request Tracing**: Optional request ID tracking through the entire flow

### 2. Operation Types

Supported operations through `OperationType` enum:

- `TEXT_TO_IMAGE` → `text-to-image` endpoint
- `IMAGE_TO_IMAGE` → `image-to-image` endpoint
- `INPAINTING` → `inpainting` endpoint
- `REPLACE_BACKGROUND` → `replace-background` endpoint
- `TEXT_TO_SPEECH` → `text-to-speech` endpoint
- `CHAT` → `chat` endpoint
- `STORE_VECTOR_DB` → `store-file-in-vector-database` endpoint
- `TASK_STATUS` → `task-status/{id}` endpoint

### 3. Convenience Functions

Pre-configured operation functions:

```python
# Text-to-Image
await execute_text_to_image(request_data, request_id)

# Chat
await execute_chat(request_data, request_id)

# Task Status
await get_task_status_unified(task_id, request_id)
```

## Integration Flow

### Standard Operation Flow

1. **MCP Tool Invocation**: User calls MCP tool (e.g., `text_to_image`)
2. **Data Preparation**: Tool prepares request data dictionary
3. **Business Logic Execution**: Call to orchestrator's `execute_operation()`
4. **Validation**: Automatic validation using appropriate Pydantic model
5. **API Call**: HTTP client execution with retry/rate limiting
6. **Response Processing**: Qolaba response → MCP response transformation
7. **Serialization**: Convert to standardized dictionary format
8. **Return**: Structured response back to MCP client

### Error Handling Flow

1. **Validation Errors**: Returned as structured validation error responses
2. **HTTP Errors**: Caught and converted to API error responses
3. **Unexpected Errors**: Logged and returned as internal error responses
4. **Response Format Errors**: Handled with fallback error responses

## Benefits

### 1. Centralized Logic
- Single point of control for all API operations
- Consistent error handling across all tools
- Unified logging and request tracing

### 2. Maintainability
- Clear separation of concerns
- Modular design allowing easy extension
- Consistent patterns across all operations

### 3. Reliability
- Comprehensive error handling
- Standardized response formats
- Request validation before API calls

### 4. Observability
- Request ID tracing through the entire flow
- Structured logging at each step
- Clear error reporting with suggestions

## Usage Examples

### Enhanced MCP Tool Implementation

```python
@mcp.tool("text_to_image_enhanced")
async def text_to_image_enhanced(ctx: Context, prompt: str, **kwargs) -> Dict[str, Any]:
    request_id = str(uuid4())

    request_data = {
        "prompt": prompt,
        **kwargs
    }

    # Single line executes the entire flow
    return await execute_text_to_image(request_data, request_id)
```

### Direct Orchestrator Usage

```python
orchestrator = get_orchestrator()
result = await orchestrator.execute_operation(
    OperationType.TEXT_TO_IMAGE,
    request_data,
    request_id
)
```

## Files Created/Modified

### New Files
- `src/qolaba_mcp_server/core/business_logic.py` - Main orchestrator implementation
- `src/qolaba_mcp_server/core/__init__.py` - Module exports
- `src/qolaba_mcp_server/server_enhanced.py` - Enhanced server demo
- `docs/BUSINESS_LOGIC_INTEGRATION.md` - This documentation

### Modified Files
- `src/qolaba_mcp_server/server.py` - Added business logic imports and documentation

## Testing

The business logic integration can be tested through:

1. **Enhanced Server**: Use `server_enhanced.py` for testing new patterns
2. **Unit Tests**: Test orchestrator components individually
3. **Integration Tests**: Test complete flows with mocked API responses
4. **Health Checks**: Use enhanced health check tools

## Future Enhancements

The orchestrator provides a foundation for:

- **Metrics Collection**: Request/response metrics and timing
- **Caching**: Response caching for repeated requests
- **Batch Operations**: Multiple API calls in single operation
- **Webhooks**: Event-driven response handling
- **Plugin System**: Custom operation handlers

## Completion Status

✅ **MCP-004 Implementation Complete**

- ✅ Central orchestrator implemented
- ✅ All operation types supported
- ✅ Validation integration functional
- ✅ API client coordination working
- ✅ Response processing unified
- ✅ Error handling standardized
- ✅ Documentation provided
- ✅ Enhanced server example created

The main business logic connection between MCP and API Client is now fully operational and ready for production use.