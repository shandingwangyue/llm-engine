"""
模型管理路由
"""

import logging
from fastapi import APIRouter, HTTPException
from app.models import ModelsResponse, LoadModelRequest
from app.core.model_manager import model_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """获取模型列表"""
    try:
        models = model_manager.list_models()
        return ModelsResponse(models=list(models.values()))
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {e}")


@router.get("/models/{model_name}")
async def get_model_info(model_name: str):
    """获取特定模型信息"""
    try:
        model_info = model_manager.get_model_info(model_name)
        if model_info is None:
            raise HTTPException(status_code=404, detail=f"模型不存在: {model_name}")
        
        return model_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {e}")


@router.post("/models/{model_name}/load")
async def load_model(model_name: str, request: LoadModelRequest):
    """加载模型"""
    try:
        success = model_manager.load_model(
            model_name=model_name,
            **request.dict()
        )
        
        if success:
            return {"status": "success", "message": f"模型加载成功: {model_name}"}
        else:
            raise HTTPException(status_code=400, detail=f"模型加载失败: {model_name}")
            
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise HTTPException(status_code=500, detail=f"模型加载失败: {e}")


@router.post("/models/{model_name}/unload")
async def unload_model(model_name: str):
    """卸载模型"""
    try:
        success = model_manager.unload_model(model_name)
        
        if success:
            return {"status": "success", "message": f"模型卸载成功: {model_name}"}
        else:
            raise HTTPException(status_code=400, detail=f"模型卸载失败: {model_name}")
            
    except Exception as e:
        logger.error(f"模型卸载失败: {e}")
        raise HTTPException(status_code=500, detail=f"模型卸载失败: {e}")


@router.post("/models/reload")
async def reload_models():
    """重新加载所有模型"""
    try:
        # 先卸载所有模型
        models = model_manager.list_models()
        for model_name in list(models.keys()):
            model_manager.unload_model(model_name)
        
        # 重新加载模型
        results = model_manager.auto_load_models()
        loaded_count = sum(1 for success in results.values() if success)
        
        return {
            "status": "success",
            "message": f"重新加载完成: {loaded_count}/{len(results)} 个模型",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"重新加载模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载模型失败: {e}")


@router.get("/models/disk")
async def list_disk_models():
    """列出磁盘上的模型文件"""
    try:
        import os
        from app.config import settings
        
        model_files = []
        model_dir = settings.model_dir
        
        if not os.path.exists(model_dir):
            return {"models": [], "count": 0}
        
        # 扫描模型文件
        for filename in os.listdir(model_dir):
            filepath = os.path.join(model_dir, filename)
            
            if os.path.isfile(filepath):
                # 检查文件扩展名
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.gguf', '.ggml', '.bin', '.safetensors', '.pt']:
                    model_files.append({
                        "name": filename,
                        "path": filepath,
                        "size": os.path.getsize(filepath),
                        "type": "file"
                    })
            elif os.path.isdir(filepath):
                # 检查是否是模型目录
                model_files.append({
                    "name": filename,
                    "path": filepath,
                    "size": "directory",
                    "type": "directory"
                })
        
        return {
            "models": model_files,
            "count": len(model_files),
            "directory": model_dir
        }
        
    except Exception as e:
        logger.error(f"列出磁盘模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出磁盘模型失败: {e}")