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


class Seo(SQLModel, table=True):
    """SEO表 - 存储SEO相关信息"""

    __tablename__ = "seo"

    __table_args__ = (
        # 单列索引
        Index("idx_seo_id", "id"),
        Index("idx_seo_chinese_title", "chinese_title"),
        # 排序索引
        Index("idx_seo_created_at_desc", desc("created_at")),
        Index("idx_seo_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    chinese_title: str = Field(
        nullable=False, max_length=100, unique=True)  # 优化长度
    english_title: Optional[str] = Field(default=None, max_length=100)  # 优化长度
    chinese_description: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    english_description: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    chinese_keywords: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    english_keywords: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
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
        return f"<Seo(id={self.id}, chinese_name={self.chinese_name}, english_name={self.english_name}, user_id={self.user_id})>"
