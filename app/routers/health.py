"""
健康检查路由
"""

import logging
import psutil
from fastapi import APIRouter
from app.models import HealthResponse
from app.core.model_manager import model_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        # 获取内存使用情况
        process = psutil.Process()
        memory_info = process.memory_info()
        total_memory = psutil.virtual_memory().total
        
        memory_usage = f"{memory_info.rss / 1024 / 1024:.1f}MB/{total_memory / 1024 / 1024:.1f}MB"
        
        # 检查模型加载状态
        models = model_manager.list_models()
        model_loaded = any(info['loaded'] for info in models.values())
        
        # 获取活跃连接数（简化实现）
        active_connections = 0
        
        return HealthResponse(
            status="healthy",
            model_loaded=model_loaded,
            memory_usage=memory_usage,
            active_connections=active_connections,
            version="0.1.0"
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            memory_usage="未知",
            active_connections=0,
            version="0.1.0"
        )


@router.get("/health/models")
async def health_models():
    """模型健康检查"""
    try:
        models = model_manager.list_models()
        return {
            "status": "healthy",
            "models": models,
            "total_models": len(models),
            "loaded_models": sum(1 for info in models.values() if info['loaded'])
        }
    except Exception as e:
        logger.error(f"模型健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/health/system")
async def health_system():
    """系统健康检查"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_info = {
            "total": f"{memory.total / 1024 / 1024:.1f}MB",
            "available": f"{memory.available / 1024 / 1024:.1f}MB",
            "used": f"{memory.used / 1024 / 1024:.1f}MB",
            "percent": f"{memory.percent}%"
        }
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": f"{disk.total / 1024 / 1024 / 1024:.1f}GB",
            "used": f"{disk.used / 1024 / 1024 / 1024:.1f}GB",
            "free": f"{disk.free / 1024 / 1024 / 1024:.1f}GB",
            "percent": f"{disk.percent}%"
        }
        
        return {
            "status": "healthy",
            "cpu": f"{cpu_percent}%",
            "memory": memory_info,
            "disk": disk_info
        }
        
    except Exception as e:
        logger.error(f"系统健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }