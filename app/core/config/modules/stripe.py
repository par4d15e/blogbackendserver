from pydantic import Field, SecretStr, HttpUrl
from app.core.config.base import EnvBaseSettings


class StripeSettings(EnvBaseSettings):
    STRIPE_SECRET_KEY: SecretStr = Field(
        ..., repr=False, description="Stripe secret key"
    )
    STRIPE_PUBLIC_KEY: SecretStr = Field(
        ..., repr=False, description="Stripe public key"
    )
    STRIPE_WEBHOOK_SECRET: SecretStr = Field(
        ..., repr=False, description="Stripe webhook secret key"
    )
    SUCCESS_URL: HttpUrl = Field(..., description="Stripe checkout success URL")
    CANCEL_URL: HttpUrl = Field(..., description="Stripe checkout cancel URL")
