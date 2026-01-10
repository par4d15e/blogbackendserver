import asyncio
import json
from typing import Optional
from sqlmodel import select
from app.core.logger import logger_manager
from app.core.database.mysql import mysql_manager
from app.core.celery import celery_app, with_db_init
from app.utils.agent import agent_utils
from app.models.blog_model import Blog
from app.models.project_model import Project
from app.schemas.common import LargeContentTranslationType
from app.core.database.redis import redis_manager


@celery_app.task(
    name="large_content_translation_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
@with_db_init
def large_content_translation_task(
    self, content: dict, content_type: LargeContentTranslationType, content_id: int
) -> Optional[bool]:
    """
    翻译富文本内容中的文本和caption，保持原有JSON结构

    改进的错误处理：
    - 当翻译API返回内容过滤错误时，会正确识别并记录
    - 如果原内容中没有中文，翻译结果与原内容相同是正常行为，不会抛出异常
    - 对内容过滤错误使用不同的重试策略（更少重试次数，更长间隔）
    """
    logger = logger_manager.get_logger(__name__)

    try:
        # 在同步函数中运行异步翻译
        logger.info(
            f"Starting translation for content_id: {content_id}, type: {content_type}"
        )
        logger.debug(
            f"Original content: {json.dumps(content, ensure_ascii=False)}")

        try:
            translated_content = asyncio.run(
                agent_utils.large_content_translation(content)
            )
            logger.debug(
                f"Translated content: {json.dumps(translated_content, ensure_ascii=False)}"
            )

            # 检查翻译是否成功
            # 注意：如果原内容中没有中文，翻译结果与原内容相同是正常的
            if translated_content == content:
                logger.info(
                    "Translation completed - content unchanged (likely no Chinese content to translate)"
                )
            else:
                logger.info(
                    "Translation completed successfully - content has been modified"
                )

        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)

            # 根据错误类型提供更详细的日志信息
            if "inappropriate content" in error_message.lower():
                logger.error(
                    f"Translation failed due to content filtering: {error_message}"
                )
                logger.error(
                    "The content may contain sensitive or inappropriate material that violates API policies"
                )
            elif "HTTPException" in error_type:
                logger.error(f"Translation API HTTP error: {error_message}")
            elif "timeout" in error_message.lower():
                logger.error(f"Translation timeout: {error_message}")
            else:
                logger.error(
                    f"Translation failed with {error_type}: {error_message}")

            # 重新抛出异常，让任务重试或失败
            raise

        # 验证内容类型
        if content_type not in [
            LargeContentTranslationType.BLOG,
            LargeContentTranslationType.PROJECT,
        ]:
            logger.warning(f"Invalid content type: {content_type}")
            return False

        # 使用同步方式更新数据库
        with mysql_manager.get_sync_db() as session:
            if content_type == LargeContentTranslationType.BLOG:
                # 检查是否有blog
                blog_result = session.execute(
                    select(Blog).where(Blog.id == content_id)
                ).first()
                if not blog_result:
                    logger.warning(f"Blog not found with ID: {content_id}")
                    return False

                blog = blog_result[0]  # 解包元组获取Blog对象

                # 更新博客内容
                blog.english_content = translated_content
                session.add(blog)
                session.commit()

                # 更新缓存
                redis_manager.delete_pattern_sync(
                    f"blog_details:{blog.slug}:*")
                redis_manager.delete_pattern_sync(f"blog_tts:{content_id}")
                redis_manager.delete_pattern_sync(
                    f"blog_summary:{content_id}:*")
                logger.info(
                    f"Successfully translated blog content for blog ID: {content_id}"
                )
                return True

            elif content_type == LargeContentTranslationType.PROJECT:
                # 检查是否有项目
                project_result = session.execute(
                    select(Project).where(Project.id == content_id)
                ).first()
                if not project_result:
                    logger.warning(f"Project not found with ID: {content_id}")
                    return False

                project = project_result[0]  # 解包元组获取Project对象

                # 更新项目内容
                project.english_content = translated_content
                session.add(project)
                session.commit()

                # 更新缓存
                redis_manager.delete_pattern_sync(
                    f"project_details:{project.slug}:*")
                redis_manager.delete_pattern_sync(f"project_tts:{content_id}")
                redis_manager.delete_pattern_sync(
                    f"project_summary:{content_id}:*")

                logger.info(
                    f"Successfully translated project content for project ID: {content_id}"
                )
                return True

    except Exception as e:
        error_message = str(e)
        error_type = type(e).__name__

        # 对于内容过滤错误，使用更长的重试间隔，因为内容本身可能有问题
        if "inappropriate content" in error_message.lower():
            logger.error(
                f"Content filtering error in large_content_translation_task: {error_message}"
            )
            logger.error(
                "This content may violate API content policies and may not be translatable"
            )
            # 对于内容过滤错误，减少重试次数或使用更长的间隔
            if self.request.retries < 2:  # 只重试2次而不是3次
                raise self.retry(exc=e, countdown=300)  # 5分钟重试间隔
            else:
                logger.error(
                    "Max retries reached for content filtering error - task will fail"
                )
                return False
        else:
            logger.error(
                f"Error in large_content_translation_task: {error_message}")
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=60)
            return False
