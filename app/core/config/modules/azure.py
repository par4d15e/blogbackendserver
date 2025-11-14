from pydantic import Field, SecretStr
from app.core.config.base import EnvBaseSettings


class AzureSettings(EnvBaseSettings):
    AZURE_SPEECH_KEY: SecretStr = Field(..., repr=False,
                                        description="Azure Speech API key")
    AZURE_SPEECH_REGION: str = Field(...,
                                     description="Azure Speech API region")
