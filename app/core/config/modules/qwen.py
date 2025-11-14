from pydantic import Field, SecretStr
from app.core.config.base import EnvBaseSettings


class QwenSettings(EnvBaseSettings):
    QWEN_API_KEY: SecretStr = Field(..., repr=False, description="DeepSeek API key")
    QWEN_API_MAX_RETRIES: int = Field(
        default=3, description="DeepSeek API maximum retries"
    )
