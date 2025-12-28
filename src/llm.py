"""LLM 统一管理模块"""

import asyncio
import time
from functools import wraps
from typing import Callable, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import config


class LLMManager:
    """LLM 调用管理器"""
    
    _instances: dict[str, ChatGoogleGenerativeAI] = {}
    _token_usage: dict[str, dict[str, int]] = {}
    
    @classmethod
    def get_model(cls, purpose: str) -> ChatGoogleGenerativeAI:
        """获取指定用途的模型实例
        
        Args:
            purpose: segment | translate | review
        """
        if purpose not in cls._instances:
            model_config = config.get_model(purpose)
            cls._instances[purpose] = ChatGoogleGenerativeAI(
                model=model_config["name"],
                google_api_key=config.api_key,
                max_output_tokens=model_config.get("max_tokens", 8192),
                temperature=0.3,  # 较低温度保证翻译稳定性
            )
            cls._token_usage[purpose] = {"input": 0, "output": 0}
        
        return cls._instances[purpose]
    
    @classmethod
    def track_usage(cls, purpose: str, input_tokens: int, output_tokens: int) -> None:
        """追踪 token 使用量"""
        if purpose not in cls._token_usage:
            cls._token_usage[purpose] = {"input": 0, "output": 0}
        cls._token_usage[purpose]["input"] += input_tokens
        cls._token_usage[purpose]["output"] += output_tokens
    
    @classmethod
    def get_usage(cls) -> dict[str, dict[str, int]]:
        """获取 token 使用统计"""
        return cls._token_usage.copy()
    
    @classmethod
    async def invoke(
        cls,
        purpose: str,
        prompt: str,
        system_prompt: str | None = None
    ) -> str:
        """调用 LLM
        
        Args:
            purpose: 模型用途
            prompt: 用户提示
            system_prompt: 系统提示（可选）
        
        Returns:
            模型响应文本
        """
        model = cls.get_model(purpose)
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = await model.ainvoke(messages)
        
        # 追踪 token 使用（估算）
        input_tokens = len(prompt) // 4  # 粗略估算
        output_tokens = len(response.content) // 4
        cls.track_usage(purpose, input_tokens, output_tokens)
        
        return response.content


def retry_with_backoff(
    max_attempts: int | None = None,
    backoff_base: int | None = None,
    backoff_max: int | None = None
) -> Callable:
    """带指数退避的重试装饰器
    
    使用配置文件中的默认值，也可以覆盖
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            retry_config = config.retry_config
            attempts = max_attempts or retry_config["max_attempts"]
            base = backoff_base or retry_config["backoff_base"]
            max_wait = backoff_max or retry_config["backoff_max"]
            
            last_exception = None
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < attempts - 1:
                        wait_time = min(base ** attempt, max_wait)
                        print(f"⚠️  重试 {attempt + 1}/{attempts}，等待 {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator


# 便捷函数
async def translate_text(text: str) -> str:
    """翻译文本"""
    return await LLMManager.invoke("translate", text)


async def review_translation(original: str, translation: str) -> str:
    """审核翻译"""
    prompt = f"## 原文\n{original}\n\n## 译文\n{translation}"
    return await LLMManager.invoke("review", prompt)
