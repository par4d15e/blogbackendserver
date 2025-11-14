from typing import List
from pydantic import Field, SecretStr, PositiveInt
from app.core.config.base import EnvBaseSettings


class CSRFSettings(EnvBaseSettings):
    CSRF_ENABLED: bool = Field(default=True, description="Enable CSRF protection")
    CSRF_SECRET_KEY: SecretStr = Field(
        default=SecretStr("your-secret-key-here-change-in-production"),
        repr=False,
        description="CSRF secret key",
    )
    CSRF_EXPIRATION: PositiveInt = Field(
        default=3600, description="CSRF expiration time (seconds)"
    )
    CSRF_TRUSTED_ORIGINS: List[str] = Field(
        default=["https://*.heyxiaoli.com"], description="Trusted origins for CSRF"
    )
