# AIEco API Reference

> OpenAI-compatible API for self-hosted AI inference

---

## Overview

AIEco provides a fully OpenAI-compatible REST API, making it easy to migrate from commercial APIs to self-hosted inference without changing your code.

**Base URL:**
```
http://localhost:8000/v1
```

**Authentication:**
```bash
Authorization: Bearer sk-your-api-key
```

---

## Authentication

### API Keys

AIEco supports two authentication methods:

1. **Bearer Token** (recommended)
```bash
curl https://your-server/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key"
```

2. **X-API-Key Header**
```bash
curl https://your-server/v1/chat/completions \
  -H "X-API-Key: sk-your-api-key"
```

### Creating API Keys

```bash
# Via Backend API
curl -X POST http://localhost:8080/api/v1/auth/api-keys \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "expires_in_days": 90}'
```

**Response:**
```json
{
  "api_key": "sk-aieco-xxxxxxxxxxxxxxxxxxxx",
  "name": "my-app",
  "created_at": "2026-01-01T00:00:00Z",
  "expires_at": "2026-04-01T00:00:00Z"
}
```

---

## Models

### List Models

Returns a list of available models.

```http
GET /v1/models
```

**Example Request:**
```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer $API_KEY"
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "glm-4.7",
      "object": "model",
      "created": 1704067200,
      "owned_by": "aieco",
      "permission": [],
      "root": "glm-4.7",
      "context_window": 1048576,
      "type": "chat"
    },
    {
      "id": "minimax-m2.1",
      "object": "model",
      "created": 1704067200,
      "owned_by": "aieco",
      "context_window": 204800,
      "type": "chat"
    }
  ]
}
```

### Retrieve Model

Get details about a specific model.

```http
GET /v1/models/{model_id}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | string | Yes | The ID of the model (e.g., `glm-4.7`) |

---

## Chat Completions

Create a chat completion, which is a response to a conversation.

```http
POST /v1/chat/completions
```

### Request Body

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | - | Model ID (e.g., `glm-4.7`) |
| `messages` | array | Yes | - | List of messages in the conversation |
| `temperature` | number | No | 0.7 | Sampling temperature (0-2) |
| `top_p` | number | No | 1.0 | Nucleus sampling parameter |
| `max_tokens` | integer | No | 4096 | Maximum tokens to generate |
| `stream` | boolean | No | false | Enable streaming responses |
| `stop` | string/array | No | null | Stop sequences |
| `presence_penalty` | number | No | 0 | Presence penalty (-2 to 2) |
| `frequency_penalty` | number | No | 0 | Frequency penalty (-2 to 2) |
| `tools` | array | No | null | Tool definitions for function calling |
| `tool_choice` | string/object | No | "auto" | Tool selection mode |

### Message Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | Yes | `system`, `user`, `assistant`, or `tool` |
| `content` | string | Yes | The message content |
| `name` | string | No | Name of the author |
| `tool_calls` | array | No | Tool calls made by the assistant |
| `tool_call_id` | string | No | ID of the tool call being responded to |

### Example: Basic Chat

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "glm-4.7",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "glm-4.7",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 8,
    "total_tokens": 33
  }
}
```

### Example: Streaming

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Tell me a joke"}],
    "stream": true
  }'
```

**Response (Server-Sent Events):**
```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"Why"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":" did"},"finish_reason":null}]}

...

data: [DONE]
```

### Example: Long Context (1M tokens)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.7",
    "messages": [
      {"role": "system", "content": "Analyze the following codebase..."},
      {"role": "user", "content": "[... 500,000 tokens of code ...]"}
    ],
    "max_tokens": 8000
  }'
```

### Example: Function Calling

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.7",
    "messages": [
      {"role": "user", "content": "What is the weather in Tokyo?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get the current weather in a location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City name"
              }
            },
            "required": ["location"]
          }
        }
      }
    ],
    "tool_choice": "auto"
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\": \"Tokyo\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

---

## Completions (Legacy)

For text completion (non-chat format).

```http
POST /v1/completions
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model ID |
| `prompt` | string/array | Yes | The prompt to complete |
| `max_tokens` | integer | No | Maximum tokens |
| `temperature` | number | No | Sampling temperature |
| `stream` | boolean | No | Enable streaming |

---

## Embeddings

> Coming soon - not currently supported

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Invalid API key provided",
    "type": "authentication_error",
    "code": "invalid_api_key",
    "param": null
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid parameters |
| `401` | Unauthorized - Invalid API key |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Model or resource not found |
| `429` | Rate Limited - Too many requests |
| `500` | Internal Error - Server error |
| `503` | Service Unavailable - Model loading |

### Rate Limits

| Limit | Default |
|-------|---------|
| Requests per minute | 60 |
| Tokens per minute | 100,000 |

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704067260
```

---

## Rate Limits & Usage

### Checking Usage

```http
GET /api/v1/usage
```

**Response:**
```json
{
  "period": "2026-01",
  "tokens_used": 1250000,
  "requests_made": 500,
  "cost_usd": 0.00
}
```

---

## Differences from OpenAI API

| Feature | OpenAI | AIEco |
|---------|--------|-------|
| Max context | 128K | **2M** |
| Streaming | ✅ | ✅ |
| Function calling | ✅ | ✅ |
| Vision | ✅ | Coming soon |
| Embeddings | ✅ | Coming soon |
| Fine-tuning | ✅ | Not supported |
| Rate limits | Strict | Configurable |
| Cost | $15-60/1M tokens | **Self-hosted** |
| Privacy | Data may be used | **100% private** |

---

## SDK Examples

### Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-local",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### JavaScript/TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-local',
  baseURL: 'http://localhost:8000/v1',
});

const response = await client.chat.completions.create({
  model: 'glm-4.7',
  messages: [{ role: 'user', content: 'Hello!' }],
});

console.log(response.choices[0].message.content);
```

### cURL

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{"model": "glm-4.7", "messages": [{"role": "user", "content": "Hello!"}]}'
```

---

*Last updated: January 2026*
