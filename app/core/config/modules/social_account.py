from pydantic import Field, SecretStr, HttpUrl
from app.core.config.base import EnvBaseSettings


class SocialAccountSettings(EnvBaseSettings):
    GITHUB_CLIENT_ID: SecretStr = Field(
        ..., repr=False, description="Github OAuth client ID"
    )
    GITHUB_CLIENT_SECRET: SecretStr = Field(
        ..., repr=False, description="Github OAuth client secret"
    )
    GITHUB_REDIRECT_URI: HttpUrl = Field(..., description="Github OAuth redirect URI")

    GOOGLE_CLIENT_ID: SecretStr = Field(
        ..., repr=False, description="Google OAuth client ID"
    )
    GOOGLE_CLIENT_SECRET: SecretStr = Field(
        ..., repr=False, description="Google OAuth client secret"
    )
    GOOGLE_REDIRECT_URI: HttpUrl = Field(..., description="Google OAuth redirect URI")
