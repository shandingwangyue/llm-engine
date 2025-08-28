# API Design Specification

## 🎯 Basic Information
- **Base URL**: `/api/v1` (Custom Interface)
- **OpenAI Compatible URL**: `/v1` (Fully Compatible with OpenAI API)
- **Authentication**: API Key (Optional) / JWT Token
- **Response Format**: JSON
- **Encoding**: UTF-8

## 📋 Core API Endpoints

### 1. Health Check Endpoint
```http
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "memory_usage": "2.1GB/8GB",
  "active_connections": 5
}
```

### 2. Text Generation Endpoint
```http
POST /generate
```
**Request Body**:
```json
{
  "prompt": "Please explain the concept of artificial intelligence",
  "model": "llama-2-7b-chat",
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

**Response**:
```json
{
  "text": "Artificial Intelligence is...",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 128,
    "total_tokens": 143
  },
  "latency": 2.3
}
```

### 3. Stream Generation Endpoint
```http
POST /generate/stream
```
**Request Headers**:
```
Accept: text/event-stream
```

**Request Body**:
```json
{
  "prompt": "Please explain the concept of artificial intelligence",
  "model": "qwen-7b-chat",
  "max_tokens": 512,
  "temperature": 0.7
}
```

**Response** (SSE Format):
```
data: {"token": "Arti", "finished": false}

data: {"token": "ficial", "finished": false}

data: {"token": " Intel", "finished": false}

data: {"token": "ligence", "finished": true}
```

### 4. Model Management Endpoint
```http
GET /models
```
**Response**:
```json
{
  "models": [
    {
      "name": "llama-2-7b-chat",
      "format": "gguf",
      "size": "4.2GB",
      "loaded": true,
      "memory_usage": "3.8GB"
    }
  ]
}
```

```http
POST /models/{model_name}/load
```
**Request Body**:
```json
{
  "quantization": "q4_0",
  "prefer_gpu": false
}
```

## 🔧 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "MODEL_NOT_LOADED",
    "message": "Requested model is not loaded",
    "details": "Please call the load endpoint first"
  }
}
```

### Common Error Codes
- `400`: Bad Request
- `401`: Authentication Failed
- `404`: Resource Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error
- `503`: Service Unavailable

## 📊 Performance Monitoring Endpoint

```http
GET /metrics
```
**Response** (Prometheus Format):
```
# HELP model_inference_seconds Model inference time
# TYPE model_inference_seconds histogram
model_inference_seconds_bucket{le="1"} 15
model_inference_seconds_bucket{le="3"} 42
model_inference_seconds_bucket{le="5"} 78

# HELP active_connections Active connections
# TYPE active_connections gauge
active_connections 23
```

## 🛡️ Rate Limiting Strategy

### Response Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633046400
```

## 🔄 Batch Request Support

```http
POST /batch/generate
```
**Request Body**:
```json
{
  "requests": [
    {
      "prompt": "Question 1",
      "max_tokens": 100
    },
    {
      "prompt": "Question 2",
      "max_tokens": 150
    }
  ]
}
```

**Response**:
```json
{
  "results": [
    {
      "text": "Answer 1",
      "usage": {...}
    },
    {
      "text": "Answer 2",
      "usage": {...}
    }
  ]
}
```

## 📝 Usage Examples

### Python Client Example
```python
import requests

def generate_text(prompt, model="default"):
    url = "http://localhost:8000/api/v1/generate"
    payload = {
        "prompt": prompt,
        "model": model,
        "max_tokens": 512,
        "temperature": 0.7
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Usage Example
result = generate_text("Write a poem about spring")
print(result["text"])
```

### JavaScript Client Example
```javascript
async function streamGenerate(prompt) {
    const response = await fetch('/api/v1/generate/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        },
        body: JSON.stringify({ prompt })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const data = JSON.parse(chunk.replace('data: ', ''));
        console.log(data.token);
    }
}
```

## 🌐 OpenAI Compatible Interface

### Chat Completions Endpoint
```http
POST /v1/chat/completions
```
**Request Body** (Non-streaming):
```json
{
  "model": "qwen-7b-chat",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Please explain the concept of artificial intelligence"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

**Request Body** (Streaming):
```json
{
  "model": "qwen-7b-chat",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Please explain the concept of artificial intelligence"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": true  // Enable streaming output
}
```

**Streaming Response** (SSE Format):
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Arti"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"ficial"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":" Intel"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"ligence"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{},"finish_reason":"stop","index":0}]}

data: [DONE]
```

**Response Body**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "qwen-7b-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Artificial Intelligence is..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 128,
    "total_tokens": 143
  }
}
```

### Models List Endpoint
```http
GET /v1/models
```

### Supported Models
- `qwen-7b-chat` - Alibaba Qwen 7B Chat Model
- `qwen-14b-chat` - Alibaba Qwen 14B Chat Model
- `gemma-7b` - Google Gemma 7B Model
- `gemma-2b` - Google Gemma 2B Model
- `llama-2-7b-chat` - Meta LLaMA 2 7B Chat Model
- `chatglm3-6b` - Tsinghua Zhipu ChatGLM3 6B Model

### Official OpenAI SDK Example
```python
import openai

# Configure to point to local service
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "any-key"  # Optional authentication

# Fully compatible with OpenAI API
response = openai.ChatCompletion.create(
    model="qwen-7b-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Please explain the concept of artificial intelligence"}
    ]
)

print(response.choices[0].message.content)
```

### LangChain Integration Example
```python
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

# Use local model
llm = OpenAI(
    openai_api_base="http://localhost:8000/v1",
    model_name="qwen-7b-chat"
)

# Or use chat model
chat = ChatOpenAI(
    openai_api_base="http://localhost:8000/v1",
    model_name="qwen-7b-chat"
)
```
