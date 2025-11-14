from functools import cached_property

from app.core.config.modules.app import AppSettings
from app.core.config.modules.aws import AWSSettings
from app.core.config.modules.celery import CelerySettings
from app.core.config.modules.cors import CORSSettings
from app.core.config.modules.csrf import CSRFSettings
from app.core.config.modules.database import DatabaseSettings
from app.core.config.modules.qwen import QwenSettings
from app.core.config.modules.azure import AzureSettings
from app.core.config.modules.domain import DomainSettings
from app.core.config.modules.email import EmailSettings
from app.core.config.modules.files import FilesSettings
from app.core.config.modules.invoice import InvoiceSettings
from app.core.config.modules.jwt import JWTSettings
from app.core.config.modules.logging import LoggingSettings
from app.core.config.modules.rate_limit import RateLimitSettings
from app.core.config.modules.redis import RedisSettings
from app.core.config.modules.social_account import SocialAccountSettings
from app.core.config.modules.stripe import StripeSettings
from app.core.config.modules.weather import WeatherSettings


class Settings:
    @cached_property
    def app(self) -> AppSettings:
        return AppSettings()

    @cached_property
    def aws(self) -> AWSSettings:
        return AWSSettings()

    @cached_property
    def celery(self) -> CelerySettings:
        return CelerySettings()

    @cached_property
    def cors(self) -> CORSSettings:
        return CORSSettings()

    @cached_property
    def csrf(self) -> CSRFSettings:
        return CSRFSettings()

    @cached_property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings()

    @cached_property
    def qwen(self) -> QwenSettings:
        return QwenSettings()

    @cached_property
    def azure(self) -> AzureSettings:
        return AzureSettings()

    @cached_property
    def domain(self) -> DomainSettings:
        return DomainSettings()

    @cached_property
    def email(self) -> EmailSettings:
        return EmailSettings()

    @cached_property
    def files(self) -> FilesSettings:
        return FilesSettings()

    @cached_property
    def invoice(self) -> InvoiceSettings:
        return InvoiceSettings()

    @cached_property
    def jwt(self) -> JWTSettings:
        return JWTSettings()

    @cached_property
    def logging(self) -> LoggingSettings:
        return LoggingSettings()

    @cached_property
    def rate_limit(self) -> RateLimitSettings:
        return RateLimitSettings()

    @cached_property
    def redis(self) -> RedisSettings:
        return RedisSettings()

    @cached_property
    def social_account(self) -> SocialAccountSettings:
        return SocialAccountSettings()

    @cached_property
    def stripe(self) -> StripeSettings:
        return StripeSettings()

    @cached_property
    def weather(self) -> WeatherSettings:
        return WeatherSettings()


# Create a global settings instance
settings = Settings()
