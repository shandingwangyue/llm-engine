"""
推理服务模块 - 处理模型推理请求
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from app.core.model_manager import model_manager
from app.core.cache import response_cache, cached_generate

logger = logging.getLogger(__name__)


class InferenceService:
    """推理服务"""
    
    def __init__(self):
        self.active_requests = 0
        self.total_requests = 0
        self.request_queue = asyncio.Queue()
    
    @cached_generate
    async def generate_text(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成文本
        
        Args:
            model_name: 模型名称
            prompt: 输入提示词
            **kwargs: 生成参数
            
        Returns:
            Dict: 生成结果
        """
        self.active_requests += 1
        self.total_requests += 1
        
        try:
            start_time = time.time()
            
            # 获取模型
            model = model_manager.get_model(model_name)
            if model is None:
                raise ValueError(f"模型未加载: {model_name}")
            
            # 执行推理
            result = await self._inference(model, prompt, **kwargs)
            
            latency = time.time() - start_time
            
            response = {
                "text": result,
                "usage": {
                    "prompt_tokens": self._estimate_tokens(prompt),
                    "completion_tokens": self._estimate_tokens(result),
                    "total_tokens": self._estimate_tokens(prompt) + self._estimate_tokens(result)
                },
                "latency": latency
            }
            
            logger.info(f"推理完成: model={model_name}, latency={latency:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"推理失败: {e}")
            raise
        finally:
            self.active_requests -= 1
    
    async def generate_stream(self, model_name: str, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成文本
        
        Args:
            model_name: 模型名称
            prompt: 输入提示词
            **kwargs: 生成参数
            
        Returns:
            AsyncGenerator: 流式生成器
        """
        self.active_requests += 1
        self.total_requests += 1
        
        try:
            # 获取模型
            model = model_manager.get_model(model_name)
            if model is None:
                yield {"error": f"模型未加载: {model_name}", "finished": True}
                return
            
            # 执行流式推理
            if hasattr(model, 'create_completion'):
                # GGML模型流式生成
                # 注意：llama-cpp-python的create_completion是同步的，需要包装为异步
                completion_generator = model.create_completion(prompt, stream=True, **kwargs)
                for token in completion_generator:
                    yield {
                        "token": token['choices'][0]['text'],
                        "finished": False
                    }
            else:
                # 非流式模型的简化实现
                result = await self.generate_text(model_name, prompt, **kwargs)
                for char in result['text']:
                    yield {"token": char, "finished": False}
            
            # 结束标志
            yield {"token": "", "finished": True}
            
        except Exception as e:
            logger.error(f"流式推理失败: {e}")
            yield {"error": str(e), "finished": True}
        finally:
            self.active_requests -= 1
    
    async def _inference(self, model, prompt: str, **kwargs) -> str:
        """
        执行模型推理
        
        Args:
            model: 模型对象
            prompt: 输入提示词
            **kwargs: 生成参数
            
        Returns:
            str: 生成结果
        """
        try:
            if hasattr(model, 'create_completion'):
                # GGML模型推理
                result = model.create_completion(prompt, **kwargs)
                return result['choices'][0]['text']
            else:
                # HuggingFace模型推理
                import torch
                from transformers import GenerationConfig
                
                model_obj = model['model']
                tokenizer = model['tokenizer']
                
                # 编码输入
                inputs = tokenizer(prompt, return_tensors="pt")
                
                # 设置生成参数
                generation_config = GenerationConfig(
                    max_new_tokens=kwargs.get('max_tokens', 512),
                    temperature=kwargs.get('temperature', 0.7),
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                # 执行生成
                with torch.no_grad():
                    outputs = model_obj.generate(
                        **inputs,
                        generation_config=generation_config
                    )
                
                # 解码结果
                result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                # 移除输入部分
                if result.startswith(prompt):
                    result = result[len(prompt):].strip()
                
                return result
                
        except Exception as e:
            logger.error(f"模型推理失败: {e}")
            raise
    
    def _estimate_tokens(self, text: str) -> int:
        """
        估算token数量
        
        Args:
            text: 文本内容
            
        Returns:
            int: 估算的token数量
        """
        # 简单估算：英文约4字符一个token，中文约2字符一个token
        import re
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        
        token_count = (chinese_chars / 2) + (other_chars / 4)
        return max(1, int(token_count))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "active_requests": self.active_requests,
            "total_requests": self.total_requests,
            "cache_stats": response_cache.get_stats()
        }


# 全局推理服务实例
inference_service = InferenceService()