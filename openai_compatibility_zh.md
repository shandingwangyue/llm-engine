# OpenAI兼容接口设计

## 🎯 OpenAI API兼容性

### 1. 核心兼容接口

#### Chat Completions接口 (OpenAI标准)
```http
POST /v1/chat/completions
```
**请求体** (OpenAI兼容格式):
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

**响应体** (OpenAI兼容格式):
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

#### Completions接口 (传统格式)
```http
POST /v1/completions
```
**请求体**:
```json
{
  "model": "gemma-7b",
  "prompt": "请解释人工智能的概念",
  "max_tokens": 512,
  "temperature": 0.7
}
```

### 2. 模型发现接口
```http
GET /v1/models
```
**响应体**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "qwen-7b-chat",
      "object": "model",
      "created": 1677616000,
      "owned_by": "local",
      "permission": [...],
      "root": "qwen-7b-chat",
      "parent": null
    },
    {
      "id": "gemma-7b",
      "object": "model", 
      "created": 1677616000,
      "owned_by": "local",
      "permission": [...],
      "root": "gemma-7b",
      "parent": null
    }
  ]
}
```

## 🔧 Qwen模型支持

### 模型配置
```python
# Qwen模型专用配置
QWEN_MODEL_CONFIG = {
    "qwen-7b": {
        "format": "gguf",
        "recommended_quantization": "q4_0",
        "context_length": 4096,
        "special_tokens": {
            "bos_token": "<|im_start|>",
            "eos_token": "<|im_end|>",
            "pad_token": "<|extra_0|>"
        }
    },
    "qwen-14b": {
        "format": "gguf", 
        "recommended_quantization": "q4_0",
        "context_length": 4096
    }
}
```

### Qwen对话格式处理
```python
def format_qwen_chat(messages):
    """将OpenAI格式消息转换为Qwen对话格式"""
    formatted = ""
    for msg in messages:
        if msg["role"] == "system":
            formatted += f"<|im_start|>system\n{msg['content']}<|im_end|>\n"
        elif msg["role"] == "user":
            formatted += f"<|im_start|>user\n{msg['content']}<|im_end|>\n"
        elif msg["role"] == "assistant":
            formatted += f"<|im_start|>assistant\n{msg['content']}<|im_end|>\n"
    
    formatted += "<|im_start|>assistant\n"
    return formatted
```

## 🔧 Gemma模型支持

### 模型配置
```python
# Gemma模型专用配置
GEMMA_MODEL_CONFIG = {
    "gemma-7b": {
        "format": "gguf",
        "recommended_quantization": "q4_0", 
        "context_length": 8192,
        "special_tokens": {
            "bos_token": "<bos>",
            "eos_token": "<eos>",
            "pad_token": "<pad>"
        }
    },
    "gemma-2b": {
        "format": "gguf",
        "recommended_quantization": "q4_0",
        "context_length": 8192
    }
}
```

### Gemma对话格式处理
```python
def format_gemma_chat(messages):
    """将OpenAI格式消息转换为Gemma对话格式"""
    conversation = []
    for msg in messages:
        if msg["role"] == "system":
            conversation.append(f"<start_of_turn>system\n{msg['content']}<end_of_turn>")
        elif msg["role"] == "user":
            conversation.append(f"<start_of_turn>user\n{msg['content']}<end_of_turn>")
        elif msg["role"] == "assistant":
            conversation.append(f"<start_of_turn>model\n{msg['content']}<end_of_turn>")
    
    conversation.append("<start_of_turn>model\n")
    return "\n".join(conversation)
```

## 🏗️ 扩展模型加载器

### 支持更多模型类型
```python
# app/core/model_loader.py - 扩展版本

class ExtendedModelLoader(ModelLoader):
    def __init__(self):
        super().__init__()
        self.supported_formats.extend(['.safetensors', '.pt'])
        
        # 模型特定配置
        self.model_configs = {
            'qwen': QWEN_MODEL_CONFIG,
            'gemma': GEMMA_MODEL_CONFIG,
            'llama': LLAMA_MODEL_CONFIG,
            'chatglm': CHATGLM_MODEL_CONFIG
        }
    
    def detect_model_type(self, model_path: str) -> str:
        """自动检测模型类型"""
        model_name = os.path.basename(model_path).lower()
        
        if 'qwen' in model_name:
            return 'qwen'
        elif 'gemma' in model_name:
            return 'gemma' 
        elif 'chatglm' in model_name:
            return 'chatglm'
        elif 'llama' in model_name:
            return 'llama'
        else:
            return 'unknown'
    
    def load_model_with_config(self, model_path: str, **kwargs):
        """根据模型类型加载并应用特定配置"""
        model_type = self.detect_model_type(model_path)
        
        if model_type in self.model_configs:
            model_config = self.model_configs[model_type]
            # 应用模型特定配置
            kwargs.update(model_config.get('default_params', {}))
        
        return self.load_model(model_path, **kwargs)
```

## 📋 OpenAI兼容路由实现

```python
# app/routers/openai.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time
import shortuuid

router = APIRouter(prefix="/v1", tags=["openai"])

# OpenAI兼容的数据模型
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI兼容的聊天补全接口"""
    try:
        # 转换消息格式
        if request.model.startswith('qwen'):
            prompt = format_qwen_chat(request.messages)
        elif request.model.startswith('gemma'):
            prompt = format_gemma_chat(request.messages)
        else:
            # 默认格式
            prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])
        
        # 执行推理
        result = await inference_service.generate_text(
            request.model, prompt, 
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # 构建OpenAI兼容响应
        response = {
            "id": f"chatcmpl-{shortuuid.uuid()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["text"]
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": result["usage"]
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/completions") 
async def completions(request: CompletionRequest):
    """OpenAI兼容的补全接口"""
    try:
        result = await inference_service.generate_text(
            request.model, request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        response = {
            "id": f"cmpl-{shortuuid.uuid()}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "text": result["text"],
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "length"
                }
            ],
            "usage": result["usage"]
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    """列出所有可用模型"""
    models = model_manager.list_models()
    
    model_list = []
    for model_name, model_info in models.items():
        model_list.append({
            "id": model_name,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "local",
            "permission": [
                {
                    "id": f"modelperm-{shortuuid.uuid()}",
                    "object": "model_permission",
                    "created": int(time.time()),
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": model_name,
            "parent": None
        })
    
    return {"object": "list", "data": model_list}
```

## 🚀 客户端兼容性

### OpenAI SDK直接使用
```python
# 使用官方OpenAI SDK
import openai

# 配置指向本地服务
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "your-api-key"  # 可选的认证

# 直接调用（与OpenAI API完全兼容）
response = openai.ChatCompletion.create(
    model="qwen-7b-chat",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "请解释人工智能的概念"}
    ]
)

print(response.choices[0].message.content)
```

### LangChain集成
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

## 📊 支持的模型列表

| 模型家族 | 支持版本 | 推荐量化 | 特点 |
|----------|----------|----------|------|
| **Qwen** | 7B, 14B | q4_0 | 阿里通义千问，中文优化 |
| **Gemma** | 2B, 7B | q4_0 | Google轻量级模型 |
| **LLaMA** | 7B, 13B | q4_0 | Meta开源模型 |
| **ChatGLM** | 6B | q4_0 | 清华智谱AI |
| **其他** | 自定义 | q4_0 | 支持任意GGUF格式 |

这个扩展设计确保了与OpenAI API的完全兼容性，并增加了对Qwen和Gemma模型的专门支持。