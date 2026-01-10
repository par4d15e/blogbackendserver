from typing import List
from pydantic import Field
from app.core.config.base import EnvBaseSettings


class CelerySettings(EnvBaseSettings):
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL. Defaults to Redis. Supports password: redis://:password@host:port",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL. Defaults to Redis. Supports password: redis://:password@host:port",
    )
    CELERY_CONNECTION_RETRY: bool = Field(
        default=True, description="Celery broker connection retry on startup"
    )
    CELERY_ACCEPT_CONTENT: List[str] = Field(
        default=["json"], description="Celery accepted content types"
    )
    CELERY_TASK_SERIALIZER: str = Field(
        default="json", description="Celery task serializer"
    )
    CELERY_RESULT_SERIALIZER: str = Field(
        default="json", description="Celery result serializer"
    )
    CELERY_MAX_TIRES: int = Field(
        default=3, description="Maximum number of retries for a task"
    )
    CELERY_TIMEZONE: str = Field(default="UTC", description="Celery timezone")
    CELERY_ENABLE_UTC: bool = Field(default=True, description="Enable UTC for Celery")
