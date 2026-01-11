"""
清理未验证用户的定时任务
每天凌晨 2 点批量删除 is_verified=False 的用户
"""

import asyncio
from datetime import datetime, timedelta

from sqlmodel import select, delete
from sqlalchemy import func

from app.core.celery import celery_app, with_db_init
from app.core.database.mysql import mysql_manager
from app.core.logger import logger_manager
from app.models.user_model import User

logger = logger_manager.get_logger(__name__)


@celery_app.task(
    name="cleanup_unverified_users_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    time_limit=1800,  # 30 分钟超时
    soft_time_limit=1500,  # 25 分钟软超时
)
@with_db_init
def cleanup_unverified_users_task(self, retention_hours: int = 24) -> dict:
    """
    清理未验证的用户账户
    
    Args:
        retention_hours: 保留时间（小时），超过此时间且未验证的用户将被删除
                        默认 24 小时，即只删除注册超过 24 小时仍未验证的用户
    
    Returns:
        dict: 清理结果
    """
    
    async def _cleanup():
        try:
            async with mysql_manager.get_session() as db:
                # 计算截止时间：只删除注册超过 retention_hours 的未验证用户
                cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
                
                # 先统计要删除的用户数量
                count_stmt = select(func.count(User.id)).where(
                    User.is_verified == False,
                    User.created_at < cutoff_time
                )
                result = await db.execute(count_stmt)
                count = result.scalar_one()
                
                if count == 0:
                    logger.info("没有需要清理的未验证用户")
                    return {
                        "success": True,
                        "deleted_count": 0,
                        "message": "没有需要清理的未验证用户",
                    }
                
                logger.info(f"准备删除 {count} 个未验证用户（注册超过 {retention_hours} 小时）")
                
                # 批量删除
                delete_stmt = delete(User).where(
                    User.is_verified == False,
                    User.created_at < cutoff_time
                )
                await db.execute(delete_stmt)
                await db.commit()
                
                logger.info(f"✅ 成功删除 {count} 个未验证用户")
                
                return {
                    "success": True,
                    "deleted_count": count,
                    "cutoff_time": cutoff_time.isoformat(),
                    "retention_hours": retention_hours,
                    "message": f"成功删除 {count} 个未验证用户",
                }
                
        except Exception as e:
            logger.error(f"清理未验证用户失败: {e}", exc_info=True)
            raise
    
    try:
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_cleanup())
        
    except Exception as e:
        logger.error(f"清理任务执行失败: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300)
        
        return {
            "success": False,
            "error": str(e),
            "message": "清理任务执行失败",
        }
