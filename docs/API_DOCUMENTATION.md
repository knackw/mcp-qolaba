# Qolaba API Documentation Analysis

## Overview
This document provides a comprehensive analysis of the Qolaba API endpoints and their integration requirements for the MCP server implementation.

**API Base URL:** `https://api.qolaba.ai`
**Environment Variable:** `QOLABA_API_BASE_URL`
**Documentation Sources:**
- Main API Platform: https://docs.qolaba.ai/api-platform
- Text-to-Image: https://docs.qolaba.ai/api-platform/text-to-image
- Image-to-Image: https://docs.qolaba.ai/api-platform/image-to-image
- Inpainting: https://docs.qolaba.ai/api-platform/inpainting
- Replace Background: https://docs.qolaba.ai/api-platform/replace-background
- Text-to-Speech: https://docs.qolaba.ai/api-platform/text-to-speech
- Task Status: https://docs.qolaba.ai/api-platform/task-status
- Stream Chat: https://docs.qolaba.ai/api-platform/streamchat
- Chat API: https://docs.qolaba.ai/api-platform/chat
- Vector Database: https://docs.qolaba.ai/api-platform/store-file-in-vector-database
- Pricing: https://docs.qolaba.ai/api-platform/pricing

## Qolaba API Endpoints Overview

The Qolaba API provides the following main service categories:

### 1. AI Image Generation Services
- **Text-to-Image**: Generate images from text descriptions
- **Image-to-Image**: Transform existing images based on prompts
- **Inpainting**: Fill or modify specific areas of images
- **Replace Background**: Change image backgrounds automatically

### 2. AI Audio Services
- **Text-to-Speech**: Convert text to natural-sounding speech

### 3. AI Chat Services
- **Chat API**: Standard chat completions
- **Stream Chat**: Real-time streaming chat responses

### 4. Task Management
- **Task Status**: Monitor the status of asynchronous operations

### 5. Data Services
- **Vector Database Storage**: Store and manage files in vector database

### 6. Platform Services
- **Pricing**: Access pricing information for API usage

## Authentication Mechanisms

### API Key Authentication
- **Method:** Bearer token in Authorization header
- **Header Format:** `Authorization: Bearer <API_KEY>`
- **Environment Variable:** `QOLABA_API_KEY`
- **Usage:** Required for all API endpoints

## Core API Endpoints

### Text-to-Image Generation

#### POST /text-to-image
- **Purpose:** Generate images from text descriptions
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** application/json
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/text-to-image
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/text-to-image

**Request Parameters:**
- `prompt` (required): Text description of the desired image
- `model`: AI model to use for generation
- `width`: Image width in pixels
- `height`: Image height in pixels
- `steps`: Number of inference steps
- `guidance_scale`: Adherence to prompt (typically 7.0-15.0)
- `seed`: Random seed for reproducible results
- `negative_prompt`: What to avoid in the generated image

### Image-to-Image Transformation

#### POST /image-to-image
- **Purpose:** Transform existing images based on text prompts
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** multipart/form-data
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/image-to-image
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/image-to-image

**Request Parameters:**
- `image` (required): Input image file
- `prompt` (required): Text description for transformation
- `strength`: Transformation strength (0.0-1.0)
- `guidance_scale`: Adherence to prompt
- `steps`: Number of inference steps
- `seed`: Random seed for reproducible results

### Inpainting

#### POST /inpainting
- **Purpose:** Fill or modify specific areas of images
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** multipart/form-data
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/inpainting
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/inpainting

**Request Parameters:**
- `image` (required): Input image file
- `mask` (required): Mask image indicating areas to modify
- `prompt` (required): Text description of desired content
- `guidance_scale`: Adherence to prompt
- `steps`: Number of inference steps
- `seed`: Random seed for reproducible results

### Replace Background

#### POST /replace-background
- **Purpose:** Automatically replace image backgrounds
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** multipart/form-data
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/replace-background
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/replace-background

**Request Parameters:**
- `image` (required): Input image file
- `background_prompt`: Description of new background
- `background_image`: Alternative background image
- `mask_threshold`: Threshold for automatic masking

### Text-to-Speech

#### POST /text-to-speech
- **Purpose:** Convert text to natural-sounding speech
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** application/json
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/text-to-speech
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/text-to-speech

