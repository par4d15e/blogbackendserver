"""
邮箱域名验证装饰器
只允许主流邮箱服务商的邮箱地址
"""

from functools import wraps
from typing import Callable, Awaitable
from fastapi import Request, HTTPException
from app.core.i18n.i18n import get_message
from app.core.config.settings import settings


def validate_email_domain(email_field: str = "email"):
    """
    验证邮箱域名是否为主流邮箱服务商
    
    Args:
        email_field: 请求体中邮箱字段的名称，默认为 "email"
    
    Usage:
        @router.post("/send-verification-code")
        @validate_email_domain()
        async def send_code(request: Request, form_data: SendCodeRequest):
            ...
    """
    def decorator(func: Callable[..., Awaitable]):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 从 kwargs 中获取 form_data
            form_data = kwargs.get("form_data")
            if form_data is None:
                # 尝试从 args 中获取
                for arg in args:
                    if hasattr(arg, email_field):
                        form_data = arg
                        break
            
            if form_data is None:
                return await func(request, *args, **kwargs)
            
            # 获取邮箱地址
            email = getattr(form_data, email_field, None)
            if not email or "@" not in email:
                raise HTTPException(
                    status_code=400,
                    detail=get_message("auth.common.invalidEmailFormat"),
                )
            
            # 提取域名并验证
            domain = email.split("@")[-1].lower()
            if domain not in settings.email.ALLOWED_EMAIL_DOMAINS:
                raise HTTPException(
                    status_code=400,
                    detail=get_message("auth.common.unsupportedEmailDomain"),
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
