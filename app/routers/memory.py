"""
内存管理路由 - 提供内存状态查看和管理功能
"""

import logging
from fastapi import APIRouter, HTTPException
from app.core.memory_manager import memory_manager
from app.core.model_manager import model_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["memory"])


@router.get("/memory/stats")
async def get_memory_stats():
    """获取内存统计信息"""
    try:
        stats = memory_manager.get_memory_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取内存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内存统计失败: {e}")


@router.get("/memory/pressure")
async def check_memory_pressure():
    """检查内存压力状态"""
    try:
        needs_cleanup, models_to_clean = memory_manager.check_memory_pressure()
        return {
            "status": "success",
            "data": {
                "memory_pressure": needs_cleanup,
                "recommended_cleanup": models_to_clean,
                "message": "内存压力检测完成" if not needs_cleanup else "检测到内存压力，建议清理模型"
            }
        }
    except Exception as e:
        logger.error(f"检查内存压力失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查内存压力失败: {e}")


@router.post("/memory/cleanup")
async def cleanup_memory():
    """清理内存，卸载不常用模型"""
    try:
        unloaded_models = model_manager.handle_memory_pressure()
        
        if unloaded_models:
            return {
                "status": "success",
                "data": {
                    "unloaded_models": unloaded_models,
                    "message": f"已卸载 {len(unloaded_models)} 个模型以释放内存"
                }
            }
        else:
            return {
                "status": "success",
                "data": {
                    "unloaded_models": [],
                    "message": "无需清理，内存使用正常"
                }
            }
            
    except Exception as e:
        logger.error(f"内存清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"内存清理失败: {e}")


@router.get("/memory/models")
async def list_model_memory_usage():
    """列出所有模型的内存使用情况"""
    try:
        models_info = model_manager.list_models()
        memory_stats = memory_manager.get_memory_stats()
        
        # 合并模型信息和内存使用数据
        result = []
        for model_name, info in models_info.items():
            model_memory = None
            for mem_info in memory_stats.get('models', []):
                if mem_info['name'] == model_name:
                    model_memory = mem_info
                    break
            
            result.append({
                "name": model_name,
                "type": info['type'],
                "loaded": info['loaded'],
                "file_size": info['size'],
                "memory_usage": info['memory_usage'],
                "last_used": model_memory['last_used'] if model_memory else 0,
                "access_count": model_memory['access_count'] if model_memory else 0
            })
        
        return {
            "status": "success",
            "data": {
                "models": result,
                "total_count": len(result),
                "loaded_count": sum(1 for m in result if m['loaded'])
            }
        }
        
    except Exception as e:
        logger.error(f"获取模型内存使用列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型内存使用列表失败: {e}")


@router.post("/memory/limit")
async def set_memory_limit(limit_gb: float = None):
    """
    设置内存使用限制
    
    Args:
        limit_gb: 内存限制(GB)，如果为None则使用系统推荐值
    """
    try:
        if limit_gb is not None:
            if limit_gb <= 0:
                raise HTTPException(status_code=400, detail="内存限制必须大于0")
            
            # 转换为字节
            new_limit = int(limit_gb * 1024 * 1024 * 1024)
            memory_manager.max_memory_usage = new_limit
            
            logger.info(f"设置内存限制: {limit_gb} GB ({memory_manager._format_bytes(new_limit)})")
        
        return {
            "status": "success",
            "data": {
                "memory_limit": memory_manager.max_memory_usage,
                "formatted_limit": memory_manager._format_bytes(memory_manager.max_memory_usage),
                "current_usage": memory_manager.get_total_memory_usage(),
                "formatted_usage": memory_manager._format_bytes(memory_manager.get_total_memory_usage()),
                "message": "内存限制设置成功" if limit_gb is not None else "当前内存限制信息"
            }
        }
        
    except Exception as e:
        logger.error(f"设置内存限制失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置内存限制失败: {e}")


@router.get("/memory/system")
async def get_system_memory():
    """获取系统内存信息"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "status": "success",
            "data": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_free": swap.free,
                "swap_percent": swap.percent,
                "formatted": {
                    "total": memory_manager._format_bytes(memory.total),
                    "available": memory_manager._format_bytes(memory.available),
                    "used": memory_manager._format_bytes(memory.used),
                    "swap_total": memory_manager._format_bytes(swap.total),
                    "swap_used": memory_manager._format_bytes(swap.used),
                    "swap_free": memory_manager._format_bytes(swap.free)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取系统内存信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统内存信息失败: {e}")