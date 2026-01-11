from typing import Optional, Set
from pydantic import Field, SecretStr, PositiveInt
from app.core.config.base import EnvBaseSettings


class EmailSettings(EnvBaseSettings):
    EMAIL_HOST: str = Field(..., description="Mail server host")
    EMAIL_PORT: PositiveInt = Field(..., description="Mail server port")
    EMAIL_HOST_USER: str = Field(..., description="Mail server username")
    EMAIL_HOST_PASSWORD: SecretStr = Field(
        ..., repr=False, description="Mail server password"
    )
    EMAIL_USE_TLS: bool = Field(default=True, description="Use TLS")
    EMAIL_USE_SSL: bool = Field(default=False, description="Use SSL")
    EMAIL_TIMEOUT: PositiveInt = Field(
        default=60, description="Mail connection timeout (seconds)"
    )
    EMAIL_SSL_CERT_REQS: Optional[str] = Field(
        default="optional", description="SSL certificate verification"
    )
    EMAIL_EXPIRATION: PositiveInt = Field(
        default=300, description="Email verification code expiration time (seconds)"
    )

    # 允许的邮箱域名白名单
    ALLOWED_EMAIL_DOMAINS: Set[str] = Field(
        default={
            # 国际主流
            "gmail.com",
            "outlook.com",
            "hotmail.com",
            "live.com",
            "yahoo.com",
            "icloud.com",
            "me.com",
            "mac.com",
            "protonmail.com",
            "proton.me",
            # 国内主流
            "qq.com",
            "163.com",
            "126.com",
            "yeah.net",
            "sina.com",
            "sina.cn",
            "sohu.com",
            "foxmail.com",
            "aliyun.com",
        },
        description="Allowed email domains whitelist",
    )
