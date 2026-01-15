"""
清理过期 Token 的定时任务
每天凌晨 1 点批量删除已过期或未激活的 Token
"""

from datetime import datetime

from sqlmodel import select, delete, or_, func

from app.core.celery import celery_app, with_db_init
from app.core.database.mysql import mysql_manager
from app.core.logger import logger_manager
from app.models.auth_model import RefreshToken

logger = logger_manager.get_logger(__name__)


@celery_app.task(
    name="cleanup_expired_tokens_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    time_limit=1800,  # 30 分钟超时
    soft_time_limit=1500,  # 25 分钟软超时
)
@with_db_init
def cleanup_expired_tokens_task(self) -> dict:
    """
    清理过期或未激活的 Refresh Token

    清理条件：
    1. 已过期的 refresh token (expired_at <= 当前时间)
    2. 未激活的 refresh token (is_active = False)

    Returns:
        dict: 清理结果
    """

    def _cleanup():
        # 使用同步会话（Celery 任务是同步的）
        db = mysql_manager.get_sync_db()

        try:
            # 先统计要删除的 refresh token 数量
            count_stmt = select(func.count(RefreshToken.id)).where(
                or_(
                    func.utc_timestamp() >= RefreshToken.expired_at,
                    RefreshToken.is_active == False,
                )
            )
            result = db.execute(count_stmt)
            count = result.scalar_one()

            if count == 0:
                logger.info("没有需要清理的过期或未激活 Refresh Token")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "没有需要清理的过期或未激活 Refresh Token",
                }

            logger.info(f"准备删除 {count} 个过期或未激活的 Refresh Token")

            # 批量删除过期或未激活的 refresh token
            delete_stmt = delete(RefreshToken).where(
                or_(
                    func.utc_timestamp() >= RefreshToken.expired_at,
                    RefreshToken.is_active == False,
                )
            )
            db.execute(delete_stmt)
            db.commit()

            logger.info(f"✅ 成功删除 {count} 个过期或未激活的 Refresh Token")

            return {
                "success": True,
                "deleted_count": count,
                "cleanup_time": datetime.utcnow().isoformat(),
                "message": f"成功删除 {count} 个过期或未激活的 Refresh Token",
            }

        except Exception as e:
            db.rollback()
            logger.error(f"清理过期 Refresh Token 失败: {e}", exc_info=True)
            raise
        finally:
            db.close()

    try:
        # 直接调用同步函数
        return _cleanup()

    except Exception as e:
        logger.error(f"清理任务执行失败: {e}", exc_info=True)

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300)

        return {
            "success": False,
            "error": str(e),
            "message": "清理任务执行失败",
        }
