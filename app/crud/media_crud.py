import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import lazyload
from sqlmodel import insert, select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media_model import Media, MediaType
from app.core.database.mysql import mysql_manager
from app.core.database.redis import redis_manager
from app.core.logger import logger_manager
from app.core.i18n.i18n import get_message, Language
from app.utils.offset_pagination import offset_paginator


class MediaCrud:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger_manager.get_logger(__name__)

    async def get_media(self, media_id: int, user_id: Optional[int] = None):
        """
        根据media_id和user_id获取媒体文件
        移除了uuid参数以提升性能，因为media_id已经是唯一主键
        """

        filter_conditions = [
            Media.id == media_id,
        ]
        if user_id:
            filter_conditions.append(Media.user_id == user_id,
                                     )

        statement = (
            select(Media)
            .options(lazyload("*"))
            .where(*filter_conditions)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_media_lists(
        self,
        user_id: int,
        page: int,
        size: int,
        language: Language,
        media_type: Optional[MediaType] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        # 验证分页参数
        try:
            page, size = offset_paginator.validate_pagination_params(
                page, size)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=get_message("common.invalidRequest", language),
            )

        cache_key = f"media_lists:{user_id}:{media_type}:{page}:{size}"
        cached_data = await redis_manager.get_async(cache_key)
        if cached_data:
            payload = json.loads(cached_data)
            return payload.get("items", []), payload.get("pagination", {})

        # 构建查询条件
        where_conditions = [
            Media.user_id == user_id,
            Media.is_avatar == False,
            Media.is_content_audio == False,
        ]

        # 只有当media_type不为None时才添加类型过滤条件
        if media_type is not None:
            where_conditions.append(Media.type == media_type)

        # 构建查询语句 - 过滤掉头像文件
        base_stmt = (
            select(Media)
            .options(lazyload("*"))
            .where(*where_conditions)
        )

        # 构建计数语句
        count_stmt = select(func.count(Media.id)).where(*where_conditions)

        # 验证分页参数
        page, size = offset_paginator.validate_pagination_params(page, size)

        # 获取总数
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar()

        if total_count == 0:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="media.common.mediaNotFound", lang=language),
            )

        # 应用排序和分页
        base_stmt = base_stmt.order_by(
            Media.created_at.desc(), Media.id.desc())
        base_stmt = offset_paginator.apply_pagination(base_stmt, page, size)

        # 执行查询
        result = await self.db.execute(base_stmt)
        items = result.scalars().all()

        # 创建分页元数据
        pagination_metadata = offset_paginator.create_pagination_metadata(
            total_count, page, size
        )

        # 计算本月新增的数量（基于所有媒体文件，不仅仅是当前页）
        current_month = datetime.now().month
        current_year = datetime.now().year

        # 查询用户所有媒体文件中本月新增的数量
        this_month_count_stmt = (
            select(func.count(Media.id))
            .where(
                Media.user_id == user_id,
                Media.is_avatar == False,
                Media.is_content_audio == False,
                func.extract('year', Media.created_at) == current_year,
                func.extract('month', Media.created_at) == current_month,
            )
        )

        # 只有当media_type不为None时才添加类型过滤条件
        if media_type is not None:
            this_month_count_stmt = this_month_count_stmt.where(
                Media.type == media_type)

        this_month_count_result = await self.db.execute(this_month_count_stmt)
        this_month_count = this_month_count_result.scalar() or 0

        pagination_metadata["new_items_this_month"] = this_month_count

        # 格式化响应数据（返回原始数据，预签名 URL 在 service 层处理）
        response_items: List[Dict[str, Any]] = []
        for media in items:
            item_data = {
                "media_id": media.id,
                "media_uuid": media.uuid,
                "media_type": media.type.name,
                "file_name": media.file_name,
                "original_filepath_url": media.original_filepath_url,
                "thumbnail_filepath_url": media.thumbnail_filepath_url
                if media.thumbnail_filepath_url
                else None,
                "watermark_filepath_url": media.watermark_filepath_url
                if media.watermark_filepath_url
                else None,
                "file_size": media.file_size,
                "created_at": media.created_at.isoformat()
                if media.created_at
                else None,
            }

            response_items.append(item_data)

        # 缓存结果
        cache_data = offset_paginator.create_response_data(
            response_items, pagination_metadata
        )
        await redis_manager.set_async(cache_key, json.dumps(cache_data))

        return response_items, pagination_metadata

    async def upload_media_to_s3(
        self,
        uuid: str,
        user_id: int,
        type: MediaType,
        is_avatar: bool,
        file_name: str,
        language: Language,
        original_filepath_url: str,
        thumbnail_filepath_url: Optional[str] = None,
        watermark_filepath_url: Optional[str] = None,
        file_size: int = 0,
    ) -> bool:
        if not original_filepath_url:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="media.common.mediaNotFound", lang=language),
            )

        if is_avatar == True:
            # 删除掉旧的avatar
            await self.db.execute(
                delete(Media).where(
                    Media.user_id == user_id,
                    Media.is_avatar == True,
                )
            )

        await self.db.execute(
            insert(Media).values(
                uuid=uuid,
                user_id=user_id,
                type=type,
                is_avatar=is_avatar,
                file_name=file_name,
                original_filepath_url=original_filepath_url,
                thumbnail_filepath_url=thumbnail_filepath_url,
                watermark_filepath_url=watermark_filepath_url,
                file_size=file_size,
            )
        )
        await self.db.commit()

        # 更新缓存
        cache_key = f"media_lists:{user_id}:*"
        await redis_manager.delete_pattern_async(cache_key)

        return True

    async def delete_media_from_s3(
        self, media_id: int, user_id: int, language: Language
    ):
        """
        删除媒体文件记录
        简化参数，只使用media_id和user_id
        """
        # 检查是否存在
        media = await self.get_media(media_id=media_id, user_id=user_id)
        if not media:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="media.common.mediaNotFound", lang=language),
            )

        # 删除数据库中的记录
        await self.db.delete(media)
        await self.db.commit()

        # 更新缓存
        cache_key = f"media_lists:{user_id}:*"
        await redis_manager.delete_pattern_async(cache_key)

        return True

    async def download_media_from_s3(
        self, media_id: int, language: Language
    ):
        """
        获取媒体文件下载URL
        简化参数，只使用media_id
        """
        media = await self.get_media(media_id=media_id)
        self.logger.info(f"media_id: {media_id}, media: {media}")
        if not media:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="media.common.mediaNotFound", lang=language),
            )

        # 原文件url
        original_filepath_url = media.original_filepath_url

        return original_filepath_url


def get_media_crud(db: AsyncSession = Depends(mysql_manager.get_db)) -> MediaCrud:
    return MediaCrud(db)
