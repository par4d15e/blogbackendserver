import hashlib
from functools import wraps
from typing import Callable, Awaitable
from fastapi import Request, HTTPException
from app.core.database.redis import redis_manager
from app.utils.client_info import client_info_utils


def rate_limiter(limit: int = 5, seconds: int = 60):
    def decorator(func: Callable[..., Awaitable]):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            ip = client_info_utils.get_client_ip(request)
            user_agent = client_info_utils.get_user_agent(request)

            # 计算哈希值
            hash_key = hashlib.sha256(f"{ip}:{user_agent}".encode()).hexdigest()

            # 使用原子性递增操作获取当前计数
            client = await redis_manager.get_async_client()
            current_count = await client.incr(hash_key)

            if current_count == 1:
                # 第一次访问, 设置过期时间
                await client.expire(hash_key, seconds)

            if current_count > limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests, please try again later",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
