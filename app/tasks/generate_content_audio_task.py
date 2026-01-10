import uuid
from pathlib import Path
from sqlmodel import select
from app.core.logger import logger_manager
from app.core.database.mysql import mysql_manager
from app.core.celery import celery_app, with_db_init
from app.utils.agent import agent_utils
from app.models.blog_model import Blog, Blog_TTS
from app.models.media_model import Media, MediaType
from app.core.database.redis import redis_manager
from app.utils.s3_bucket import create_s3_bucket

from app.core.i18n.i18n import Language


def generate_audio_for_text(text: str, language: Language) -> str:
    """
    为文本生成音频

    Args:
        text: 要转换为音频的文本
        language: 语言标识

    Returns:
        str: 生成的音频文件路径
    """
    logger = logger_manager.get_logger(__name__)

    if not text or not text.strip():
        raise Exception("No text content to process")

    logger.info(f"Generating audio for {language} text (length: {len(text)})")

    try:
        # 直接生成音频，无需分割
        audio_result = agent_utils.synthesize(text, language)
        audio_path = audio_result["audio_path"]

        logger.info(f"Successfully generated audio file: {audio_path}")
        return audio_path

    except Exception as e:
        logger.error(f"Failed to generate audio: {e}")
        raise Exception(f"Audio generation failed: {e}")


def save_audio_to_media_db(
    session, audio_path: str, user_id: int, language: str
) -> Media:
    """
    将音频文件保存到数据库并返回Media对象

    Args:
        session: 数据库会话
        audio_path: 本地音频文件路径
        user_id: 用户ID
        language: 语言标识

    Returns:
        Media: 保存后的Media对象
    """
    logger = logger_manager.get_logger(__name__)

    try:
        # 生成唯一UUID
        media_uuid = str(uuid.uuid4())

        # 获取文件信息
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise Exception(f"Audio file does not exist: {audio_path}")

        file_name = f"{media_uuid}.opus"
        file_size = audio_file.stat().st_size

        # 生成S3键
        s3_key = f"audio/{user_id}/{media_uuid}.opus"

        # 上传到S3
        with create_s3_bucket() as s3_bucket:
            upload_success = s3_bucket.upload_files(
                file_paths=str(audio_path),
                s3_keys=s3_key,
                acl="public-read",  # 音频文件设为公开访问
            )

            if not upload_success:
                raise Exception(f"Failed to upload audio file to S3: {s3_key}")

            # 获取文件URL
            file_url = s3_bucket.get_file_url(s3_key)

        # 创建Media记录
        media = Media(
            uuid=media_uuid,
            user_id=user_id,
            type=MediaType.audio,
            is_avatar=False,
            is_content_audio=True,
            file_name=file_name,
            original_filepath_url=file_url,
            file_size=file_size,
        )

        session.add(media)
        session.commit()
        session.refresh(media)

        # 清理缓存
        redis_manager.delete_pattern_sync("blog_tts:*")

        logger.info(f"Successfully saved audio to database: {file_url}")
        return media

    except Exception as e:
        logger.error(f"Failed to save audio to database: {e}")
        raise Exception(f"Failed to save audio: {e}")


