import gzip
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List

from app.core.celery import celery_app, with_db_init
from app.core.config.settings import settings
from app.core.logger import logger_manager
from app.utils.s3_bucket import create_s3_bucket
from botocore.exceptions import ClientError

logger = logger_manager.get_logger(__name__)


def _parse_database_url(database_url: str) -> dict:
    """
    解析数据库连接 URL

    Args:
        database_url: 格式如 mysql://user:password@host:port/database

    Returns:
        dict: 包含 host, port, user, password, database 的字典
    """
    try:
        parsed = urlparse(database_url)

        # 处理 mysql:// 或 mysql+pymysql:// 等格式
        if parsed.scheme.startswith("mysql"):
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            user = parsed.username or "root"
            password = parsed.password or ""
            database = parsed.path.lstrip("/") if parsed.path else "blog"

            return {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": database,
            }
        else:
            raise ValueError(f"不支持的数据库类型: {parsed.scheme}")
    except Exception as e:
        logger.error(f"解析数据库 URL 失败: {e}")
        raise


def _dump_database(db_config: dict, output_file: Path) -> bool:
    """
    使用 mysqldump 导出数据库

    Args:
        db_config: 数据库配置字典
        output_file: 输出文件路径

    Returns:
        bool: 是否成功
    """
    try:
        # 构建 mysqldump 命令
        cmd = [
            "mysqldump",
            f"--host={db_config['host']}",
            f"--port={db_config['port']}",
            f"--user={db_config['user']}",
            "--single-transaction",  # 保证数据一致性
            "--routines",  # 包含存储过程和函数
            "--triggers",  # 包含触发器
            "--events",  # 包含事件
            "--quick",  # 快速模式
            "--lock-tables=false",  # 不锁定表
            db_config["database"],
        ]

        # 设置密码环境变量（更安全）
        env = os.environ.copy()
        if db_config["password"]:
            env["MYSQL_PWD"] = db_config["password"]

        logger.info(f"开始导出数据库: {db_config['database']}")

        # 执行 mysqldump
        with open(output_file, "wb") as f:
            subprocess.run(
                cmd, stdout=f, stderr=subprocess.PIPE, env=env, check=True
            )

        # 检查文件大小
        file_size = output_file.stat().st_size
        if file_size == 0:
            logger.error("导出的数据库文件为空")
            return False

        file_size_mb = file_size / 1024 / 1024
        logger.info(f"数据库导出成功: {output_file.name} ({file_size_mb:.2f} MB)")
        return True

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"mysqldump 执行失败: {error_msg}")
        return False
    except Exception as e:
        logger.error(f"导出数据库时出错: {e}")
        return False


def _compress_file(input_file: Path, output_file: Path) -> bool:
    """
    压缩文件

    Args:
        input_file: 输入文件路径
        output_file: 输出压缩文件路径

    Returns:
        bool: 是否成功
    """
    try:
        logger.info(f"开始压缩文件: {input_file.name}")

        with open(input_file, "rb") as f_in:
            with gzip.open(output_file, "wb", compresslevel=6) as f_out:
                f_out.writelines(f_in)

        original_size = input_file.stat().st_size
        compressed_size = output_file.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100

        logger.info(
            f"压缩完成: {output_file.name} "
            f"({compressed_size / 1024 / 1024:.2f} MB, "
            f"压缩率: {compression_ratio:.1f}%)"
        )
        return True

    except Exception as e:
        logger.error(f"压缩文件时出错: {e}")
        return False


