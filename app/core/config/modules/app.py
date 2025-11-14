from pydantic import Field
from app.core.config.base import EnvBaseSettings


class AppSettings(EnvBaseSettings):
    """Application metadata configuration"""

    APP_NAME: str = Field(default="HeyXiaoli", description="Application name")

    APP_DESCRIPTION: str = Field(
        default="HeyXiaoli is a personal blog site built with FastAPI to share experiences on programming, technology, and life.",
        description="Application description",
    )

    APP_VERSION: str = Field(default="0.1.0", description="Application version")
