"""
数据模型模块 - 请求和响应数据模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    model_loaded: bool = Field(..., description="模型是否加载")
    memory_usage: str = Field(..., description="内存使用情况")
    active_connections: int = Field(..., description="活跃连接数")
    version: str = Field(..., description="服务版本")


class GenerateRequest(BaseModel):
    """文本生成请求模型"""
    prompt: str = Field(..., description="输入提示词")
    model: str = Field("default", description="模型名称")
    max_tokens: Optional[int] = Field(512, description="最大生成token数")
    temperature: Optional[float] = Field(0.7, description="温度参数")
    stream: Optional[bool] = Field(False, description="是否流式输出")


class GenerateResponse(BaseModel):
    """文本生成响应模型"""
    text: str = Field(..., description="生成的文本")
    usage: Dict[str, int] = Field(..., description="token使用情况")
    latency: float = Field(..., description="推理耗时(秒)")


class StreamToken(BaseModel):
    """流式token模型"""
    token: str = Field(..., description="生成的token")
    finished: bool = Field(..., description="是否生成完成")


class ModelInfo(BaseModel):
    """模型信息模型"""
    name: str = Field(..., description="模型名称")
    format: str = Field(..., description="模型格式")
    size: str = Field(..., description="模型大小")
    loaded: bool = Field(..., description="是否已加载")
    memory_usage: str = Field(..., description="内存使用量")


class ModelsResponse(BaseModel):
    """模型列表响应模型"""
    models: List[ModelInfo] = Field(..., description="模型列表")


class LoadModelRequest(BaseModel):
    """加载模型请求模型"""
    quantization: Optional[str] = Field("q4_0", description="量化方式")
    prefer_gpu: Optional[bool] = Field(False, description="是否优先使用GPU")
    n_ctx: Optional[int] = Field(2048, description="上下文长度")
    n_threads: Optional[int] = Field(4, description="线程数")


# OpenAI兼容模型
class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")


class ChatCompletionRequest(BaseModel):
    """OpenAI聊天补全请求模型"""
    model: str = Field(..., description="模型名称")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    max_tokens: Optional[int] = Field(None, description="最大生成token数")
    temperature: Optional[float] = Field(0.7, description="温度参数")
    stream: Optional[bool] = Field(False, description="是否流式输出")


class ChatCompletionChoice(BaseModel):
    """聊天补全选择模型"""
    index: int = Field(..., description="索引")
    message: ChatMessage = Field(..., description="消息")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class ChatCompletionUsage(BaseModel):
    """token使用情况模型"""
    prompt_tokens: int = Field(..., description="提示token数")
    completion_tokens: int = Field(..., description="生成token数")
    total_tokens: int = Field(..., description="总token数")


class ChatCompletionResponse(BaseModel):
    """OpenAI聊天补全响应模型"""
    id: str = Field(..., description="请求ID")
    object: str = Field(..., description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[ChatCompletionChoice] = Field(..., description="选择列表")
    usage: ChatCompletionUsage = Field(..., description="使用情况")


class CompletionRequest(BaseModel):
    """OpenAI补全请求模型"""
    model: str = Field(..., description="模型名称")
    prompt: str = Field(..., description="提示词")
    max_tokens: Optional[int] = Field(None, description="最大生成token数")
    temperature: Optional[float] = Field(0.7, description="温度参数")


class CompletionChoice(BaseModel):
    """补全选择模型"""
    text: str = Field(..., description="生成的文本")
    index: int = Field(..., description="索引")
    logprobs: Optional[Any] = Field(None, description="对数概率")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class CompletionResponse(BaseModel):
    """OpenAI补全响应模型"""
    id: str = Field(..., description="请求ID")
    object: str = Field(..., description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[CompletionChoice] = Field(..., description="选择列表")
    usage: ChatCompletionUsage = Field(..., description="使用情况")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: Dict[str, str] = Field(..., description="错误信息")


# 批量请求模型
class BatchGenerateRequest(BaseModel):
    """批量生成请求模型"""
    requests: List[GenerateRequest] = Field(..., description="请求列表")


class BatchGenerateResponse(BaseModel):
    """批量生成响应模型"""
    results: List[GenerateResponse] = Field(..., description="结果列表")