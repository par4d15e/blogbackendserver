from pydantic import Field, PositiveInt
from app.core.config.base import EnvBaseSettings


class RateLimitSettings(EnvBaseSettings):
    RATE_LIMIT: PositiveInt = Field(
        default=5, description="Maximum requests per minute"
    )
    PER_SECONDS: PositiveInt = Field(default=60, description="Rate limit per seconds")
