from typing import Optional
from pydantic import Field, PositiveInt, SecretStr
from app.core.config.base import EnvBaseSettings


class JWTSettings(EnvBaseSettings):
    JWT_SECRET_KEY: SecretStr = Field(
        ..., repr=False, description="Secret key used to sign JWTs"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Algorithm used for JWT")
    JWT_ACCESS_TOKEN_EXPIRATION: PositiveInt = Field(
        default=1800, description="JWT access token expiration time (seconds)"
    )
    JWT_REFRESH_TOKEN_EXPIRATION: PositiveInt = Field(
        default=604800,
        description="JWT refresh token expiration time (seconds) - 7 days",
    )
    JWT_ISSUER: Optional[str] = Field(default="xiaoli", description="JWT issuer")
    JWT_AUDIENCE: Optional[str] = Field(
        default="xiaoli_users", description="JWT audience"
    )
