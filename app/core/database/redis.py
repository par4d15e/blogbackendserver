from typing import Optional, cast
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio import from_url as async_from_url
from redis import Redis as SyncRedis
from redis import from_url as sync_from_url
from app.core.config.settings import settings
from app.core.logger import logger_manager


class RedisManager:
    """Redis 连接管理器 - 支持异步和同步客户端"""

    def __init__(self):
        self.logger = logger_manager.get_logger(__name__)
        self.async_client: Optional[AsyncRedis] = None
        self.sync_client: Optional[SyncRedis] = None
        self.config = settings.redis

    async def initialize_async(self) -> None:
        """初始化异步 Redis 客户端 - 用于 FastAPI"""
        if self.async_client:
            self.logger.debug("Redis async client already initialized.")
            return

        try:
            self.async_client = async_from_url(
                self.config.REDIS_CONNECTION_URL,
                decode_responses=True,
                max_connections=self.config.REDIS_POOL_SIZE,
                socket_timeout=self.config.REDIS_SOCKET_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self.logger.info("✅ Redis async client initialized.")
        except Exception:
            self.logger.exception("❌ Failed to initialize Redis async client.")
            raise

    def initialize_sync(self) -> None:
        """初始化同步 Redis 客户端 - 用于 Celery"""
        if self.sync_client:
            self.logger.debug("Redis sync client already initialized.")
            return

        try:
            self.sync_client = sync_from_url(
                self.config.REDIS_CONNECTION_URL,
                decode_responses=True,
                max_connections=self.config.REDIS_POOL_SIZE,
                socket_timeout=self.config.REDIS_SOCKET_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self.logger.info("✅ Redis sync client initialized.")
        except Exception:
            self.logger.exception("❌ Failed to initialize Redis sync client.")
            raise

    # -------------------------------
    # ✅ 异步方法 - FastAPI 使用
    # -------------------------------

    async def get_async_client(self) -> AsyncRedis:
        if not self.async_client:
            await self.initialize_async()
        # 此时 self.async_client 不为 None
        assert self.async_client is not None
        return self.async_client

    async def get_async(self, key: str) -> Optional[str]:
        client = await self.get_async_client()
        result = await client.get(key)
        return result.decode() if isinstance(result, bytes) else result

    async def set_async(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        client = await self.get_async_client()
        ex = ex or self.config.REDIS_DEFAULT_TTL
        return await client.set(key, value, ex=ex)

    async def delete_async(self, *keys: str) -> int:
        client = await self.get_async_client()
        return await client.delete(*keys)

    async def delete_pattern_async(self, pattern: str) -> int:
        client = await self.get_async_client()
        keys = await client.keys(pattern)
        return await client.delete(*keys) if keys else 0

    async def exists_async(self, key: str) -> bool:
        """检查键是否存在（异步）"""
        client = await self.get_async_client()
        result = await client.exists(key)
        return result > 0

    async def async_test_connection(self) -> bool:
        try:
            client = await self.get_async_client()
            await client.ping()
            self.logger.info("✅ Redis async client connection test successful.")
            return True
        except Exception:
            self.logger.exception("❌ Redis async client connection test failed.")
            raise

    # -------------------------------
    # ✅ 同步方法 - Celery / 脚本使用
    # -------------------------------

    def get_sync_client(self) -> SyncRedis:
        if not self.sync_client:
            self.initialize_sync()
        # 此时 self.sync_client 不为 None
        assert self.sync_client is not None
        return self.sync_client

    def get_sync(self, key: str) -> Optional[str]:
        result = self.get_sync_client().get(key)
        if result is None:
            return None
        return result.decode() if isinstance(result, bytes) else cast(str, result)

    def set_sync(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        ex = ex or self.config.REDIS_DEFAULT_TTL
        result = self.get_sync_client().set(key, value, ex=ex)
        return cast(bool, result)

    def delete_sync(self, *keys: str) -> int:
        result = self.get_sync_client().delete(*keys)
        return cast(int, result)

    def delete_pattern_sync(self, pattern: str) -> int:
        client = self.get_sync_client()
        keys = client.keys(pattern)
        if not keys:
            return 0
        result = client.delete(*keys)
        return cast(int, result)

    def sync_test_connection(self) -> bool:
        try:
            client = self.get_sync_client()
            client.ping()
            self.logger.info("✅ Redis sync client connection test successful.")
            return True
        except Exception:
            self.logger.exception("❌ Redis sync client connection test failed.")
            raise

    # -------------------------------
    # ✅ 清理资源
    # -------------------------------

    async def close(self) -> None:
        """关闭异步和同步客户端"""
        if self.async_client:
            try:
                await self.async_client.close()
                self.async_client = None
                self.logger.info("✅ Redis async client closed.")
            except Exception:
                self.logger.exception("❌ Failed to close Redis async client.")

        if self.sync_client:
            try:
                self.sync_client.close()
                self.sync_client = None
                self.logger.info("✅ Redis sync client closed.")
            except Exception:
                self.logger.exception("❌ Failed to close Redis sync client.")

    async def __aenter__(self) -> "RedisManager":
        await self.initialize_async()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()


# 单例
redis_manager = RedisManager()
