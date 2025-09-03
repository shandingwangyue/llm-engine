"""
模型加载器模块 - 支持多种模型格式的加载
"""

import os
import logging
from typing import Any, Optional, Dict
from app.config import settings, get_model_config
from app.core.utils import detect_model_type, sanitize_model_name

logger = logging.getLogger(__name__)


class ModelLoader:
    """模型加载器，支持多种模型格式"""
    
    def __init__(self):
        self.supported_formats = ['.gguf', '.ggml', '.bin', '.safetensors', '.pt']
        self.loaded_models = {}
        self.gpu = True
    def load_model(self, model_path: str, **kwargs) -> Any:
        """
        加载模型
        
        Args:
            model_path: 模型文件路径
            **kwargs: 模型加载参数
            
        Returns:
            Any: 加载的模型对象
        """
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
            
            # 检测模型类型并应用特定配置
            model_type = detect_model_type(model_path)
            model_config = get_model_config(model_type)
            
            # 合并配置参数
            load_params = model_config.get('default_params', {}).copy()
            load_params.update(kwargs)
            
            # 根据文件扩展名选择加载方式
            ext = os.path.splitext(model_path)[1].lower()
            
            if ext in ['.gguf', '.ggml']:
                return self._load_ggml_model(model_path, **load_params)
            elif ext in ['.bin', '.safetensors', '.pt']:
                return self._load_hf_model(model_path, **load_params)
            else:
                raise ValueError(f"不支持的模型格式: {ext}")
                
        except Exception as e:
            logger.error(f"模型加载失败: {model_path}, 错误: {e}")
            raise
    
    def _load_ggml_model(self, model_path: str, **kwargs) -> Any:
        """
        加载GGUF/GGML格式模型
        
        Args:
            model_path: 模型文件路径
            **kwargs: 模型参数
            
        Returns:
            Any: llama.cpp模型实例
        """
        try:
            import llama_cpp
            
            # 默认参数
            default_params = {
                'model_path': model_path,
                'n_ctx': kwargs.get('n_ctx', 2048),
                'n_threads': kwargs.get('n_threads', settings.n_threads),
                'n_batch': kwargs.get('n_batch', settings.n_batch),
                'use_mmap': kwargs.get('use_mmap', settings.use_mmap),
                'use_mlock': kwargs.get('use_mlock', settings.use_mlock),
                'verbose': False
            }
            
            # 如果有GPU，尝试使用GPU加速
            if kwargs.get('n_gpu_layers', settings.n_gpu_layers) > 0 and self.gpu:
                default_params['n_gpu_layers'] = kwargs.get('n_gpu_layers', settings.n_gpu_layers)
                print(f"使用GPU加速: {  settings.n_gpu_layers} GPU层")
                self.gpu = False
            logger.info(f"加载GGML模型: {model_path}")
            model = llama_cpp.Llama(**default_params)
            logger.info(f"GGML模型加载成功: {model_path}")
            
            return model
            
        except ImportError:
            raise ImportError("请安装 llama-cpp-python: pip install llama-cpp-python")
        except Exception as e:
            logger.error(f"GGML模型加载失败: {e}")
            raise
    
    def _load_hf_model(self, model_path: str, **kwargs) -> Any:
        """
        加载HuggingFace格式模型
        
        Args:
            model_path: 模型文件路径
            **kwargs: 模型参数
            
        Returns:
            Dict: 包含model和tokenizer的字典
        """
        try:
            from transformers import AutoModel, AutoTokenizer, AutoConfig
            import torch
            
            # 检查模型配置
            try:
                config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
                logger.info(f"模型配置: {config.model_type}")
            except:
                logger.warning(f"无法读取模型配置: {model_path}")
                config = None
            
            # 量化配置
            load_in_8bit = kwargs.get('load_in_8bit', False)
            load_in_4bit = kwargs.get('load_in_4bit', False)
            device_map = kwargs.get('device_map', 'auto')
            
            # 设备配置
            if torch.cuda.is_available():
                device = kwargs.get('device', 'cuda')
                torch_dtype = kwargs.get('torch_dtype', torch.float16)
            else:
                device = kwargs.get('device', 'cpu')
                torch_dtype = kwargs.get('torch_dtype', torch.float32)
            
            logger.info(f"加载HF模型: {model_path}")
            
            # 加载tokenizer
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    use_fast=True
                )
            except:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True
                )
            
            # 加载模型
            model = AutoModel.from_pretrained(
                model_path,
                torch_dtype=torch_dtype,
                device_map=device_map,
                load_in_8bit=load_in_8bit,
                load_in_4bit=load_in_4bit,
                trust_remote_code=True
            )
            
            # 确保模型在评估模式
            model.eval()
            
            logger.info(f"HF模型加载成功: {model_path}")
            
            return {
                'model': model,
                'tokenizer': tokenizer,
                'config': config
            }
            
        except ImportError:
            raise ImportError("请安装 transformers: pip install transformers")
        except Exception as e:
            logger.error(f"HF模型加载失败: {e}")
            raise
    
    def load_model_with_config(self, model_path: str, model_name: str, **kwargs) -> Any:
        """
        根据模型配置加载模型
        
        Args:
            model_path: 模型文件路径
            model_name: 模型名称
            **kwargs: 额外参数
            
        Returns:
            Any: 加载的模型对象
        """
        # 清理模型名称
        sanitized_name = sanitize_model_name(model_name)
        
        # 检测模型类型
        model_type = detect_model_type(model_path)
        model_config = get_model_config(model_type)
        
        # 合并配置参数
        load_params = model_config.get('default_params', {}).copy()
        load_params.update(kwargs)
        
        # 加载模型
        model = self.load_model(model_path, **load_params)
        
        # 记录加载的模型
        self.loaded_models[sanitized_name] = {
            'model': model,
            'path': model_path,
            'type': model_type,
            'config': model_config
        }
        
        return model
    
    def get_loaded_model(self, model_name: str) -> Optional[Any]:
        """
        获取已加载的模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Any]: 模型对象或None
        """
        sanitized_name = sanitize_model_name(model_name)
        model_info = self.loaded_models.get(sanitized_name)
        return model_info['model'] if model_info else None
    
    def unload_model(self, model_name: str) -> bool:
        """
        卸载模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否成功卸载
        """
        sanitized_name = sanitize_model_name(model_name)
        if sanitized_name in self.loaded_models:
            # 清理模型资源
            model_info = self.loaded_models[sanitized_name]
            if hasattr(model_info['model'], 'close'):
                model_info['model'].close()
            
            del self.loaded_models[sanitized_name]
            logger.info(f"模型已卸载: {model_name}")
            return True
        
        return False
    
    def list_loaded_models(self) -> Dict[str, Dict]:
        """
        列出所有已加载的模型
        
        Returns:
            Dict: 已加载模型信息
        """
        return self.loaded_models.copy()


# 全局模型加载器实例
model_loader = ModelLoader()