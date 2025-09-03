"""
模型管理器模块 - 管理多个模型的加载和卸载
"""

import os
import logging
import threading
from typing import Dict, Optional, Any, List
from app.config import settings
from app.core.model_loader import model_loader
from app.core.memory_manager import memory_manager
from app.core.utils import detect_model_type, format_bytes

logger = logging.getLogger(__name__)


class ModelManager:
    """模型管理器，负责多个模型的生命周期管理"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_info: Dict[str, Dict] = {}
        self.lock = threading.RLock()
        self._setup_model_dir()
    
    def _setup_model_dir(self):
        """设置模型目录"""
        if not os.path.exists(settings.model_dir):
            os.makedirs(settings.model_dir, exist_ok=True)
            logger.info(f"创建模型目录: {settings.model_dir}")
    
    def load_model(self, model_name: str, model_path: Optional[str] = None, **kwargs) -> bool:
        """
        加载模型
        
        Args:
            model_name: 模型名称
            model_path: 模型文件路径（可选，自动发现）
            **kwargs: 模型加载参数
            
        Returns:
            bool: 是否加载成功
        """
        with self.lock:
            if model_name in self.models:
                logger.warning(f"模型已加载: {model_name}")
                return True
            
            # 自动发现模型文件
            if model_path is None:
                model_path = self._discover_model_file(model_name)
                if model_path is None:
                    logger.error(f"未找到模型文件: {model_name}")
                    return False
            
            try:
                # 加载模型
                model = model_loader.load_model_with_config(model_path, model_name, **kwargs)
                
                # 记录模型信息
                self.models[model_name] = model
                model_type = detect_model_type(model_path)
                self.model_info[model_name] = {
                    'path': model_path,
                    'type': model_type,
                    'loaded': True,
                    'load_params': kwargs
                }
                
                # 注册模型内存使用
                memory_usage = self._get_model_memory_usage_bytes(model, model_type)
                if memory_usage > 0:
                    memory_manager.register_model_memory(model_name, memory_usage)
                    logger.info(f"模型加载成功: {model_name} - 内存使用: {self._format_bytes(memory_usage)}")
                else:
                    logger.info(f"模型加载成功: {model_name} - 内存使用: 未知")
                
                return True
                
            except Exception as e:
                logger.error(f"模型加载失败: {model_name}, 错误: {e}")
                return False
    
    def _discover_model_file(self, model_name: str) -> Optional[str]:
        """
        自动发现模型文件
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[str]: 模型文件路径或None
        """
        # 可能的文件扩展名
        extensions = ['.gguf', '.ggml', '.bin', '.safetensors']
        
        # 检查模型目录
        for ext in extensions:
            model_path = os.path.join(settings.model_dir, f"{model_name}{ext}")
            if os.path.exists(model_path):
                return model_path
        
        # 检查是否有对应的目录（HuggingFace格式）
        model_dir = os.path.join(settings.model_dir, model_name)
        if os.path.isdir(model_dir):
            # 检查目录中是否有模型文件
            for ext in extensions:
                model_file = os.path.join(model_dir, f"pytorch_model{ext}")
                if os.path.exists(model_file):
                    return model_file
            
            # 检查是否有bin文件
            bin_file = os.path.join(model_dir, "pytorch_model.bin")
            if os.path.exists(bin_file):
                return bin_file
        
        return None
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """
        获取已加载的模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Any]: 模型对象或None
        """
        with self.lock:
            return self.models.get(model_name)
    
    def unload_model(self, model_name: str) -> bool:
        """
        卸载模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否成功卸载
        """
        with self.lock:
            if model_name in self.models:
                try:
                    # 从模型加载器卸载
                    success = model_loader.unload_model(model_name)
                    
                    # 清理内存记录
                    memory_manager.unregister_model_memory(model_name)
                    
                    # 清理本地记录
                    del self.models[model_name]
                    del self.model_info[model_name]
                    
                    logger.info(f"模型卸载成功: {model_name}")
                    return success
                    
                except Exception as e:
                    logger.error(f"模型卸载失败: {model_name}, 错误: {e}")
                    return False
            return False
    
    def list_models(self) -> Dict[str, Dict]:
        """
        列出所有模型信息
        
        Returns:
            Dict: 模型信息字典
        """
        with self.lock:
            result = {}
            for name, info in self.model_info.items():
                model = self.models.get(name)
                result[name] = {
                    'name': name,
                    'path': info['path'],
                    'type': info['type'],
                    'loaded': info['loaded'],
                    'memory_usage': self._get_model_memory_usage(model, info['type']),
                    'size': self._get_model_size(info['path'])
                }
            return result
    
    def _get_model_memory_usage_bytes(self, model, model_type: str) -> int:
        """
        获取模型内存使用量（字节）

        Args:
            model: 模型对象
            model_type: 模型类型

        Returns:
            int: 内存使用量(bytes)
        """
        if model is None:
            return 0

        try:
            if model_type in ['gguf', 'ggml']:
                # llama.cpp模型
                if hasattr(model, 'model_size'):
                    return model.model_size
                else:
                    # 估算：文件大小 * 1.2（考虑运行时开销）
                    return 0
            else:
                # HuggingFace模型
                import torch
                if hasattr(model, 'get_memory_footprint'):
                    return model.get_memory_footprint()
                else:
                    # 估算内存使用
                    if isinstance(model, dict) and 'model' in model:
                        model_obj = model['model']
                        param_count = sum(p.numel() for p in model_obj.parameters())
                        memory_estimate = param_count * 4  # 假设float32
                        return memory_estimate
                    return 0
        except:
            return 0

    def _get_model_memory_usage(self, model, model_type: str) -> str:
        """
        获取模型内存使用情况

        Args:
            model: 模型对象
            model_type: 模型类型

        Returns:
            str: 内存使用情况描述
        """
        bytes_usage = self._get_model_memory_usage_bytes(model, model_type)
        return format_bytes(bytes_usage) if bytes_usage > 0 else "未知"
    
    def _get_model_size(self, model_path: str) -> str:
        """
        获取模型文件大小
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            str: 文件大小描述
        """
        try:
            if os.path.isfile(model_path):
                size = os.path.getsize(model_path)
                return format_bytes(size)
            elif os.path.isdir(model_path):
                total_size = 0
                for dirpath, _, filenames in os.walk(model_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                return format_bytes(total_size)
            else:
                return "未知"
        except:
            return "未知"
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """
        获取特定模型的详细信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Dict]: 模型信息或None
        """
        with self.lock:
            if model_name in self.model_info:
                info = self.model_info[model_name].copy()
                model = self.models.get(model_name)
                
                info.update({
                    'memory_usage': self._get_model_memory_usage(model, info['type']),
                    'size': self._get_model_size(info['path']),
                    'active': model is not None
                })
                
                return info
            return None
    
    def auto_load_models(self) -> Dict[str, bool]:
        """
        自动加载模型目录中的所有模型
        
        Returns:
            Dict: 加载结果字典
        """
        results = {}
        
        # 检查模型文件
        for filename in os.listdir(settings.model_dir):
            filepath = os.path.join(settings.model_dir, filename)
            
            if os.path.isfile(filepath):
                # 单个模型文件
                model_name = os.path.splitext(filename)[0]
                if self._is_model_file(filename):
                    results[model_name] = self.load_model(model_name, filepath)
            
            elif os.path.isdir(filepath):
                # 模型目录（HuggingFace格式）
                model_name = filename
                results[model_name] = self.load_model(model_name, filepath)
        
        return results
    
    def _is_model_file(self, filename: str) -> bool:
        """
        检查文件是否为模型文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否为模型文件
        """
        extensions = ['.gguf', '.ggml', '.bin', '.safetensors', '.pt']
        return any(filename.endswith(ext) for ext in extensions)
    
    def cleanup(self):
        """清理所有模型资源"""
        with self.lock:
            for model_name in list(self.models.keys()):
                self.unload_model(model_name)
            logger.info("所有模型资源已清理")
    
    def handle_memory_pressure(self) -> List[str]:
        """
        处理内存压力，卸载不常用的模型
        
        Returns:
            List[str]: 被卸载的模型名称列表
        """
        with self.lock:
            needs_cleanup, models_to_clean = memory_manager.check_memory_pressure()
            if not needs_cleanup:
                return []
            
            unloaded_models = []
            for model_name in models_to_clean:
                if model_name in self.models:
                    if self.unload_model(model_name):
                        unloaded_models.append(model_name)
                        logger.info(f"因内存压力卸载模型: {model_name}")
            
            return unloaded_models
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """
        获取已加载的模型，并更新使用统计
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Any]: 模型对象或None
        """
        with self.lock:
            model = self.models.get(model_name)
            if model:
                memory_manager.update_model_usage(model_name)
            return model

    def _format_bytes(self, size: int) -> str:
        """
        格式化字节大小为易读格式
        
        Args:
            size: 字节大小
            
        Returns:
            str: 格式化后的字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


# 全局模型管理器实例
model_manager = ModelManager()


def init_model_manager():
    """初始化模型管理器"""
    if settings.auto_load_models:
        logger.info("开始自动加载模型...")
        results = model_manager.auto_load_models()
        loaded_count = sum(1 for success in results.values() if success)
        logger.info(f"自动加载完成: 成功 {loaded_count}/{len(results)} 个模型")
    
    # 确保默认模型已加载
    if settings.default_model and settings.default_model not in model_manager.models:
        logger.info(f"加载默认模型: {settings.default_model}")
        model_manager.load_model(settings.default_model)


# 应用退出时清理资源
import atexit
atexit.register(model_manager.cleanup)