**Request Parameters:**
- `text` (required): Text to convert to speech
- `voice`: Voice model to use
- `language`: Target language
- `speed`: Speech speed (0.25-4.0)
- `pitch`: Voice pitch adjustment

### Task Status Monitoring

#### GET /task-status/{task_id}
- **Purpose:** Check the status of asynchronous operations
- **Method:** GET
- **Authentication:** Required (API Key)
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/task-status
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/get-status

**Path Parameters:**
- `task_id` (required): Unique identifier of the task

**Response:**
```json
{
  "task_id": "string",
  "status": "pending|processing|completed|failed",
  "progress": 0.75,
  "result": {},
  "error": "string",
  "created_at": "2025-09-13T10:20:00Z",
  "completed_at": "2025-09-13T10:20:00Z"
}
```

### Chat Services

#### POST /chat
- **Purpose:** Standard chat completions
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** application/json
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/chat
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/chat-api

**Request Parameters:**
- `messages` (required): Array of conversation messages
- `model`: Chat model to use
- `temperature`: Response creativity (0.0-2.0)
- `max_tokens`: Maximum response length
- `stream`: Whether to stream response

#### POST /streamchat
- **Purpose:** Real-time streaming chat responses
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** application/json
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/streamchat
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/streamchat

**Request Parameters:**
- `messages` (required): Array of conversation messages
- `model`: Chat model to use
- `temperature`: Response creativity
- `max_tokens`: Maximum response length

### Vector Database Storage

#### POST /store-file-in-vector-database
- **Purpose:** Store and index files in vector database
- **Method:** POST
- **Authentication:** Required (API Key)
- **Content-Type:** multipart/form-data
- **Documentation:** 
  - https://docs.qolaba.ai/api-platform/store-file-in-vector-database
  - https://app.theneo.io/api-runner/qolaba/ml-apis/api-reference/store-file-in-vector-database

**Request Parameters:**
- `file` (required): File to store and index
- `collection_name`: Vector database collection
- `metadata`: Additional metadata for the file
- `chunk_size`: Text chunking size
- `overlap`: Chunk overlap size

### Pricing Information

#### GET /pricing
- **Purpose:** Retrieve pricing information for API usage
- **Method:** GET
- **Authentication:** Required (API Key)
- **Documentation:** https://docs.qolaba.ai/api-platform/pricing

## Common Response Patterns

### Successful Response Format
```json
{
  "success": true,
  "data": {},
  "task_id": "string",
  "timestamp": "2025-09-13T10:20:00Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {},
    "timestamp": "2025-09-13T10:20:00Z"
  }
}
```

### Asynchronous Operation Response
```json
{
  "success": true,
  "task_id": "uuid-string",
  "status": "pending",
  "message": "Task queued successfully"
}
```

## HTTP Status Codes

- **200 OK**: Request successful
- **202 Accepted**: Asynchronous task accepted
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid API key
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Endpoint or resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

## Rate Limiting

- Rate limits are enforced per API key
- Limits vary by endpoint and subscription plan
- Rate limit information included in response headers:
  - `X-RateLimit-Limit`: Request limit per time window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when rate limit resets

## Data Formats

### Common Data Types
- **Timestamps**: ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ)
- **Task IDs**: UUID v4 strings
- **Images**: Base64 encoded or multipart file upload
- **Audio**: Base64 encoded or binary data

### File Upload Guidelines
- **Maximum file size**: Varies by endpoint (typically 10MB-100MB)
- **Supported formats**: 
  - Images: JPEG, PNG, WebP
  - Audio: MP3, WAV, OGG
  - Documents: PDF, TXT, DOCX

## Integration Considerations

### Asynchronous Operations
Many endpoints return task IDs for long-running operations. Clients should:
1. Submit request and receive task_id
2. Poll task status using `/task-status/{task_id}`
3. Retrieve results when status is "completed"

### Error Handling
- Implement exponential backoff for retries
- Handle rate limiting with appropriate delays
- Validate file formats and sizes before upload
- Parse error responses for detailed error information

### Security Best Practices
- Store API keys securely using environment variables
- Use HTTPS for all requests
- Implement proper timeout handling
- Log requests for debugging but never log sensitive data