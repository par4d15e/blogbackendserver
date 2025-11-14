from celery import Celery
from celery.schedules import crontab
from app.core.config.settings import settings
import asyncio
from functools import wraps
from app.core.database.mysql import mysql_manager
from app.core.logger import logger_manager


def with_db_init(func):
    """装饰器：为Celery任务自动初始化数据库连接"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logger_manager.get_logger(__name__)

        # 初始化数据库连接（Celery worker需要单独初始化）
        async def init_db():
            try:
                await mysql_manager.initialize()
                logger.debug(
                    "Database initialized successfully for Celery task")
            except Exception as e:
                logger.error(
                    f"Failed to initialize database for Celery task: {e}")
                raise

        # 在Celery任务中运行异步初始化
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(init_db())
        except Exception as e:
            logger.error(f"Database initialization failed in Celery task: {e}")
            raise

        # 执行原始任务
        return func(*args, **kwargs)

    return wrapper


class CeleryManager:
    def __init__(self):
        self.celery_app = Celery(
            "app",
            broker=settings.celery.CELERY_BROKER_URL,
            backend=settings.celery.CELERY_RESULT_BACKEND,
        )

    def setup(self):
        self.celery_app.conf.update(
            broker_connection_retry_on_startup=True,
            accept_content=settings.celery.CELERY_ACCEPT_CONTENT,
            task_serializer=settings.celery.CELERY_TASK_SERIALIZER,
            result_serializer=settings.celery.CELERY_RESULT_SERIALIZER,
            timezone=settings.celery.CELERY_TIMEZONE,
            enable_utc=settings.celery.CELERY_ENABLE_UTC,
        )

    def autodiscovery(self):
        self.celery_app.autodiscover_tasks(
            packages=["app.tasks"],
            force=True,
        )

    def start(self):
        self.celery_app.start()

    def close(self):
        self.celery_app.close()


# Create a celery app instance
celery_app = Celery(
    "app",
    broker=settings.celery.CELERY_BROKER_URL,
    backend=settings.celery.CELERY_RESULT_BACKEND,
)

# Configure the celery app
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    accept_content=settings.celery.CELERY_ACCEPT_CONTENT,
    task_serializer=settings.celery.CELERY_TASK_SERIALIZER,
    result_serializer=settings.celery.CELERY_RESULT_SERIALIZER,
    timezone=settings.celery.CELERY_TIMEZONE,
    enable_utc=settings.celery.CELERY_ENABLE_UTC,
    # 保守策略配置：适合 2核心 2GB 服务器
    worker_concurrency=2,  # 最多 2 个 worker 进程
    worker_prefetch_multiplier=1,  # 避免 worker 预取过多任务
    task_acks_late=True,  # 任务完成后再确认
    worker_max_tasks_per_child=100,  # 每个 worker 处理 100 个任务后重启
    task_time_limit=3600,  # 任务超时时间：1小时
    task_soft_time_limit=3000,  # 软超时时间：50分钟
    # 防止任务重复执行的配置
    task_reject_on_worker_lost=True,  # worker 崩溃时拒绝任务，避免重复执行
    task_ignore_result=False,  # 保存任务结果以便追踪
    # 确保任务只执行一次
    task_always_eager=False,  # 确保任务异步执行
    worker_disable_rate_limits=False,  # 启用速率限制
    # 使用唯一标识符防止重复
    task_store_eager_result=True,  # 存储eager模式的结果
)

# Auto-discover tasks
# 移除 force=True 避免任务被重复注册
celery_app.autodiscover_tasks(
    packages=["app.tasks"],
    force=False,  # 改为 False，避免重复注册任务
)

# Configure Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'backup-database-daily': {
        'task': 'backup_database_task',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨 3 点执行
        'args': (None, 30),  # (database_name=None, retention_days=30)
        'options': {
            'expires': 3600,  # 任务过期时间：1小时
        }
    }
}
