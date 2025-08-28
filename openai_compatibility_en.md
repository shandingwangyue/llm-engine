# OpenAI Compatible Interface Design

## 🎯 OpenAI API Compatibility

### 1. Core Compatible Interfaces

#### Chat Completions Interface (OpenAI Standard)
```http
POST /v1/chat/completions
```
**Request Body** (OpenAI Compatible Format):
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

**Response Body** (OpenAI Compatible Format):
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

#### Completions Interface (Traditional Format)
```http
POST /v1/completions
```
**Request Body**:
```json
{
  "model": "gemma-7b",
  "prompt": "Please explain the concept of artificial intelligence",
  "max_tokens": 512,
  "temperature": 0.7
}
```

### 2. Model Discovery Interface
```http
GET /v1/models
```
**Response Body**:
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

## 🔧 Qwen Model Support

### Model Configuration
```python
# Qwen model specific configuration
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

### Qwen Chat Format Processing
```python
def format_qwen_chat(messages):
    """Convert OpenAI format messages to Qwen chat format"""
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

## 🔧 Gemma Model Support

### Model Configuration
```python
# Gemma model specific configuration
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

### Gemma Chat Format Processing
```python
def format_gemma_chat(messages):
    """Convert OpenAI format messages to Gemma chat format"""
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

## 🏗️ Extended Model Loader

### Support for More Model Types
```python
# app/core/model_loader.py - Extended version

class ExtendedModelLoader(ModelLoader):
    def __init__(self):
        super().__init__()
        self.supported_formats.extend(['.safetensors', '.pt'])
        
        # Model specific configurations
        self.model_configs = {
            'qwen': QWEN_MODEL_CONFIG,
            'gemma': GEMMA_MODEL_CONFIG,
            'llama': LLAMA_MODEL_CONFIG,
            'chatglm': CHATGLM_MODEL_CONFIG
        }
    
    def detect_model_type(self, model_path: str) -> str:
        """Automatically detect model type"""
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
        """Load and apply specific configuration based on model type"""
        model_type = self.detect_model_type(model_path)
        
        if model_type in self.model_configs:
            model_config = self.model_configs[model_type]
            # Apply model specific configuration
            kwargs.update(model_config.get('default_params', {}))
        
        return self.load_model(model_path, **kwargs)
```

## 📋 OpenAI Compatible Router Implementation

```python
# app/routers/openai.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time
import shortuuid

router = APIRouter(prefix="/v1", tags=["openai"])

# OpenAI compatible data models
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
    """OpenAI compatible chat completions endpoint"""
    try:
        # Convert message format
        if request.model.startswith('qwen'):
            prompt = format_qwen_chat(request.messages)
        elif request.model.startswith('gemma'):
            prompt = format_gemma_chat(request.messages)
        else:
            # Default format
            prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])
        
        # Execute inference
        result = await inference_service.generate_text(
            request.model, prompt, 
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Build OpenAI compatible response
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
    """OpenAI compatible completions endpoint"""
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
    """List all available models"""
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

## 🚀 Client Compatibility

### Direct Use of OpenAI SDK
```python
# Using official OpenAI SDK
import openai

# Configure to point to local service
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "your-api-key"  # Optional authentication

# Direct call (fully compatible with OpenAI API)
response = openai.ChatCompletion.create(
    model="qwen-7b-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Please explain the concept of artificial intelligence"}
    ]
)

print(response.choices[0].message.content)
```

### LangChain Integration
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

## 📊 Supported Models List

| Model Family | Supported Versions | Recommended Quantization | Features |
|-------------|-------------------|-------------------------|-----------|
| **Qwen** | 7B, 14B | q4_0 | Alibaba Qwen, Chinese optimized |
| **Gemma** | 2B, 7B | q4_0 | Google lightweight model |
| **LLaMA** | 7B, 13B | q4_0 | Meta open-source model |
| **ChatGLM** | 6B | q4_0 | Tsinghua Zhipu AI |
| **Others** | Custom | q4_0 | Supports any GGUF format |

This extended design ensures full compatibility with the OpenAI API and adds specialized support for Qwen and Gemma models.
