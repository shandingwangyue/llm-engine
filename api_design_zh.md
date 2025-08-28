# API 接口设计规范

## 🎯 基础信息
- **基础URL**: `/api/v1` (自定义接口)
- **OpenAI兼容URL**: `/v1` (完全兼容OpenAI API)
- **认证方式**: API Key (可选) / JWT Token
- **响应格式**: JSON
- **编码**: UTF-8

## 📋 核心API端点

### 1. 健康检查接口
```http
GET /health
```
**响应**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "memory_usage": "2.1GB/8GB",
  "active_connections": 5
}
```

### 2. 文本生成接口
```http
POST /generate
```
**请求体**:
```json
{
  "prompt": "请解释人工智能的概念",
  "model": "llama-2-7b-chat",
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

**响应**:
```json
{
  "text": "人工智能是...",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 128,
    "total_tokens": 143
  },
  "latency": 2.3
}
```

### 3. 流式生成接口
```http
POST /generate/stream
```
**请求头**:
```
Accept: text/event-stream
```

**请求体**:
```json
{
  "prompt": "请解释人工智能的概念",
  "model": "qwen-7b-chat",
  "max_tokens": 512,
  "temperature": 0.7
}
```

**响应** (SSE格式):
```
data: {"token": "人", "finished": false}

data: {"token": "工", "finished": false}

data: {"token": "智", "finished": false}

data: {"token": "能", "finished": true}
```

### 4. 模型管理接口
```http
GET /models
```
**响应**:
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
**请求体**:
```json
{
  "quantization": "q4_0",
  "prefer_gpu": false
}
```

## 🔧 错误处理

### 错误响应格式
```json
{
  "error": {
    "code": "MODEL_NOT_LOADED",
    "message": "请求的模型未加载",
    "details": "请先调用加载接口"
  }
}
```

### 常见错误码
- `400`: 请求参数错误
- `401`: 认证失败
- `404`: 资源未找到
- `429`: 请求过于频繁
- `500`: 服务器内部错误
- `503`: 服务不可用

## 📊 性能监控接口

```http
GET /metrics
```
**响应** (Prometheus格式):
```
# HELP model_inference_seconds 模型推理耗时
# TYPE model_inference_seconds histogram
model_inference_seconds_bucket{le="1"} 15
model_inference_seconds_bucket{le="3"} 42
model_inference_seconds_bucket{le="5"} 78

# HELP active_connections 活跃连接数
# TYPE active_connections gauge
active_connections 23
```

## 🛡️ 限流策略

### 请求头信息
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633046400
```

## 🔄 批量请求支持

```http
POST /batch/generate
```
**请求体**:
```json
{
  "requests": [
    {
      "prompt": "问题1",
      "max_tokens": 100
    },
    {
      "prompt": "问题2", 
      "max_tokens": 150
    }
  ]
}
```

**响应**:
```json
{
  "results": [
    {
      "text": "回答1",
      "usage": {...}
    },
    {
      "text": "回答2",
      "usage": {...}
    }
  ]
}
```

## 📝 使用示例

### Python客户端示例
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

# 使用示例
result = generate_text("请写一首关于春天的诗")
print(result["text"])
```

### JavaScript客户端示例
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

## 🌐 OpenAI兼容接口

### Chat Completions接口
```http
POST /v1/chat/completions
```
**请求体** (非流式):
```json
{
  "model": "qwen-7b-chat",
  "messages": [
    {"role": "system", "content": "你是一个有帮助的助手"},
    {"role": "user", "content": "请解释人工智能的概念"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

**请求体** (流式):
```json
{
  "model": "qwen-7b-chat",
  "messages": [
    {"role": "system", "content": "你是一个有帮助的助手"},
    {"role": "user", "content": "请解释人工智能的概念"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": true  // 启用流式输出
}
```

**流式响应** (SSE格式):
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"人"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"工"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"智"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"能"},"index":0}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{},"finish_reason":"stop","index":0}]}

data: [DONE]
```

**响应体**:
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
        "content": "人工智能是..."
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

### Models列表接口
```http
GET /v1/models
```

### 支持的主流模型
- `qwen-7b-chat` - 阿里通义千问7B聊天模型
- `qwen-14b-chat` - 阿里通义千问14B聊天模型
- `gemma-7b` - Google Gemma 7B模型
- `gemma-2b` - Google Gemma 2B模型
- `llama-2-7b-chat` - Meta LLaMA 2 7B聊天模型
- `chatglm3-6b` - 清华智谱ChatGLM3 6B模型

### 使用官方OpenAI SDK示例
```python
import openai

# 配置指向本地服务
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "any-key"  # 可选的认证

# 完全兼容OpenAI API
response = openai.ChatCompletion.create(
    model="qwen-7b-chat",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "请解释人工智能的概念"}
    ]
)

print(response.choices[0].message.content)
```

### LangChain集成示例
```python
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

# 使用本地模型
llm = OpenAI(
    openai_api_base="http://localhost:8000/v1",
    model_name="qwen-7b-chat"
)

# 或者使用聊天模型
chat = ChatOpenAI(
    openai_api_base="http://localhost:8000/v1",
    model_name="qwen-7b-chat"
)
```