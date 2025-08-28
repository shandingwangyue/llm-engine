#!/usr/bin/env python3
"""
启动脚本 - 运行大模型服务引擎
"""

import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        from app.main import app
        from app.config import settings
        
        logger.info("🚀 启动大模型服务引擎...")
        logger.info(f"📊 服务地址: http://{settings.host}:{settings.port}")
        logger.info(f"📁 模型目录: {settings.model_dir}")
        logger.info(f"🔧 工作进程: {settings.workers}")
        logger.info(f"📝 日志级别: {settings.log_level}")
        
        # 检查模型目录
        if not os.path.exists(settings.model_dir):
            os.makedirs(settings.model_dir, exist_ok=True)
            logger.info(f"✅ 创建模型目录: {settings.model_dir}")
        
        # 列出模型目录内容
        models = os.listdir(settings.model_dir)
        if models:
            logger.info(f"📦 发现的模型: {models}")
        else:
            logger.info("📦 模型目录为空，请将模型文件放入 models/ 目录")
        
        # 导入uvicorn并运行应用
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            workers=settings.workers,
            log_level=settings.log_level,
            reload=False
        )
        
    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()