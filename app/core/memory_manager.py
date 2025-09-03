"""
内存管理模块 - 实现动态内存管理和LRU缓存淘汰策略
"""

import os
import time
import logging
import threading
import psutil
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
from app.config import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """内存管理器，负责动态内存管理和模型缓存优化"""
    
    def __init__(self):
        self.model_memory_usage: Dict[str, int] = {}  # 模型名称 -> 内存使用量(bytes)
        self.model_last_used: Dict[str, float] = {}   # 模型名称 -> 最后使用时间戳
        self.model_access_count: Dict[str, int] = {}  # 模型名称 -> 访问次数
        self.lock = threading.RLock()
        self.max_memory_usage = self._get_available_memory() * 0.8  # 使用80%可用内存
        
        logger.info(f"内存管理器初始化完成，最大内存限制: {self._format_bytes(self.max_memory_usage)}")
    
    def _get_available_memory(self) -> int:
        """获取系统可用内存"""
        try:
            return psutil.virtual_memory().available
        except Exception:
            # 默认8GB如果无法获取系统内存信息
            return 8 * 1024 * 1024 * 1024
    
    def _format_bytes(self, size: int) -> str:
        """格式化字节大小为易读格式"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def register_model_memory(self, model_name: str, memory_usage: int) -> bool:
        """
        注册模型内存使用
        
        Args:
            model_name: 模型名称
            memory_usage: 内存使用量(bytes)
            
        Returns:
            bool: 是否注册成功
        """
        with self.lock:
            if model_name in self.model_memory_usage:
                logger.warning(f"模型内存已注册: {model_name}")
                return False
            
            self.model_memory_usage[model_name] = memory_usage
            self.model_last_used[model_name] = time.time()
            self.model_access_count[model_name] = 0
            
            logger.info(f"注册模型内存: {model_name} - {self._format_bytes(memory_usage)}")
            return True
    
    def update_model_usage(self, model_name: str) -> None:
        """更新模型使用时间和访问计数"""
        with self.lock:
            if model_name in self.model_last_used:
                self.model_last_used[model_name] = time.time()
                self.model_access_count[model_name] += 1
    
    def unregister_model_memory(self, model_name: str) -> bool:
        """取消注册模型内存使用"""
        with self.lock:
            if model_name in self.model_memory_usage:
                memory_usage = self.model_memory_usage.pop(model_name)
                self.model_last_used.pop(model_name, None)
                self.model_access_count.pop(model_name, None)
                
                logger.info(f"取消注册模型内存: {model_name} - 释放 {self._format_bytes(memory_usage)}")
                return True
            return False
    
    def get_total_memory_usage(self) -> int:
        """获取总内存使用量"""
        with self.lock:
            return sum(self.model_memory_usage.values())
    
    def check_memory_pressure(self) -> Tuple[bool, List[str]]:
        """
        检查内存压力，返回是否需要清理和推荐清理的模型列表
        
        Returns:
            Tuple[bool, List[str]]: (需要清理, 推荐清理的模型列表)
        """
        with self.lock:
            total_usage = self.get_total_memory_usage()
            memory_pressure = total_usage > self.max_memory_usage
            
            if not memory_pressure:
                return False, []
            
            # 使用LRU策略选择要清理的模型
            candidates = []
            current_time = time.time()
            
            for model_name, last_used in self.model_last_used.items():
                # 计算分数：访问频率低 + 长时间未使用
                access_count = self.model_access_count.get(model_name, 0)
                idle_time = current_time - last_used
                
                # 分数 = 空闲时间 / (访问次数 + 1) 避免除零
                score = idle_time / (access_count + 1)
                candidates.append((model_name, score))
            
            # 按分数降序排序（分数越高越应该被清理）
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # 选择要清理的模型，直到内存使用降到阈值以下
            models_to_clean = []
            remaining_memory = total_usage
            
            for model_name, _ in candidates:
                memory_usage = self.model_memory_usage[model_name]
                if remaining_memory - memory_usage <= self.max_memory_usage:
                    models_to_clean.append(model_name)
                    remaining_memory -= memory_usage
                    if remaining_memory <= self.max_memory_usage:
                        break
            
            logger.warning(
                f"内存压力警告: 使用 {self._format_bytes(total_usage)} / "
                f"限制 {self._format_bytes(self.max_memory_usage)}. "
                f"推荐清理 {len(models_to_clean)} 个模型"
            )
            
            return True, models_to_clean
    
    def get_memory_stats(self) -> Dict[str, any]:
        """获取内存统计信息"""
        with self.lock:
            total_usage = self.get_total_memory_usage()
            system_memory = psutil.virtual_memory()
            
            return {
                'total_models': len(self.model_memory_usage),
                'total_memory_usage': total_usage,
                'formatted_usage': self._format_bytes(total_usage),
                'memory_limit': self.max_memory_usage,
                'formatted_limit': self._format_bytes(self.max_memory_usage),
                'memory_pressure': total_usage > self.max_memory_usage,
                'system_available': system_memory.available,
                'formatted_system_available': self._format_bytes(system_memory.available),
                'system_total': system_memory.total,
                'formatted_system_total': self._format_bytes(system_memory.total),
                'models': [
                    {
                        'name': name,
                        'memory_usage': usage,
                        'formatted_usage': self._format_bytes(usage),
                        'last_used': self.model_last_used.get(name, 0),
                        'access_count': self.model_access_count.get(name, 0)
                    }
                    for name, usage in self.model_memory_usage.items()
                ]
            }
    
    def cleanup_models(self, model_names: List[str]) -> Dict[str, bool]:
        """
        清理指定模型的内存记录
        
        Args:
            model_names: 要清理的模型名称列表
            
        Returns:
            Dict[str, bool]: 清理结果字典
        """
        results = {}
        with self.lock:
            for model_name in model_names:
                results[model_name] = self.unregister_model_memory(model_name)
        return results


# 全局内存管理器实例
memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    """获取内存管理器实例"""
    return memory_manager


# 定期内存检查线程
class MemoryMonitor:
    """内存监控器，定期检查内存压力"""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
        self.thread = None
    
    def start(self):
        """启动监控线程"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"内存监控器已启动，检查间隔: {self.check_interval}s")
    
    def stop(self):
        """停止监控线程"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("内存监控器已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        import time
        while self.running:
            time.sleep(self.check_interval)
            try:
                needs_cleanup, models_to_clean = memory_manager.check_memory_pressure()
                if needs_cleanup:
                    logger.warning(f"检测到内存压力，建议清理模型: {models_to_clean}")
                    
                    # 这里可以添加自动清理逻辑，但建议由外部控制器处理
                    # 因为清理模型需要调用模型管理器的卸载功能
                    
            except Exception as e:
                logger.error(f"内存监控失败: {e}")


# 启动内存监控器
memory_monitor = MemoryMonitor(check_interval=settings.health_check_interval)
memory_monitor.start()


# 应用退出时停止监控器
import atexit
atexit.register(memory_monitor.stop)