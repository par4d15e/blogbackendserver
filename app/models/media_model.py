from enum import IntEnum
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import text, ForeignKey
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
    from app.models.user_model import User
    from app.models.blog_model import Blog
    from app.models.project_model import Project, Project_Attachment


class MediaType(IntEnum):
    image = 1
    video = 2
    audio = 3
    document = 4
    other = 5


class Media(SQLModel, table=True):
    """媒体文件表 - 存储用户上传的媒体文件信息"""

    __tablename__ = "media"

    __table_args__ = (
        # 单列索引
        Index("idx_media_id", "id"),
        Index("idx_media_uuid", "uuid"),
        Index("idx_media_user_id", "user_id"),
        Index("idx_media_type", "type"),
        Index("idx_media_is_avatar", "is_avatar"),
        # 复合索引
        Index("idx_media_id_uuid_user", "id", "uuid", "user_id"),
        # 排序索引
        Index("idx_media_created_at_desc", desc("created_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(nullable=False, max_length=36, unique=True)
    user_id: int = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    type: MediaType = Field(nullable=False)
    is_avatar: bool = Field(
        nullable=False, default=False, description="是否作为用户头像使用"
    )  # 标记是否为用户头像
    is_content_audio: bool = Field(
        nullable=False, default=False, description="是否作为内容音频使用"
    )  # 标记是否作为内容音频使用
    file_name: str = Field(nullable=False, max_length=200)  # 优化长度
    original_filepath_url: str = Field(nullable=False, max_length=500)  # 优化长度
    thumbnail_filepath_url: Optional[str] = Field(
        default=None, max_length=500
    )  # 优化长度
    watermark_filepath_url: Optional[str] = Field(
        default=None, max_length=500
    )  # 优化长度
    file_size: int = Field(nullable=False, default=0)
    created_at: datetime = Field(
        nullable=False,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    # 关系字段定义
    # 多对一关系：每个媒体文件属于特定用户
    user: "User" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "medias",
            "uselist": False,
            "lazy": "joined",
        }
    )

    # 一对多关系：一个媒体文件可以作为多个博客的封面
    cover_for_blog: List["Blog"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "cover",
            "uselist": True,
            "lazy": "select",
        }
    )

    # 一对多关系：一个媒体文件可以作为多个项目的封面
    cover_for_project: List["Project"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "cover",
            "uselist": True,
            "lazy": "select",
        }
    )

    # 一对多关系：一个媒体文件可以作为多个项目的附件
    project_attachments: List["Project_Attachment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "attachment",
            "uselist": True,
            "lazy": "select",
        }
    )

    def __repr__(self):
        return f"<Media(id={self.id}, uuid={self.uuid}, file_name={self.file_name}, type={self.type.name}, user_id={self.user_id})>"
