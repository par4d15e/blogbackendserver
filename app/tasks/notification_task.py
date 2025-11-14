import asyncio
from sqlmodel import select
from app.schemas.common import NotificationType
from app.core.logger import logger_manager
from app.core.celery import celery_app, with_db_init
from app.core.config.settings import settings
from app.utils.email import email_service, EmailMessage
from app.models.user_model import User, RoleType
from app.core.database.mysql import mysql_manager


@celery_app.task(name="notification_task", bind=True, max_retries=3, default_retry_delay=30)
@with_db_init
def notification_task(self, notification_type: str | NotificationType, message: str) -> None:
    """Notification task"""
    try:
        logger = logger_manager.get_logger(__name__)
        logger.info(
            f"Notification task - notification_type: {notification_type}, type: {type(notification_type)}")

        # 处理 Enum 对象或字符串值
        if isinstance(notification_type, NotificationType):
            notification_type_value = notification_type.value
        else:
            notification_type_value = notification_type

        if notification_type_value == NotificationType.FRIEND_REQUEST.value:
            subject = f"[{settings.app.APP_NAME}] - 📢 好友请求"
        elif notification_type_value == NotificationType.PAYMENT_REQUEST.value:
            subject = f"[{settings.app.APP_NAME}] - 💰 支付成功通知"
        else:
            subject = f"[{settings.app.APP_NAME}] - 📢 Notification"

        # 获取role为admin的用户email
        with mysql_manager.get_sync_db() as session:
            admin_email = session.execute(select(User.email).where(
                User.role == RoleType.admin)).first()

            if not admin_email:
                logger.warning("No admin user found")
                return False

            admin_email = admin_email[0]

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Send simple text email without template
            email_message = EmailMessage(
                subject=subject,
                recipient=admin_email,
                sender=email_service.settings.email.EMAIL_HOST_USER,
            ).set_text_content(message)

            mime_message = email_message.build()
            loop.run_until_complete(
                email_service.backend.send_email(mime_message))

    except Exception as e:
        logger.error(f"Notification task failed: {e}")
        raise self.retry(exc=e)
