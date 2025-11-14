from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime
from sqlmodel import (
    Column,
    Field,
    Index,
    SQLModel,
    desc,
)


class Tag(SQLModel, table=True):
    """标签表 - 存储博客标签信息"""

    __tablename__ = "tags"

    __table_args__ = (
        # 单列索引
        Index("idx_tags_id", "id"),
        Index("idx_tags_slug", "slug"),
        # 排序索引
        Index("idx_tags_created_at_desc", desc("created_at")),
        Index("idx_tags_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    chinese_title: str = Field(nullable=False, max_length=50, unique=True)  # 优化长度
    english_title: str = Field(nullable=False, max_length=50)  # 优化长度
    slug: str = Field(nullable=False, max_length=50, unique=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=None, onupdate=datetime.now(timezone.utc)
        )
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, chinese_title={self.chinese_title}, english_title={self.english_title})>"
