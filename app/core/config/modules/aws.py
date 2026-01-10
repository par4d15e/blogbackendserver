from pydantic import Field, SecretStr
from app.core.config.base import EnvBaseSettings


class AWSSettings(EnvBaseSettings):
    """AWS configuration settings"""

    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS access key ID")

    AWS_SECRET_ACCESS_KEY: SecretStr = Field(
        default=SecretStr(""), description="AWS secret access key"
    )

    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_BUCKET_NAME: str = Field(default="", description="S3 bucket name")
