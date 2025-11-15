from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import text
from sqlalchemy.dialects.mysql import TIMESTAMP
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
    chinese_title: str = Field(
        nullable=False, max_length=50, unique=True)  # 优化长度
    english_title: str = Field(nullable=False, max_length=50)  # 优化长度
    slug: str = Field(nullable=False, max_length=50, unique=True)
    created_at: datetime = Field(
        nullable=False,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"onupdate": text("CURRENT_TIMESTAMP")},
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, chinese_title={self.chinese_title}, english_title={self.english_title})>"
