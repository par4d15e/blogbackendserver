from typing import Any, Optional

from app.core.logger import logger_manager
from app.core.database.mysql import mysql_manager
from app.core.database.redis import redis_manager

logger = logger_manager.get_logger(__name__)


class DatabaseConnectionManager:
    """数据库连接管理器 - 统一管理 Redis 和 MySQL 连接"""

    def __init__(self):
        self.redis_manager = redis_manager
        self.mysql_manager = mysql_manager

    async def initialize(self) -> None:
        """初始化所有数据库连接"""
        await self.redis_manager.initialize_async()
        await self.mysql_manager.initialize()

    async def test_connections(self) -> bool:
        """测试所有数据库连接"""
        try:
            # 测试 Redis 连接
            await self.redis_manager.async_test_connection()
            self.redis_manager.sync_test_connection()

            # 测试 MySQL 连接
            await self.mysql_manager.test_connection()

            logger.info("✅ All database connections tested successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            raise

    async def close(self) -> None:
        """关闭所有数据库连接"""
        await self.redis_manager.close()
        await self.mysql_manager.close()

    async def __aenter__(self) -> "DatabaseConnectionManager":
        """进入上下文管理器"""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Optional[Any],
    ) -> None:
        """退出上下文管理器"""
        if exc_type is not None:
            logger.error(
                f"❌ Exception occurred in DatabaseConnectionManager context: {exc_type.__name__}: {exc_value}"
            )
        await self.close()
        # 返回 False 表示不抑制异常，让异常继续传播
        return False


db_manager = DatabaseConnectionManager()
