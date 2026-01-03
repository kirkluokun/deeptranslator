"""重试装饰器"""

import asyncio
from functools import wraps
from typing import Callable, Any, TypeVar

from ..config import config

T = TypeVar('T')


def retry(
    max_attempts: int | None = None,
    backoff_base: float | None = None,
    backoff_max: float | None = None,
    exceptions: tuple = (Exception,)
) -> Callable:
    """带指数退避的重试装饰器
    
    Args:
        max_attempts: 最大重试次数（默认从配置读取）
        backoff_base: 退避基数秒数（默认从配置读取）
        backoff_max: 最大退避秒数（默认从配置读取）
        exceptions: 需要重试的异常类型
    
    Example:
        @retry(max_attempts=3)
        async def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            retry_config = config.retry_config
            attempts = max_attempts or retry_config["max_attempts"]
            base = backoff_base or retry_config["backoff_base"]
            max_wait = backoff_max or retry_config["backoff_max"]
            
            last_exception = None
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < attempts - 1:
                        wait_time = min(base ** attempt, max_wait)
                        print(f"⚠️  重试 {attempt + 1}/{attempts}，等待 {wait_time:.1f}s: {type(e).__name__}")
                        await asyncio.sleep(wait_time)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            import time
            retry_config = config.retry_config
            attempts = max_attempts or retry_config["max_attempts"]
            base = backoff_base or retry_config["backoff_base"]
            max_wait = backoff_max or retry_config["backoff_max"]
            
            last_exception = None
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < attempts - 1:
                        wait_time = min(base ** attempt, max_wait)
                        print(f"⚠️  重试 {attempt + 1}/{attempts}，等待 {wait_time:.1f}s: {type(e).__name__}")
                        time.sleep(wait_time)
            
            raise last_exception
        
        # 根据函数类型返回对应的 wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
