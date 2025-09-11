"""
生成路由 - 文本生成相关接口
"""

import logging
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import GenerateRequest, GenerateResponse, StreamToken
from app.core import inference_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """文本生成接口"""
    try:
        # 参数验证
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="提示词不能为空")
        
        if request.max_tokens and request.max_tokens > 4096:
            raise HTTPException(status_code=400, detail="max_tokens 不能超过 4096")
        
        if request.temperature and (request.temperature < 0 or request.temperature > 2):
            raise HTTPException(status_code=400, detail="temperature 必须在 0-2 之间")
        
        # 执行生成
        result = await inference_service.generate_text(
            request.model,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"文本生成失败: {e}")


@router.post("/generate/stream")
async def generate_stream(request: GenerateRequest):
    """流式文本生成接口"""
    try:
        # 参数验证
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="提示词不能为空")
        
        if request.max_tokens and request.max_tokens > 4096:
            raise HTTPException(status_code=400, detail="max_tokens 不能超过 4096")
        
        if request.temperature and (request.temperature < 0 or request.temperature > 2):
            raise HTTPException(status_code=400, detail="temperature 必须在 0-2 之间")
        
        async def event_generator():
            """事件生成器"""
            try:
                import platform
                is_linux = platform.system().lower() == 'linux'
                
                async for token_data in inference_service.generate_stream(
                    request.model,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    # 在Linux环境下，立即刷新缓冲区
                    if is_linux:
                        yield f"data: {json.dumps(token_data)}\n\n"
                        # 强制刷新缓冲区
                        import sys
                        if hasattr(sys.stdout, 'flush'):
                            sys.stdout.flush()
                    else:
                        yield f"data: {json.dumps(token_data)}\n\n"
                    
                    # 如果生成完成，退出循环
                    if token_data.get('finished', False):
                        break
                        
            except Exception as e:
                error_data = {"error": str(e), "finished": True}
                yield f"data: {json.dumps(error_data)}\n\n"
        
        # Linux特定的响应头优化
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
        
        # 在Linux环境下添加额外的优化头
        import platform
        if platform.system().lower() == 'linux':
            headers.update({
                "Transfer-Encoding": "chunked",
                "X-Content-Type-Options": "nosniff",
                "X-Accel-Buffering": "no",
                "Proxy-Buffering": "off",
                "Proxy-Cache": "off"
            })
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式生成失败: {e}")


@router.post("/batch/generate")
async def batch_generate(requests: list[GenerateRequest]):
    """批量文本生成接口"""
    try:
        if not requests:
            raise HTTPException(status_code=400, detail="请求列表不能为空")
        
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="批量请求数量不能超过10个")
        
        results = []
        for i, request in enumerate(requests):
            try:
                result = await inference_service.generate_text(
                    request.model,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "error": f"第 {i+1} 个请求失败: {str(e)}",
                    "text": "",
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "latency": 0
                })
        
        return {"results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量生成失败: {e}")


@router.get("/generate/stats")
async def get_generate_stats():
    """获取生成统计信息"""
    try:
        stats = inference_service.get_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {e}")


@router.post("/generate/test")
async def test_generate():
    """测试生成接口"""
    try:
        # 使用默认模型进行测试生成
        from app.config import settings
        
        test_prompt = "请用中文介绍一下你自己"
        result = await inference_service.generate_text(
            settings.default_model,
            prompt=test_prompt,
            max_tokens=100,
            temperature=0.7
        )
        
        return {
            "status": "success",
            "test_result": result,
            "message": "测试生成成功"
        }
        
    except Exception as e:
        logger.error(f"测试生成失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "测试生成失败，请检查模型是否加载"
        }