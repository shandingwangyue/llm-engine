"""
大模型服务引擎主应用入口
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.model_manager import init_model_manager
from app.core.async_inference import async_inference_service
from app.routers import health, generate, models, openai, memory

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="LLM Service Engine",
    description="高性能大模型本地服务引擎，支持多种开源大模型和OpenAI兼容API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(generate.router, prefix="/api/v1", tags=["generate"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])
app.include_router(memory.router, prefix="/api/v1", tags=["memory"])
app.include_router(openai.router, prefix="/v1", tags=["openai"])

# 添加启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 大模型服务引擎启动中...")
    logger.info(f"📊 配置信息: host={settings.host}, port={settings.port}")
    logger.info(f"📁 模型目录: {settings.model_dir}")
    
    # 初始化模型管理器
    try:
        init_model_manager()
        logger.info("✅ 模型管理器初始化成功")
        
        # 启动异步推理服务处理任务（在事件循环运行后）
        await async_inference_service.start_processing()
        logger.info("✅ 异步推理服务启动成功")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 大模型服务引擎关闭中...")
    # 清理异步推理服务
    await async_inference_service.shutdown()
    # 其他清理工作会在atexit中自动处理

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用大模型服务引擎",
        "version": "0.1.0",
        "docs": "/docs",
        "openai_api": "/v1"
    }

# 健康检查（兼容性）
@app.get("/health")
async def health_check():
    """健康检查接口（兼容性）"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 直接运行应用
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level
    )