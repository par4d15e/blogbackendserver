from enum import IntEnum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import text, ForeignKey
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlmodel import (
    Index,
    Column,
    Field,
    Relationship,
    SQLModel,
    desc,
)

# 解决循环导入
if TYPE_CHECKING:
    from app.models.section_model import Section


class FriendType(IntEnum):
    featured = 1
    normal = 2
    hidden = 3


class Friend(SQLModel, table=True):
    """友链表 - 存储友链信息"""

    __tablename__ = "friends"

    __table_args__ = (
        # 单列索引
        Index("idx_friends_id", "id"),
        Index("idx_friends_section_id", "section_id"),
        Index("idx_friends_chinese_title", "chinese_title"),
        # 复合索引
        # 排序索引
        Index("idx_friends_created_at_desc", desc("created_at")),
        Index("idx_friends_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    section_id: int = Field(
        sa_column=Column(ForeignKey(
            "sections.id", ondelete="CASCADE"), nullable=False)
    )
    chinese_title: str = Field(
        nullable=False, max_length=100, unique=True)  # 优化长度
    english_title: Optional[str] = Field(default=None, max_length=100)  # 优化长度
    chinese_description: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    english_description: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    created_at: datetime = Field(
        nullable=False,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        nullable=True,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"server_default": text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")},
    )

    # 关系字段定义
    # 1. 多对一关系：友链属于特定栏目
    section: "Section" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "friend",
            "uselist": False,
            "lazy": "joined",  # 友链信息经常需要栏目数据
        }
    )

    # 2. 一对多关系：友链列表项
    friend_list: List["Friend_List"] = Relationship(
        sa_relationship_kwargs={
            "uselist": True,
            "lazy": "select",  # 友链列表按需加载
        }
    )

    def __repr__(self):
        return f"<Friend(id={self.id}, chinese_title={self.chinese_title}, english_title={self.english_title}, section_id={self.section_id})>"


class Friend_List(SQLModel, table=True):
    """友链列表表 - 存储具体的友链信息"""

    __tablename__ = "friend_lists"

    __table_args__ = (
        # 单列索引
        Index("idx_friend_lists_id", "id"),
        Index("idx_friend_lists_friend_id", "friend_id"),
        Index("idx_friend_lists_user_id", "user_id"),
        Index("idx_friend_lists_type", "type"),
        # 复合索引
        # 排序索引
        Index("idx_friend_lists_created_at_desc", desc("created_at")),
        Index("idx_friend_lists_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    friend_id: int = Field(
        sa_column=Column(ForeignKey(
            "friends.id", ondelete="CASCADE"), nullable=False)
    )
    user_id: int = Field(
        sa_column=Column(ForeignKey(
            "users.id", ondelete="CASCADE"), nullable=False)
    )
    type: FriendType = Field(nullable=False, default=FriendType.hidden)
    logo_url: str = Field(nullable=False, max_length=500)  # 优化长度
    site_url: str = Field(nullable=False, max_length=500)  # 优化长度
    chinese_title: str = Field(nullable=False, max_length=100)  # 优化长度
    english_title: Optional[str] = Field(default=None, max_length=100)  # 优化长度
    chinese_description: str = Field(nullable=False, max_length=200)  # 优化长度
    english_description: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    created_at: datetime = Field(
        nullable=False,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        nullable=True,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"server_default": text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")},
    )

    def __repr__(self):
        return f"<Friend_List(id={self.id}, friend_id={self.friend_id}, user_id={self.user_id}, chinese_title={self.chinese_title}, type={self.type.name})>"
