"""
缓存服务模块 - 请求结果缓存
"""

import time
import logging
from typing import Any, Optional, Dict
from collections import OrderedDict
from app.config import settings

logger = logging.getLogger(__name__)


class ResponseCache:
    """响应缓存服务"""
    
    def __init__(self, max_size: Optional[int] = None, ttl: Optional[int] = None):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存数量
            ttl: 缓存过期时间（秒）
        """
        self.cache = OrderedDict()
        self.max_size = max_size or settings.max_cache_size
        self.ttl = ttl or settings.cache_ttl
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.info(f"初始化缓存: max_size={self.max_size}, ttl={self.ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值或None
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        value, timestamp = self.cache[key]
        
        # 检查是否过期
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            self.misses += 1
            return None
        
        # 更新访问顺序
        self.cache.move_to_end(key)
        self.hits += 1
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），可选
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 检查缓存大小，如果超过则移除最久未使用的
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            cache_ttl = ttl or self.ttl
            self.cache[key] = (value, time.time())
            
            # 确保新添加的项在最后
            self.cache.move_to_end(key)
            
            return True
            
        except Exception as e:
            logger.error(f"缓存设置失败: {key}, 错误: {e}")
            return False
    
    def _evict_oldest(self):
        """移除最久未使用的缓存项"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.evictions += 1
            logger.debug(f"缓存淘汰: {oldest_key}")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        logger.info("缓存已清空")
    
    def cleanup_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            int: 清理的缓存数量
        """
        expired_count = 0
        current_time = time.time()
        
        keys_to_remove = []
        for key, (value, timestamp) in self.cache.items():
            if current_time - timestamp > self.ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            expired_count += 1
        
        if expired_count > 0:
            logger.debug(f"清理了 {expired_count} 个过期缓存")
        
        return expired_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0,
            'evictions': self.evictions,
            'ttl': self.ttl
        }
    
    def __contains__(self, key: str) -> bool:
        """检查键是否在缓存中（包括检查过期）"""
        return self.get(key) is not None
    
    def __len__(self) -> int:
        """获取缓存数量"""
        return len(self.cache)


class RedisCache:
    """Redis缓存服务（可选）"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化Redis缓存
        
        Args:
            redis_url: Redis连接URL
        """
        try:
            import redis
            self.redis = redis.Redis.from_url(redis_url or settings.redis_url)
            self.enabled = True
            logger.info("Redis缓存已启用")
        except ImportError:
            self.enabled = False
            logger.warning("Redis未安装，使用内存缓存")
        except Exception as e:
            self.enabled = False
            logger.error(f"Redis连接失败: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """从Redis获取缓存"""
        if not self.enabled:
            return None
        
        try:
            import pickle
            cached = self.redis.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置Redis缓存"""
        if not self.enabled:
            return False
        
        try:
            import pickle
            cache_ttl = ttl or settings.cache_ttl
            serialized = pickle.dumps(value)
            self.redis.setex(key, cache_ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除Redis缓存"""
        if not self.enabled:
            return False
        
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            return False


# 全局缓存实例
def get_cache() -> ResponseCache:
    """获取缓存实例"""
    if settings.redis_enabled:
        return RedisCache()
    else:
        return ResponseCache()


# 创建全局缓存实例
response_cache = get_cache()


def generate_cache_key(model: str, prompt: str, **kwargs) -> str:
    """
    生成缓存键
    
    Args:
        model: 模型名称
        prompt: 提示词
        **kwargs: 其他参数
        
    Returns:
        str: 缓存键
    """
    import hashlib
    import json
    
    # 创建参数摘要
    params = {
        'model': model,
        'prompt': prompt,
        **kwargs
    }
    
    # 序列化并生成哈希
    param_str = json.dumps(params, sort_keys=True)
    return f"cache:{hashlib.md5(param_str.encode()).hexdigest()}"


def cached_generate(func):
    """
    缓存装饰器，用于生成函数
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 提取关键参数
        model = kwargs.get('model', 'default')
        prompt = kwargs.get('prompt', '')
        
        # 生成缓存键
        cache_key = generate_cache_key(model, prompt, **{
            k: v for k, v in kwargs.items() 
            if k in ['max_tokens', 'temperature']
        })
        
        # 检查缓存
        cached_result = response_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"缓存命中: {cache_key}")
            return cached_result
        
        # 执行函数并缓存结果
        result = await func(*args, **kwargs)
        response_cache.set(cache_key, result)
        
        return result
    
    return wrapper


# 定期清理过期缓存的线程
class CacheCleaner:
    """缓存清理器"""
    
    def __init__(self, cache: ResponseCache, interval: int = 300):
        self.cache = cache
        self.interval = interval
        self.running = False
        self.thread = None
    
    def start(self):
        """启动清理线程"""
        if self.running:
            return
        
        self.running = True
        import threading
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        logger.info(f"缓存清理器已启动，间隔: {self.interval}s")
    
    def stop(self):
        """停止清理线程"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("缓存清理器已停止")
    
    def _cleanup_loop(self):
        """清理循环"""
        import time
        while self.running:
            time.sleep(self.interval)
            try:
                expired_count = self.cache.cleanup_expired()
                if expired_count > 0:
                    logger.info(f"自动清理了 {expired_count} 个过期缓存")
            except Exception as e:
                logger.error(f"缓存清理失败: {e}")


# 启动缓存清理器
cache_cleaner = CacheCleaner(response_cache, interval=300)
cache_cleaner.start()


# 应用退出时停止清理器
import atexit
atexit.register(cache_cleaner.stop)