def _upload_to_s3(local_file: Path, s3_key: str) -> bool:
    """
    上传文件到 S3

    Args:
        local_file: 本地文件路径
        s3_key: S3 对象键

    Returns:
        bool: 是否成功
    """
    # 检查文件是否存在
    if not local_file.exists():
        logger.error(f"本地文件不存在: {local_file}")
        return False

    file_size = local_file.stat().st_size
    logger.info(f"开始上传到 S3: {s3_key} (文件大小: {file_size / 1024 / 1024:.2f} MB)")

    try:
        logger.info(f"准备上传文件到 S3: {local_file} -> {s3_key}")
        logger.info("AWS配置检查:")
        logger.info(f"  - Bucket: {settings.aws.AWS_BUCKET_NAME}")
        logger.info(f"  - Region: {settings.aws.AWS_REGION}")
        logger.info(
            f"  - Access Key配置: {'是' if settings.aws.AWS_ACCESS_KEY_ID else '否'}"
        )

        with create_s3_bucket() as s3_bucket:
            logger.info(f"S3 bucket 连接成功，bucket: {settings.aws.AWS_BUCKET_NAME}")

            # 上传文件到S3
            upload_success = s3_bucket.upload_files(
                file_paths=str(local_file),
                s3_keys=s3_key,
                metadata_list={
                    "backup_type": "database",
                    "backup_date": datetime.now().isoformat(),
                },
                verify=True,  # 启用验证以确保上传成功
            )

            logger.info(
                f"upload_files 调用完成，返回值: {upload_success} (类型: {type(upload_success)})"
            )

            # 判断上传是否成功
            # upload_files 返回 bool (单文件) 或 Dict[str, bool] (多文件)
            if isinstance(upload_success, bool):
                if not upload_success:
                    error_msg = f"文件上传到S3失败: {s3_key}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
            elif isinstance(upload_success, dict):
                # 多文件上传的情况（不应该发生，但防御性编程）
                if not upload_success.get(s3_key, False):
                    error_msg = f"文件上传到S3失败: {s3_key}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
            else:
                # 未知返回类型
                error_msg = f"upload_files 返回未知类型: {type(upload_success)}, 值: {upload_success}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.info(f"上传成功: s3://{settings.aws.AWS_BUCKET_NAME}/{s3_key}")
            return True

    except Exception as e:
        logger.error(
            f"上传到 S3 失败: {s3_key}, 文件: {local_file}, 大小: {file_size} bytes, 错误: {e}",
            exc_info=True,
        )
        return False


def _list_backup_files(s3_bucket, prefix: str) -> List[dict]:
    """
    列出 S3 中的备份文件

    Args:
        s3_bucket: RobustS3Bucket 实例
        prefix: S3 路径前缀，如 "backups/database/"

    Returns:
        List[dict]: 包含 'Key' 和 'LastModified' 的文件列表
    """
    try:
        files = []
        paginator = s3_bucket.s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(
            Bucket=settings.aws.AWS_BUCKET_NAME, Prefix=prefix
        ):
            if "Contents" in page:
                for obj in page["Contents"]:
                    files.append(
                        {
                            "Key": obj["Key"],
                            "LastModified": obj["LastModified"],
                            "Size": obj.get("Size", 0),
                        }
                    )

        return files
    except ClientError as e:
        logger.error(f"列出 S3 文件失败: {e}")
        return []
    except Exception as e:
        logger.error(f"列出 S3 文件时出错: {e}")
        return []


