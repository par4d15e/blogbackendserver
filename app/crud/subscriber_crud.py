from fastapi import Depends, HTTPException
from sqlmodel import select, update
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any, Tuple
from app.models.subscriber_model import Subscriber
from app.core.database.mysql import mysql_manager
from app.core.logger import logger_manager
from app.utils.offset_pagination import offset_paginator


class SubscriberCrud:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger_manager.get_logger(__name__)

    async def get_subscriber_by_email(self, email: str) -> Optional[Subscriber]:
        statement = select(Subscriber).where(Subscriber.email == email)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_subscriber_lists(
        self, page: int = 1, size: int = 100
    ) -> Tuple[List[Subscriber], Dict[str, Any]]:
        items, pagination_metadata = await offset_paginator.get_paginated_result(
            self.db, Subscriber, page=page, size=size
        )
        return items, pagination_metadata

    async def create_subscriber(self, email: str) -> Subscriber:
        # 检查是否已存在
        existing_subscriber = await self.get_subscriber_by_email(email)

        if existing_subscriber:
            if existing_subscriber.is_active:
                raise HTTPException(
                    status_code=400, detail="Email is already subscribed."
                )
            else:
                # 如果存在但未激活，重新激活订阅
                # subscribed_at 由数据库自动设置（CURRENT_TIMESTAMP）
                stmt = (
                    update(Subscriber)
                    .where(Subscriber.email == email)
                    .values(
                        is_active=True, subscribed_at=func.now(), unsubscribed_at=None
                    )
                )
                await self.db.execute(stmt)
                await self.db.commit()
                await self.db.refresh(existing_subscriber)
                return existing_subscriber

        # 创建新订阅者
        new_subscriber = Subscriber(email=email)
        self.db.add(new_subscriber)
        await self.db.commit()
        await self.db.refresh(new_subscriber)
        return new_subscriber

    async def ensure_subscriber_active(self, email: str) -> Subscriber:
        """
        确保订阅者存在且激活。如果不存在则创建，如果存在但未激活则重新激活。
        如果已存在且已激活，直接返回。不会抛出异常。
        """
        existing_subscriber = await self.get_subscriber_by_email(email)

        if existing_subscriber:
            if existing_subscriber.is_active:
                # 已存在且已激活，直接返回
                return existing_subscriber
            else:
                # 存在但未激活，重新激活
                # subscribed_at 由数据库自动设置（CURRENT_TIMESTAMP）
                stmt = (
                    update(Subscriber)
                    .where(Subscriber.email == email)
                    .values(
                        is_active=True, subscribed_at=func.now(), unsubscribed_at=None
                    )
                )
                await self.db.execute(stmt)
                await self.db.commit()
                await self.db.refresh(existing_subscriber)
                return existing_subscriber

        # 不存在，创建新订阅者
        new_subscriber = Subscriber(email=email)
        self.db.add(new_subscriber)
        await self.db.commit()
        await self.db.refresh(new_subscriber)
        return new_subscriber

    async def unsubscribe_subscriber(self, email: str) -> Subscriber:
        # 检查是否存在
        existing_subscriber = await self.get_subscriber_by_email(email)

        if not existing_subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found.")

        if not existing_subscriber.is_active:
            raise HTTPException(
                status_code=400, detail="Subscriber is already unsubscribed."
            )

        # 使用数据库的 CURRENT_TIMESTAMP 函数
        stmt = (
            update(Subscriber)
            .where(Subscriber.email == email)
            .values(is_active=False, unsubscribed_at=func.now())
        )
        await self.db.execute(stmt)
        await self.db.commit()
        await self.db.refresh(existing_subscriber)
        return existing_subscriber


def get_subscriber_crud(
    db: AsyncSession = Depends(mysql_manager.get_db),
) -> SubscriberCrud:
    return SubscriberCrud(db)
