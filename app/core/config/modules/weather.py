from pydantic import Field, SecretStr
from app.core.config.base import EnvBaseSettings


class WeatherSettings(EnvBaseSettings):
    OPENWEATHER_API_KEY: SecretStr = Field(
        ..., repr=False, description="OpenWeather API key"
    )
    OPENWEATHER_API_URL: str = Field(
        default="https://api.openweathermap.org/data/2.5/weather",
        description="OpenWeather API URL",
    )
    OPENWEATHER_API_ICON: str = Field(
        default="https://openweathermap.org/img/wn/",
        description="OpenWeather API default icon URL",
    )