@celery_app.task(
    name="generate_content_audio_task", bind=True, max_retries=3, default_retry_delay=30
)
@with_db_init
def generate_content_audio_task(self, blog_id: int) -> bool:
    """
    生成内容音频
    """
    logger = logger_manager.get_logger(__name__)

    try:
        with mysql_manager.get_sync_db() as session:
            blog_result = session.execute(
                select(Blog).where(Blog.id == blog_id)
            ).first()
            if not blog_result:
                logger.warning(f"Blog not found with ID: {blog_id}")
                return False

            blog = blog_result[0]  # 解包元组获取Blog对象

            chinese_content = blog.chinese_content
            english_content = blog.english_content
            if not chinese_content and not english_content:
                logger.warning(f"No content found for blog ID: {blog_id}")
                return False

            # 初始化音频变量
            chinese_media = None
            english_media = None

            if chinese_content:
                # 从JSON内容中提取文本
                extracted_data = agent_utils.extract_full_text_from_content(
                    chinese_content
                )
                chinese_text = extracted_data.get("full_text", "").strip()

                if chinese_text:
                    audio_path = None
                    try:
                        # 生成中文音频
                        audio_path = generate_audio_for_text(
                            chinese_text, Language.ZH_CN)

                        # 保存到数据库
                        chinese_media = save_audio_to_media_db(
                            session, audio_path, blog.user_id, "zh"
                        )

                        logger.info(
                            f"Successfully generated Chinese audio for blog ID: {blog_id}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to generate Chinese audio for blog ID {blog_id}: {e}"
                        )
                        chinese_media = None
                    finally:
                        # 确保临时文件被清理
                        if audio_path:
                            Path(audio_path).unlink(missing_ok=True)

            if english_content:
                # 从JSON内容中提取文本
                extracted_data = agent_utils.extract_full_text_from_content(
                    english_content
                )
                english_text = extracted_data.get("full_text", "").strip()

                if english_text:
                    audio_path = None
                    try:
                        # 生成英文音频
                        audio_path = generate_audio_for_text(
                            english_text, Language.EN_US)

                        # 保存到数据库
                        english_media = save_audio_to_media_db(
                            session, audio_path, blog.user_id, "en"
                        )

                        logger.info(
                            f"Successfully generated English audio for blog ID: {blog_id}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to generate English audio for blog ID {blog_id}: {e}"
                        )
                        english_media = None
                    finally:
                        # 确保临时文件被清理
                        if audio_path:
                            Path(audio_path).unlink(missing_ok=True)

            # 检查Blog_TTS是否存在
            blog_tts_result = session.execute(
                select(Blog_TTS).where(Blog_TTS.blog_id == blog_id)
            ).first()

            # 确保至少有一个音频文件才创建/更新记录
            if chinese_media or english_media:
                if blog_tts_result:
                    # 更新现有的Blog_TTS记录
                    blog_tts = blog_tts_result[0]  # 解包元组获取Blog_TTS对象

                    # 先获取旧的音频文件信息，用于删除S3中的旧文件
                    old_chinese_media = None
                    old_english_media = None

                    if blog_tts.chinese_tts_id:
                        old_chinese_media_result = session.execute(
                            select(Media).where(
                                Media.id == blog_tts.chinese_tts_id)
                        ).first()
                        if old_chinese_media_result:
                            old_chinese_media = old_chinese_media_result[0]

                    if blog_tts.english_tts_id:
                        old_english_media_result = session.execute(
                            select(Media).where(
                                Media.id == blog_tts.english_tts_id)
                        ).first()
                        if old_english_media_result:
                            old_english_media = old_english_media_result[0]

                    # 更新TTS记录
                    if chinese_media:
                        blog_tts.chinese_tts_id = chinese_media.id
                    if english_media:
                        blog_tts.english_tts_id = english_media.id
                    session.add(blog_tts)
                    session.commit()

                    # 删除S3中的旧音频文件
                    try:
                        with create_s3_bucket() as s3_bucket:
                            # 收集需要删除的S3键
                            s3_keys_to_delete = []

                            if old_chinese_media and chinese_media:
                                # 从URL中提取S3键
                                old_s3_key = s3_bucket.extract_s3_key(
                                    old_chinese_media.original_filepath_url
                                )
                                if old_s3_key:
                                    s3_keys_to_delete.append(old_s3_key)

                            if old_english_media and english_media:
                                # 从URL中提取S3键
                                old_s3_key = s3_bucket.extract_s3_key(
                                    old_english_media.original_filepath_url
                                )
                                if old_s3_key:
                                    s3_keys_to_delete.append(old_s3_key)

                            # 批量删除S3文件
                            if s3_keys_to_delete:
                                s3_bucket.delete_files(s3_keys_to_delete)
                                logger.info(
                                    f"Deleted {len(s3_keys_to_delete)} old audio files from S3"
                                )

                            # 删除数据库中的旧Media记录
                            if old_chinese_media and chinese_media:
                                session.delete(old_chinese_media)
                            if old_english_media and english_media:
                                session.delete(old_english_media)
                            session.commit()

                    except Exception as e:
                        logger.error(f"Failed to delete old audio files: {e}")
                        # 即使删除旧文件失败，也不影响新文件的保存

                else:
                    # 创建新的Blog_TTS记录
                    blog_tts = Blog_TTS(
                        blog_id=blog_id,
                        chinese_tts_id=chinese_media.id if chinese_media else None,
                        english_tts_id=english_media.id if english_media else None,
                    )
                    session.add(blog_tts)
                    session.commit()

                    # 清理缓存
                    redis_manager.delete_pattern_sync("blog_tts:*")
                    logger.info(
                        f"Successfully created new Blog_TTS record for blog ID: {blog_id}"
                    )

            logger.info(
                f"Successfully generated content audio for blog ID: {blog_id}")
            return True
    except Exception as e:
        logger.error(
            f"Failed to generate content audio for blog ID {blog_id}: {e}")
        # 重试任务如果失败
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return False
