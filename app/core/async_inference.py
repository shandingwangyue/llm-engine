"""
异步推理服务模块 - 实现真正的异步模型推理
"""

import asyncio
import time
import logging
import concurrent.futures
from typing import Dict, Any, Optional, List, AsyncGenerator
from functools import partial

from app.core.model_manager import model_manager
from app.core.cache import response_cache, cached_generate
from app.config import settings

logger = logging.getLogger(__name__)

# 创建线程池用于CPU密集型操作
thread_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=settings.async_worker_threads,
    thread_name_prefix="inference_worker"
)

class AsyncInferenceService:
    """异步推理服务"""
    
    def __init__(self):
        self.active_requests = 0
        self.total_requests = 0
        self.request_queue = asyncio.Queue(maxsize=settings.async_queue_size)
        self.batch_processor = None
        self._processing_task = None
        self._started = False
    
    async def start_processing(self):
        """启动后台处理任务（在事件循环运行后调用）"""
        if not self._started and (self._processing_task is None or self._processing_task.done()):
            self._processing_task = asyncio.create_task(self._process_requests())
            self._started = True
            logger.info("✅ 异步推理服务处理任务已启动")
    
    async def _process_requests(self):
        """处理请求队列的后台任务"""
        while True:
            try:
                # 从队列获取请求
                request_data = await self.request_queue.get()
                if request_data is None:  # 停止信号
                    break
                    
                model_name, prompt, kwargs, future = request_data
                
                # 执行推理
                try:
                    result = await self._execute_inference(model_name, prompt, **kwargs)
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self.request_queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"请求处理错误: {e}")
                await asyncio.sleep(0.1)  # 防止错误循环
    
    @cached_generate
    async def generate_text(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        异步生成文本
        
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
            # 创建Future用于异步结果
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            
            # 将请求放入队列
            await self.request_queue.put((model_name, prompt, kwargs, future))
            
            # 等待结果
            result = await future
            return result
            
        except Exception as e:
            logger.error(f"异步生成失败: {e}")
            raise
        finally:
            self.active_requests -= 1
    
    async def generate_stream(self, model_name: str, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步流式生成文本
        
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
                # 使用线程池执行同步的流式生成
                loop = asyncio.get_event_loop()
                
                # 创建生成器函数
                def stream_generator():
                    try:
                        return model.create_completion(prompt, stream=True, **kwargs)
                    except Exception as e:
                        logger.error(f"流式生成错误: {e}")
                        raise
                
                # 在线程池中执行
                completion_generator = await loop.run_in_executor(
                    thread_pool, stream_generator
                )
                
                # 流式返回结果
                for token in completion_generator:
                    yield {
                        "token": token['choices'][0]['text'],
                        "finished": False
                    }
                
                # 结束标志
                yield {"token": "", "finished": True}
                
            else:
                # 非流式模型的简化实现
                result = await self.generate_text(model_name, prompt, **kwargs)
                for char in result['text']:
                    yield {"token": char, "finished": False}
                yield {"token": "", "finished": True}
                
        except Exception as e:
            logger.error(f"流式推理失败: {e}")
            yield {"error": str(e), "finished": True}
        finally:
            self.active_requests -= 1
    
    async def _execute_inference(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        执行模型推理（在线程池中运行）
        
        Args:
            model_name: 模型名称
            prompt: 输入提示词
            **kwargs: 生成参数
            
        Returns:
            Dict: 生成结果
        """
        start_time = time.time()
        
        # 获取模型
        model = model_manager.get_model(model_name)
        if model is None:
            raise ValueError(f"模型未加载: {model_name}")
        
        # 在线程池中执行推理
        loop = asyncio.get_event_loop()
        
        if hasattr(model, 'create_completion'):
            # GGML模型推理
            inference_func = partial(
                model.create_completion, 
                prompt, 
                stream=False, 
                **kwargs
            )
            result = await loop.run_in_executor(thread_pool, inference_func)
            generated_text = result['choices'][0]['text']
            
        else:
            # HuggingFace模型推理
            def hf_inference():
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
                result_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                if result_text.startswith(prompt):
                    result_text = result_text[len(prompt):].strip()
                
                return result_text
            
            generated_text = await loop.run_in_executor(thread_pool, hf_inference)
        
        latency = time.time() - start_time
        
        response = {
            "text": generated_text,
            "usage": {
                "prompt_tokens": self._estimate_tokens(prompt),
                "completion_tokens": self._estimate_tokens(generated_text),
                "total_tokens": self._estimate_tokens(prompt) + self._estimate_tokens(generated_text)
            },
            "latency": latency
        }
        
        logger.info(f"推理完成: model={model_name}, latency={latency:.2f}s")
        return response
    
    def _estimate_tokens(self, text: str) -> int:
        """
        估算token数量
        
        Args:
            text: 文本内容
            
        Returns:
            int: 估算的token数量
        """
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
            "queue_size": self.request_queue.qsize(),
            "thread_pool_stats": {
                "max_workers": thread_pool._max_workers,
                "active_threads": thread_pool._work_queue.qsize(),
            },
            "cache_stats": response_cache.get_stats()
        }
    
    async def shutdown(self):
        """关闭服务"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # 清空队列
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
                self.request_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        # 停止线程池
        thread_pool.shutdown(wait=False)


# 全局异步推理服务实例
async_inference_service = AsyncInferenceService()


# 应用退出时清理资源
import atexit
@atexit.register
def cleanup_async_service():
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在当前事件循环中安排关闭任务
            asyncio.create_task(async_inference_service.shutdown())
        else:
            # 运行新的事件循环来执行关闭
            loop.run_until_complete(async_inference_service.shutdown())
    except:
        pass