from sqlalchemy import Update
from app.core.logger import logger_manager
from app.models.user_model import User
from app.utils.client_info import client_info_utils
from app.core.database.mysql import mysql_manager
from app.core.celery import celery_app, with_db_init


@celery_app.task(
    name="client_info_task", bind=True, max_retries=3, default_retry_delay=30
)
@with_db_init
def client_info_task(self, user_id: int, request_headers: dict = None) -> None:
    """获取客户端IP地址并更新地理位置信息的Background任务"""
    logger = logger_manager.get_logger(__name__)

    try:
        logger.info(f"开始处理用户 {user_id} 的客户端信息更新")

        # 从请求头中获取客户端IP地址
        ip_address = None
        if request_headers:
            ip_address = client_info_utils.get_client_ip_from_headers(request_headers)

        # 如果无法获取IP地址或为本地地址，使用默认IP
        if not ip_address or ip_address in ["localhost", "127.0.0.1", "::1"]:
            ip_address = "218.107.132.66"  # 默认IP地址 北京
            logger.info(f"使用默认IP地址: {ip_address}")

        # 获取地理位置信息
        location_data = client_info_utils.get_ip_location(ip_address)

        # 使用同步方式更新数据库
        with mysql_manager.get_sync_db() as session:
            try:
                # 准备更新数据
                update_values = {"ip_address": ip_address}

                # 如果成功获取到地理位置信息，添加到更新数据中
                if (
                    location_data
                    and location_data.get("city")
                    and location_data.get("city") != "未知"
                ):
                    update_values.update(
                        {
                            "city": location_data.get("city"),
                            "latitude": location_data.get("latitude"),
                            "longitude": location_data.get("longitude"),
                        }
                    )
                    logger.info(
                        f"用户 {user_id} 的IP地址和地理位置信息更新成功: {ip_address} -> {location_data.get('city')}"
                    )
                else:
                    logger.info(
                        f"用户 {user_id} 的IP地址更新成功: {ip_address} (无法获取地理位置)"
                    )

                # 执行数据库更新
                stmt = Update(User).where(User.id == user_id).values(**update_values)
                result = session.execute(stmt)

                if result.rowcount == 0:
                    logger.warning(f"用户 {user_id} 不存在，无法更新客户端信息")
                    return None

                session.commit()
                logger.info(f"用户 {user_id} 客户端信息更新完成")

            except Exception as e:
                session.rollback()
                logger.error(f"更新用户 {user_id} 客户端信息失败: {e}")
                raise self.retry(exc=e, countdown=60)

    except Exception as e:
        logger.error(f"处理用户 {user_id} 客户端信息失败: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return None
