import asyncio
from app.core.logger import logger_manager
from app.core.celery import celery_app, with_db_init
from app.utils.email import email_service
from app.core.config.settings import settings


@celery_app.task(name="greeting_task", bind=True, max_retries=3, default_retry_delay=30)
@with_db_init
def greeting_email_task(self, user_email: str, language: str | None = None) -> None:
    """Greeting task"""
    try:
        logger = logger_manager.get_logger(__name__)
        logger.info("Greeting task")

        # 用户第一次登陆, 发送一封欢迎邮件
        if language == "zh":
            subject = f"[{settings.app.APP_NAME}] - 🌱 很高兴遇见你"
        else:
            subject = (
                f"[{settings.app.APP_NAME}] - 🌱 Hi there! A big warm welcome to you."
            )
        # 在Celery任务环境中运行异步发送
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(
            email_service.send_email(
                subject=subject,
                recipient=user_email,
                template="welcome",
                language=language,
            )
        )

    except Exception as e:
        logger.error(f"Greeting task failed: {e}")
        raise self.retry(exc=e)
