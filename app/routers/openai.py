"""
OpenAI兼容路由 - 提供与OpenAI API完全兼容的接口
"""

import logging
import time
import json
import shortuuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionUsage,
    CompletionRequest, CompletionResponse, ChatMessage
)
from app.core import format_qwen_chat, format_gemma_chat, format_gpt_chat, format_gpt_oss_chat
from app.core.async_inference import async_inference_service
from app.core.model_manager import model_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["openai"])


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI兼容的聊天补全接口"""
    try:
        # 参数验证
        if not request.messages:
            raise HTTPException(status_code=400, detail="messages不能为空")
        
        if request.max_tokens and request.max_tokens > 4096:
            raise HTTPException(status_code=400, detail="max_tokens不能超过4096")
        
        if request.temperature and (request.temperature < 0 or request.temperature > 2):
            raise HTTPException(status_code=400, detail="temperature必须在0-2之间")
        
        # 检查模型是否加载
        if not model_manager.get_model(request.model):
            raise HTTPException(status_code=404, detail=f"模型未加载: {request.model}")
        
        # 流式处理
        if request.stream:
            return await _handle_stream_chat(request)
        
        # 非流式处理
        return await _handle_non_stream_chat(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天补全失败: {e}")
        raise HTTPException(status_code=500, detail=f"聊天补全失败: {e}")


async def _handle_non_stream_chat(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """处理非流式聊天请求"""
    # 转换消息格式
    prompt = _format_chat_messages(request.model, request.messages)
    
    # 执行生成
    result = await async_inference_service.generate_text(
        request.model,
        prompt=prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )
    
    # 构建OpenAI兼容响应
    return ChatCompletionResponse(
        id=f"chatcmpl-{shortuuid.uuid()}",
        object="chat.completion",
        created=int(time.time()),
        model=request.model,
        choices=[{
            "index": 0,
            "message": ChatMessage(role="assistant", content=result["text"]),
            "finish_reason": "stop"
        }],
        usage=ChatCompletionUsage(
            prompt_tokens=result["usage"]["prompt_tokens"],
            completion_tokens=result["usage"]["completion_tokens"],
            total_tokens=result["usage"]["total_tokens"]
        )
    )


async def _handle_stream_chat(request: ChatCompletionRequest) -> StreamingResponse:
    """处理流式聊天请求"""
    # 转换消息格式
    prompt = _format_chat_messages(request.model, request.messages)
    
    async def openai_stream_generator():
        """OpenAI流式响应生成器"""
        try:
            # 执行流式生成
            async for token_data in async_inference_service.generate_stream(
                request.model,
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            ):
                if "error" in token_data:
                    # 错误处理
                    yield f"data: {json.dumps({'error': token_data['error']})}\n\n"
                    break
                
                if not token_data.get('finished', False):
                    # 正常token
                    yield f"data: {json.dumps({
                        'id': f"chatcmpl-{shortuuid.uuid()}",
                        'object': 'chat.completion.chunk',
                        'created': int(time.time()),
                        'model': request.model,
                        'choices': [{
                            'index': 0,
                            'delta': {'content': token_data['token']},
                            'finish_reason': None
                        }]
                    })}\n\n"
                else:
                    # 结束标志
                    yield f"data: {json.dumps({
                        'id': f"chatcmpl-{shortuuid.uuid()}",
                        'object': 'chat.completion.chunk',
                        'created': int(time.time()),
                        'model': request.model,
                        'choices': [{
                            'index': 0,
                            'delta': {},
                            'finish_reason': 'stop'
                        }]
                    })}\n\n"
                    yield "data: [DONE]\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        openai_stream_generator(),
        media_type="text/event-stream"
    )


@router.post("/completions", response_model=CompletionResponse)
async def completions(request: CompletionRequest):
    """OpenAI兼容的补全接口"""
    try:
        # 参数验证
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="prompt不能为空")
        
        if request.max_tokens and request.max_tokens > 4096:
            raise HTTPException(status_code=400, detail="max_tokens不能超过4096")
        
        if request.temperature and (request.temperature < 0 or request.temperature > 2):
            raise HTTPException(status_code=400, detail="temperature必须在0-2之间")
        
        # 检查模型是否加载
        if not model_manager.get_model(request.model):
            raise HTTPException(status_code=404, detail=f"模型未加载: {request.model}")
        
        # 执行生成
        result = await async_inference_service.generate_text(
            request.model,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # 构建OpenAI兼容响应
        return CompletionResponse(
            id=f"cmpl-{shortuuid.uuid()}",
            object="text_completion",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "text": result["text"],
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }],
            usage=ChatCompletionUsage(
                prompt_tokens=result["usage"]["prompt_tokens"],
                completion_tokens=result["usage"]["completion_tokens"],
                total_tokens=result["usage"]["total_tokens"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"补全失败: {e}")
        raise HTTPException(status_code=500, detail=f"补全失败: {e}")


@router.get("/models")
async def list_models():
    """列出可用模型（OpenAI兼容）"""
    try:
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
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {e}")


def _format_chat_messages(model_name: str, messages: list[ChatMessage]) -> str:
    """
    将OpenAI格式消息转换为模型特定的提示格式
    
    Args:
        model_name: 模型名称
        messages: 消息列表
        
    Returns:
        str: 格式化后的提示词
    """
    # 转换为字典格式
    messages_dict = [msg.dict() for msg in messages]
    
    # 根据模型类型选择格式化方式
    if "gpt-oss" in model_name.lower():
        return format_gpt_oss_chat(messages_dict)
    elif "qwen" in model_name.lower():
        return format_qwen_chat(messages_dict)
    elif "gemma" in model_name.lower():
        return format_gemma_chat(messages_dict)
    elif "gpt" in model_name.lower():
        return format_gpt_chat(messages_dict)
    else:
        # 默认格式：简单拼接
        formatted = ""
        for msg in messages_dict:
            role = msg.get('role', '')
            content = msg.get('content', '')
            formatted += f"{role}: {content}\n"
        formatted += "assistant: "
        return formatted


@router.get("/")
async def openai_root():
    """OpenAI API根路径"""
    return {
        "object": "list",
        "data": [
            {
                "id": "chat.completions",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local"
            },
            {
                "id": "completions", 
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local"
            }
        ]
    }