def _cleanup_old_backups(database_name: str, retention_days: int) -> None:
    """
    清理 S3 中的旧备份文件

    Args:
        database_name: 数据库名称
        retention_days: 保留天数
    """
    if retention_days <= 0:
        logger.info("保留天数 <= 0，跳过清理")
        return

    try:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        logger.info(f"开始清理 {cutoff_date.strftime('%Y-%m-%d')} 之前的备份文件")

        with create_s3_bucket() as s3_bucket:
            # 列出所有备份文件
            prefix = "backups/database/"
            backup_files = _list_backup_files(s3_bucket, prefix)

            if not backup_files:
                logger.info("没有找到备份文件")
                return

            # 筛选需要删除的文件（根据数据库名称和日期）
            files_to_delete = []
            for file_info in backup_files:
                key = file_info["Key"]
                last_modified = file_info["LastModified"]

                # 检查是否匹配数据库名称
                if database_name and database_name not in key:
                    continue

                # 检查是否超过保留期限
                # S3 返回的 LastModified 是带时区的 datetime 对象
                if isinstance(last_modified, datetime):
                    file_date = last_modified
                else:
                    # 如果是字符串或其他格式，尝试解析
                    try:
                        file_date = datetime.fromisoformat(
                            str(last_modified).replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        logger.warning(f"无法解析文件日期: {key}, 跳过")
                        continue

                # 转换为本地时区（UTC）进行比较
                if file_date.tzinfo:
                    # 转换为 UTC 时区，然后移除时区信息以便比较
                    file_date = file_date.astimezone(timezone.utc).replace(tzinfo=None)

                if file_date < cutoff_date:
                    files_to_delete.append(key)

            if not files_to_delete:
                logger.info("没有需要清理的旧备份文件")
                return

            logger.info(f"找到 {len(files_to_delete)} 个需要删除的旧备份文件")

            # 批量删除
            deletion_results = s3_bucket.delete_files(
                s3_keys=files_to_delete, max_workers=5
            )

            # 统计删除结果
            if isinstance(deletion_results, dict):
                success_count = sum(
                    1 for success in deletion_results.values() if success
                )
                failed_count = len(deletion_results) - success_count
                logger.info(
                    f"清理完成: 成功删除 {success_count} 个文件，"
                    f"失败 {failed_count} 个文件"
                )
            else:
                logger.info(f"清理完成: {deletion_results}")

    except Exception as e:
        logger.error(f"清理旧备份文件时出错: {e}", exc_info=True)


@celery_app.task(
    name="backup_database_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 失败后 5 分钟重试
    time_limit=3600,  # 1 小时硬超时
    soft_time_limit=3300,  # 55 分钟软超时
)
@with_db_init
def backup_database_task(
    self, database_name: Optional[str] = None, retention_days: int = 30
) -> dict:
    """
    备份数据库到 S3

    Args:
        database_name: 数据库名称，默认从 DATABASE_URL 解析
        retention_days: 保留天数，超过此天数的备份文件将被自动删除（设置为 0 或负数则不清理）

    Returns:
        dict: 备份结果信息
    """
    sql_file = None
    gz_file = None

    try:
        # 1. 解析数据库配置
        database_url = settings.database.DATABASE_URL
        db_config = _parse_database_url(database_url)

        if database_name:
            db_config["database"] = database_name

        logger.info(f"开始备份数据库: {db_config['database']}")

        # 2. 创建临时目录
        temp_dir = Path("/tmp/backups")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 3. 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = db_config["database"]
        sql_file = temp_dir / f"{db_name}_backup_{timestamp}.sql"
        gz_file = temp_dir / f"{db_name}_backup_{timestamp}.sql.gz"

        # 4. 导出数据库
        if not _dump_database(db_config, sql_file):
            raise Exception("数据库导出失败")

        # 5. 压缩文件
        if not _compress_file(sql_file, gz_file):
            raise Exception("文件压缩失败")

        # 6. 上传到 S3
        date_path = datetime.now().strftime("%Y/%m/%d")
        s3_key = f"backups/database/{date_path}/{db_name}_backup_{timestamp}.sql.gz"

        # 检查压缩文件是否存在
        if not gz_file.exists():
            raise Exception(f"压缩文件不存在: {gz_file}")

        gz_file_size = gz_file.stat().st_size
        logger.info(
            f"准备上传文件: {gz_file} (大小: {gz_file_size / 1024 / 1024:.2f} MB)"
        )

        if not _upload_to_s3(gz_file, s3_key):
            # 记录更详细的错误信息
            error_msg = (
                f"上传到 S3 失败: {s3_key}, 文件: {gz_file}, 大小: {gz_file_size} bytes"
            )
            logger.error(error_msg)
            raise Exception(error_msg)

        # 7. 清理本地文件
        sql_file.unlink(missing_ok=True)
        gz_file.unlink(missing_ok=True)

        # 8. 清理旧备份文件
        if retention_days > 0:
            try:
                _cleanup_old_backups(db_name, retention_days)
            except Exception as cleanup_error:
                # 清理失败不影响备份成功
                logger.warning(f"清理旧备份文件失败: {cleanup_error}")

        result = {
            "success": True,
            "database": db_name,
            "s3_key": s3_key,
            "timestamp": timestamp,
            "retention_days": retention_days,
            "message": "备份成功",
        }

        logger.info(f"✅ 备份完成: {s3_key}")
        return result

    except Exception as e:
        logger.error(f"备份失败: {e}", exc_info=True)

        # 清理可能的临时文件
        for file in [sql_file, gz_file]:
            if file and file.exists():
                try:
                    file.unlink()
                    logger.debug(f"已清理临时文件: {file}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败 {file}: {cleanup_error}")

        # 重试任务
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300)

        # 超过重试次数，返回失败结果
        return {
            "success": False,
            "database": database_name or "unknown",
            "error": str(e),
            "message": "备份失败",
        }
