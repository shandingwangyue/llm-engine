"""
路由模块 - 所有API路由的集合
"""

from .health import router as health_router
from .generate import router as generate_router
from .models import router as models_router
from .openai import router as openai_router

__all__ = [
    'health_router',
    'generate_router', 
    'models_router',
    'openai_router'
]