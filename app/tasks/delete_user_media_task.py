from sqlmodel import select
from sqlalchemy.orm import load_only
from sqlalchemy import delete
from app.models.user_model import User
from app.models.media_model import Media
from app.core.logger import logger_manager
from app.core.database.mysql import mysql_manager
from app.core.celery import celery_app, with_db_init
from app.utils.s3_bucket import create_s3_bucket


@celery_app.task(
    name="delete_user_media", bind=True, max_retries=3, default_retry_delay=30
)
@with_db_init
def delete_user_media_task(self, user_id: int) -> None:
    """
    删除指定用户的所有媒体文件
    包括从S3删除文件和从数据库删除记录
    """
    from app.core.config.settings import settings
    from app.core.config.modules.aws import AWSSettings

    logger = logger_manager.get_logger(__name__)
    logger.info(f"开始删除用户 {user_id} 的所有媒体文件")

    try:
        # 安全地获取AWS设置
        try:
            aws_settings = settings.aws
            aws_bucket_name = aws_settings.AWS_BUCKET_NAME
            aws_region = aws_settings.AWS_REGION
        except AttributeError as e:
            logger.warning(f"无法从settings获取AWS配置，使用默认值: {e}")
            # 创建新的AWS设置实例作为后备
            aws_settings = AWSSettings()
            aws_bucket_name = aws_settings.AWS_BUCKET_NAME
            aws_region = aws_settings.AWS_REGION

        # 第一步：删除S3中的媒体文件
        s3_deletion_success = False
        with mysql_manager.get_sync_db() as session:
            # 获取用户所有媒体文件的URL
            statement = (
                select(Media)
                .options(
                    load_only(
                        Media.id,
                        Media.original_filepath_url,
                        Media.thumbnail_filepath_url,
                        Media.watermark_filepath_url,
                    )
                )
                .filter(
                    # 只删除s3文件
                    Media.original_filepath_url.like(
                        f"%{aws_bucket_name}.s3.{aws_region}.amazonaws.com/%"
                    )
                )
                .where(Media.user_id == user_id)
            )

            result = session.execute(statement)
            media_records = result.scalars().all()

            if not media_records:
                logger.info(f"用户 {user_id} 没有媒体文件需要删除")
                s3_deletion_success = True  # 没有文件需要删除，视为成功
            else:
                logger.info(f"找到 {len(media_records)} 个媒体记录需要删除")

                # 收集所有需要删除的S3文件键
                s3_keys_to_delete = []

                # 创建S3客户端
                s3_bucket = create_s3_bucket()

                for media in media_records:
                    # 提取原始文件的S3键
                    if media.original_filepath_url:
                        original_key = s3_bucket.extract_s3_key(
                            media.original_filepath_url
                        )
                        if original_key:
                            s3_keys_to_delete.append(original_key)

                    # 提取缩略图文件的S3键
                    if media.thumbnail_filepath_url:
                        thumbnail_key = s3_bucket.extract_s3_key(
                            media.thumbnail_filepath_url
                        )
                        if thumbnail_key:
                            s3_keys_to_delete.append(thumbnail_key)

                    # 提取水印文件的S3键
                    if media.watermark_filepath_url:
                        watermark_key = s3_bucket.extract_s3_key(
                            media.watermark_filepath_url
                        )
                        if watermark_key:
                            s3_keys_to_delete.append(watermark_key)

                # 去重
                s3_keys_to_delete = list(set(s3_keys_to_delete))
                logger.info(f"准备删除 {len(s3_keys_to_delete)} 个S3文件")

                # 批量删除S3文件
                if s3_keys_to_delete:
                    try:

                        def progress_callback(deleted_count, total_files, _):
                            logger.info(f"S3删除进度: {deleted_count}/{total_files}")

                        deletion_results = s3_bucket.delete_files(
                            s3_keys=s3_keys_to_delete,
                            progress_callback=progress_callback,
                            max_workers=5,
                        )

                        # 统计删除结果
                        if isinstance(deletion_results, dict):
                            success_count = sum(
                                1 for success in deletion_results.values() if success
                            )
                            failed_keys = [
                                key
                                for key, success in deletion_results.items()
                                if not success
                            ]

                            logger.info(
                                f"S3文件删除完成: {success_count}/{len(s3_keys_to_delete)} 成功"
                            )
                            if failed_keys:
                                logger.warning(f"删除失败的S3文件: {failed_keys}")
                                # 即使有部分失败，也继续删除用户
                                s3_deletion_success = True
                            else:
                                s3_deletion_success = True
                        else:
                            logger.info(f"S3文件删除结果: {deletion_results}")
                            s3_deletion_success = True
                    except Exception as s3_error:
                        logger.error(f"S3文件删除失败: {s3_error}")
                        s3_deletion_success = False
                    finally:
                        # 关闭S3客户端
                        s3_bucket.close()
                else:
                    s3_deletion_success = True

        # 第二步：删除用户（数据库会自动级联删除相关的媒体文件）
        if s3_deletion_success:
            try:
                with mysql_manager.get_sync_db() as session:
                    delete_statement = delete(User).where(User.id == user_id)
                    deleted_rows = session.execute(delete_statement)
                    session.commit()
                    logger.info(
                        f"用户 {user_id} 已从数据库删除，影响行数: {deleted_rows.rowcount}"
                    )
            except Exception as db_error:
                logger.error(f"删除用户 {user_id} 失败: {db_error}")
                raise self.retry(exc=db_error, countdown=60)
        else:
            logger.error("S3文件删除失败，跳过用户删除")
            raise self.retry(exc=Exception("S3文件删除失败"), countdown=60)

    except Exception as e:
        logger.error(f"删除用户 {user_id} 媒体文件时发生错误: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return None
