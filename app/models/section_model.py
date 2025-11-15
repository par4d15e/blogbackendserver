from enum import IntEnum
from datetime import datetime, timezone

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import text
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlmodel import (
    Column,
    Field,
    Index,
    Relationship,
    SQLModel,
    desc,
)

# 解决循环导入
if TYPE_CHECKING:
    from app.models.seo_model import Seo
    from app.models.board_model import Board
    from app.models.friend_model import Friend
    from app.models.blog_model import Blog
    from app.models.project_model import Project


class SectionType(IntEnum):
    blog = 1
    project = 2
    board = 3
    friend = 4
    about = 5


class Section(SQLModel, table=True):
    """栏目表 - 存储网站栏目信息"""

    __tablename__ = "sections"

    __table_args__ = (
        # 单列索引
        Index("idx_sections_id", "id"),
        Index("idx_sections_seo_id", "seo_id"),
        Index("idx_sections_type", "type"),
        Index("idx_sections_slug", "slug"),
        Index("idx_sections_is_active", "is_active"),
        Index("idx_sections_parent_id", "parent_id"),
        Index("idx_sections_chinese_title", "chinese_title"),
        # 复合索引
        Index("idx_sections_parent_active", "parent_id", "is_active"),
        Index("idx_sections_type_active", "type", "is_active"),
        # 排序索引
        Index("idx_sections_created_at_desc", desc("created_at")),
        Index("idx_sections_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    seo_id: Optional[int] = Field(
        default=None, ondelete="SET NULL", foreign_key="seo.id"
    )
    type: SectionType = Field(nullable=False)
    slug: str = Field(nullable=False, max_length=100, unique=True)  # 优化长度
    chinese_title: str = Field(
        nullable=False, max_length=100, unique=True)  # 优化长度
    english_title: Optional[str] = Field(default=None, max_length=100)  # 优化长度
    chinese_description: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    english_description: Optional[str] = Field(
        default=None, max_length=200)  # 优化长度
    is_active: bool = Field(default=True, nullable=False)
    parent_id: Optional[int] = Field(default=None, foreign_key="sections.id")
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

    # 关系字段定义
    # 1. 一对一关系：栏目的SEO设置
    seo: Optional["Seo"] = Relationship(
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "joined",  # 栏目信息经常需要SEO数据
        }
    )

    # 2. 自引用关系：栏目的层级结构
    parent: Optional["Section"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "children",
            "uselist": False,
            "lazy": "joined",  # 栏目层级关系经常需要显示
            "remote_side": "Section.id",  # 明确指定远程端
        }
    )

    children: List["Section"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "parent",
            "uselist": True,
            "lazy": "select",  # 子栏目按需加载
            "cascade": "all, delete-orphan",  # 删除父栏目时删除子栏目
        }
    )

    # 3. 一对多关系：栏目下的内容
    blogs: List["Blog"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "section",
            "uselist": True,
            "lazy": "select",  # 栏目的博客按需加载
            "cascade": "save-update",  # 保留博客数据
        }
    )

    boards: List["Board"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "section",
            "uselist": True,
            "lazy": "select",  # 留言板按需加载
            "cascade": "save-update",  # 保留留言板数据
        }
    )

    # 4. 一对一关系：友链（每个栏目只能有一个友链）
    friend: Optional["Friend"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "section",
            "uselist": False,
            "lazy": "select",  # 友链信息按需加载
        }
    )
    # 5. 一对一关系：项目（每个栏目只能有一个项目）
    project: Optional["Project"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "section",
            "uselist": False,
            "lazy": "select",  # 项目信息按需加载
        }
    )

    def __repr__(self):
        return f"<Section(id={self.id}, chinese_name={self.chinese_title}, type={self.type.name}, slug={self.slug})>"
