from pydantic import Field
from app.core.config.base import EnvBaseSettings


class DomainSettings(EnvBaseSettings):
    DOMAIN_URL: str = Field(..., description="Domain for the application")
