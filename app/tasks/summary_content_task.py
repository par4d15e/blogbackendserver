import asyncio
from datetime import datetime, timezone
from sqlmodel import select
from app.core.logger import logger_manager
from app.core.database.mysql import mysql_manager
from app.core.celery import celery_app, with_db_init
from app.utils.agent import agent_utils
from app.core.database.redis import redis_manager
from app.models.blog_model import Blog, Blog_Summary


@celery_app.task(
    name="summary blog content", bind=True, max_retries=3, default_retry_delay=30
)
@with_db_init
def summary_blog_content(self, blog_id: int) -> bool:
    """
    总结博客内容
    """
    logger = logger_manager.get_logger(__name__)

    try:
        with mysql_manager.get_sync_db() as session:
            blog = session.execute(select(Blog).where(Blog.id == blog_id)).first()
            if not blog:
                logger.warning(f"Blog not found with ID: {blog_id}")
                return False
            blog = blog[0]

            chinese_content = blog.chinese_content
            english_content = blog.english_content

            # 检查内容是否存在
            if not chinese_content and not english_content:
                logger.warning(f"No content found for blog ID: {blog_id}")
                return False

            # 获取或创建事件循环以调用异步的 agent_utils.summary
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，创建一个新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 初始化摘要结果
            chinese_summary = None
            english_summary = None

            # 在事件循环中运行异步函数生成摘要
            if chinese_content:
                try:
                    chinese_summary_result = loop.run_until_complete(
                        agent_utils.summary(chinese_content)
                    )
                    chinese_summary = chinese_summary_result
                    logger.info(
                        f"Successfully generated Chinese summary for blog ID: {blog_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to generate Chinese summary for blog ID {blog_id}: {str(e)}"
                    )
                    # 继续处理英文内容，不因为中文摘要失败而停止

            if english_content:
                try:
                    english_summary_result = loop.run_until_complete(
                        agent_utils.summary(english_content)
                    )
                    english_summary = english_summary_result
                    logger.info(
                        f"Successfully generated English summary for blog ID: {blog_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to generate English summary for blog ID {blog_id}: {str(e)}"
                    )
                    # 继续处理，不因为英文摘要失败而停止

            # 检查是否至少有一个摘要生成成功
            if not chinese_summary and not english_summary:
                logger.error(f"Failed to generate any summary for blog ID: {blog_id}")
                return False

            # 检查是否数据库存在
            blog_summary_result = session.execute(
                select(Blog_Summary).where(Blog_Summary.blog_id == blog_id)
            ).first()

            if blog_summary_result:
                # 如果存在，更新现有记录
                blog_summary = blog_summary_result[0]
                blog_summary.chinese_summary = chinese_summary
                blog_summary.english_summary = english_summary
                blog_summary.updated_at = datetime.now(timezone.utc)
                session.add(blog_summary)
                session.commit()
                logger.info(f"Updated existing summary for blog ID: {blog_id}")
            else:
                # 如果不存在，创建新记录
                blog_summary = Blog_Summary(
                    blog_id=blog_id,
                    chinese_summary=chinese_summary,
                    english_summary=english_summary,
                )
                session.add(blog_summary)
                session.commit()
                logger.info(f"Created new summary for blog ID: {blog_id}")

            # 清理缓存
            redis_manager.delete_pattern_sync(f"blog_summary:{blog_id}:*")
            logger.info(f"Successfully created summary for blog ID: {blog_id}")
            return True

    except Exception as e:
        logger.error(f"Error creating summary for blog ID {blog_id}: {str(e)}")
        # Retry the task if it fails
        raise self.retry(exc=e)
