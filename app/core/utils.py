"""
工具函数模块
"""

import os
import re
from typing import List, Dict, Any
from app.config import MODEL_CONFIGS


def detect_model_type(model_path: str) -> str:
    """
    自动检测模型类型
    
    Args:
        model_path: 模型文件路径
        
    Returns:
        str: 模型类型 (qwen, gemma, llama, chatglm, unknown)
    """
    model_name = os.path.basename(model_path).lower()
    
    # Qwen模型检测
    if any(keyword in model_name for keyword in ['qwen', 'qianwen']):
        return 'qwen'
    
    # Gemma模型检测
    if any(keyword in model_name for keyword in ['gemma']):
        return 'gemma'
    
    # LLaMA模型检测
    if any(keyword in model_name for keyword in ['llama', 'alpaca', 'vicuna']):
        return 'llama'
    
    # ChatGLM模型检测
    if any(keyword in model_name for keyword in ['chatglm', 'glm']):
        return 'chatglm'
    
    return 'unknown'


def format_qwen_chat(messages: List[Dict[str, str]]) -> str:
    """
    将消息列表转换为Qwen对话格式
    
    Args:
        messages: 消息列表，每个消息包含role和content
        
    Returns:
        str: 格式化后的Qwen对话文本
    """
    formatted = ""
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'system':
            formatted += f"<|im_start|>system\n{content}<|im_end|>\n"
        elif role == 'user':
            formatted += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == 'assistant':
            formatted += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        else:
            # 未知角色，默认作为用户消息处理
            formatted += f"<|im_start|>user\n{content}<|im_end|>\n"
    
    # 添加助手开始标记
    formatted += "<|im_start|>assistant\n"
    return formatted


def format_gemma_chat(messages: List[Dict[str, str]]) -> str:
    """
    将消息列表转换为Gemma对话格式
    
    Args:
        messages: 消息列表，每个消息包含role和content
        
    Returns:
        str: 格式化后的Gemma对话文本
    """
    conversation = []
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'system':
            conversation.append(f"<start_of_turn>system\n{content}<end_of_turn>")
        elif role == 'user':
            conversation.append(f"<start_of_turn>user\n{content}<end_of_turn>")
        elif role == 'assistant':
            conversation.append(f"<start_of_turn>model\n{content}<end_of_turn>")
        else:
            # 未知角色，默认作为用户消息处理
            conversation.append(f"<start_of_turn>user\n{content}<end_of_turn>")
    
    # 添加模型开始标记
    conversation.append("<start_of_turn>model\n")
    return "\n".join(conversation)


def format_llama_chat(messages: List[Dict[str, str]]) -> str:
    """
    将消息列表转换为LLaMA对话格式
    
    Args:
        messages: 消息列表，每个消息包含role和content
        
    Returns:
        str: 格式化后的LLaMA对话文本
    """
    formatted = ""
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'system':
            formatted += f"<s>[INST] <<SYS>>\n{content}\n<</SYS>>\n\n"
        elif role == 'user':
            formatted += f"{content} [/INST] "
        elif role == 'assistant':
            formatted += f"{content}</s>"
        else:
            formatted += f"{content} "
    
    return formatted


def get_model_config(model_type: str) -> Dict[str, Any]:
    """
    获取模型特定配置
    
    Args:
        model_type: 模型类型
        
    Returns:
        Dict: 模型配置
    """
    return MODEL_CONFIGS.get(model_type, {})


def sanitize_model_name(model_name: str) -> str:
    """
    清理模型名称，移除特殊字符
    
    Args:
        model_name: 原始模型名称
        
    Returns:
        str: 清理后的模型名称
    """
    # 移除特殊字符，只保留字母、数字、下划线、短横线
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', model_name)
    # 移除连续的下划线
    sanitized = re.sub(r'_+', '_', sanitized)
    # 移除开头和结尾的下划线/短横线
    sanitized = sanitized.strip('_-')
    
    return sanitized.lower()


def calculate_token_count(text: str) -> int:
    """
    估算文本的token数量（简单实现）
    
    Args:
        text: 输入文本
        
    Returns:
        int: 估算的token数量
    """
    # 简单估算：英文约4字符一个token，中文约2字符一个token
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other_chars = len(text) - chinese_chars
    
    # 估算token数
    token_count = (chinese_chars / 2) + (other_chars / 4)
    return max(1, int(token_count))


def is_safe_prompt(prompt: str) -> bool:
    """
    检查提示词是否安全（基础实现）
    
    Args:
        prompt: 输入提示词
        
    Returns:
        bool: 是否安全
    """
    # 简单的安全检查
    unsafe_patterns = [
        r'\b(admin|root|system)\b',
        r'\.\./',  # 路径遍历
        r'<script>',  # XSS
        r'exec\(|system\(|subprocess\.',  # 命令执行
    ]
    
    for pattern in unsafe_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False
    
    return True


def format_bytes(size: int) -> str:
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