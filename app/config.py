"""
配置管理模块
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务器配置
    host: str = Field("127.0.0.1", env="HOST")  # Windows上使用127.0.0.1而不是0.0.0.0
    port: int = Field(8080, env="PORT")  # 改为8080端口，避免与常用端口冲突
    workers: int = Field(1, env="WORKERS")  # Windows上建议使用1个worker
    log_level: str = Field("info", env="LOG_LEVEL")
    
    # 模型配置
    model_dir: str = Field("./models", env="MODEL_DIR")
    default_model: str = Field("qwen3-8b-Q5_K_M", env="DEFAULT_MODEL")
    auto_load_models: bool = Field(True, env="AUTO_LOAD_MODELS")
    
    # 性能配置
    max_cache_size: int = Field(1000, env="MAX_CACHE_SIZE")
    cache_ttl: int = Field(300, env="CACHE_TTL")
    max_concurrent_requests: int = Field(20, env="MAX_CONCURRENT_REQUESTS")
    max_tokens: int = Field(2048, env="MAX_TOKENS")
    
    # 内存优化配置
    use_mmap: bool = Field(True, env="USE_MMAP")
    use_mlock: bool = Field(False, env="USE_MLOCK")
    n_threads: int = Field(4, env="N_THREADS")
    n_batch: int = Field(512, env="N_BATCH")
    n_gpu_layers: int = Field(0, env="N_GPU_LAYERS")
    
    # 监控配置
    enable_monitoring: bool = Field(True, env="ENABLE_MONITORING")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    health_check_interval: int = Field(30, env="HEALTH_CHECK_INTERVAL")
    
    # 安全配置
    api_keys: List[str] = Field([], env="API_KEYS")
    enable_auth: bool = Field(False, env="ENABLE_AUTH")
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    # 流式配置
    streaming_enabled: bool = Field(True, env="STREAMING_ENABLED")
    streaming_chunk_size: int = Field(1, env="STREAMING_CHUNK_SIZE")
    streaming_flush_interval: float = Field(0.1, env="STREAMING_FLUSH_INTERVAL")
    
    # 模型特定配置
    qwen_context_length: int = Field(4096, env="QWEN_CONTEXT_LENGTH")
    gemma_context_length: int = Field(8192, env="GEMMA_CONTEXT_LENGTH")
    llama_context_length: int = Field(2048, env="LLAMA_CONTEXT_LENGTH")
    
    # Redis配置
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    redis_enabled: bool = Field(False, env="REDIS_ENABLED")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator("api_keys", pre=True)
    def parse_api_keys(cls, v):
        """解析API密钥列表"""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v or []
    
    @validator("model_dir", pre=True)
    def validate_model_dir(cls, v):
        """验证模型目录"""
        model_dir = os.path.abspath(v)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
        return model_dir


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


# 模型特定配置
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "qwen": {
        "default_params": {
            "n_ctx": settings.qwen_context_length,
            "n_threads": settings.n_threads,
            "n_batch": settings.n_batch,
            "use_mmap": settings.use_mmap,
            "use_mlock": settings.use_mlock,
        },
        "special_tokens": {
            "bos_token": "<|im_start|>",
            "eos_token": "<|im_end|>",
            "pad_token": "<|extra_0|>"
        }
    },
    "gemma": {
        "default_params": {
            "n_ctx": settings.gemma_context_length,
            "n_threads": settings.n_threads,
            "n_batch": settings.n_batch,
            "use_mmap": settings.use_mmap,
            "use_mlock": settings.use_mlock,
        },
        "special_tokens": {
            "bos_token": "<bos>",
            "eos_token": "<eos>",
            "pad_token": "<pad>"
        }
    },
     "gpt": {
        "default_params": {
            "n_ctx": settings.qwen_context_length,
            "n_threads": settings.n_threads,
            "n_batch": settings.n_batch,
            "use_mmap": settings.use_mmap,
            "use_mlock": settings.use_mlock,
        },
        "special_tokens": {
            "bos_token": "<|startoftext|>",
            "eos_token": "<|return|>",
            "pad_token": "<|endoftext|>"
        }
    },
    "llama": {
        "default_params": {
            "n_ctx": settings.llama_context_length,
            "n_threads": settings.n_threads,
            "n_batch": settings.n_batch,
            "use_mmap": settings.use_mmap,
            "use_mlock": settings.use_mlock,
        }
    },
    "chatglm": {
        "default_params": {
            "n_ctx": 2048,
            "n_threads": settings.n_threads,
            "n_batch": settings.n_batch,
            "use_mmap": settings.use_mmap,
            "use_mlock": settings.use_mlock,
        }
    }
}


def get_model_config(model_type: str) -> Dict[str, Any]:
    """
    获取模型特定配置
    
    Args:
        model_type: 模型类型
        
    Returns:
        Dict: 模型配置字典
    """
    return MODEL_CONFIGS.get(model_type, {})


if __name__ == "__main__":
    # 测试配置加载
    print("配置加载成功:")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Model Dir: {settings.model_dir}")
    print(f"Default Model: {settings.default_model}")