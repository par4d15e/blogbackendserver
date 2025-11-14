from pydantic import Field, PositiveInt
from app.core.config.base import EnvBaseSettings


class DatabaseSettings(EnvBaseSettings):
    # 数据库连接 URL
    DATABASE_URL: str = Field(
        default="mysql://user:password@localhost:3306/heyxiaoli_dev",
        description="Database connection URL",
    )

    # 连接池配置
    ECHO: bool = Field(default=False, description="Database connection pool echo")

    POOL_PRE_PING: bool = Field(
        default=True, description="Database connection pool pre-ping"
    )

    POOL_TIMEOUT: PositiveInt = Field(
        default=30, description="Database connection pool timeout (seconds)"
    )

    POOL_SIZE: PositiveInt = Field(
        default=6,
        description="Database connection pool size (保守策略：适合 2核心 2GB 服务器)",
    )

    POOL_MAX_OVERFLOW: PositiveInt = Field(
        default=2,
        description="Database connection pool max overflow (保守策略：降低溢出连接)",
    )
