from enum import IntEnum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import text
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlmodel import (
    Field,
    Index,
    Relationship,
    SQLModel,
    desc,
)


# 防止循环导入
if TYPE_CHECKING:
    from app.models.media_model import Media
    from app.models.auth_model import Code, RefreshToken, Social_Account
    from app.models.blog_model import Blog, Blog_Status, Blog_Comment, Saved_Blog
    from app.models.payment_model import Payment_Record

# 定义用户角色的枚举类型


class RoleType(IntEnum):
    user = 1
    admin = 2


class User(SQLModel, table=True):
    """用户表 - 存储系统用户的基本信息"""

    __tablename__ = "users"

    __table_args__ = (
        # 核心查询索引
        Index("idx_users_id", "id"),
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        # 复合业务索引
        Index(
            "idx_users_get_user_by_email",
            "email",
            "is_active",
            "is_verified",
            "is_deleted",
        ),  # auth_crud.py: get_user_by_email
        Index(
            "idx_users_get_user_by_id", "id", "is_active", "is_verified", "is_deleted"
        ),  # auth_crud.py: get_user_by_id
        Index(
            "idx_users_get_user_by_username", "username", "is_active", "is_verified"
        ),  # auth_crud.py: get_user_by_username
        # 时间排序索引
        Index("idx_users_created_at_desc", desc("created_at")),
        Index("idx_users_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    username: Optional[str] = Field(
        nullable=True, max_length=30, unique=True
    )  # 优化长度
    email: str = Field(nullable=False, max_length=100, unique=True)  # 优化长度
    password_hash: Optional[str] = Field(max_length=255)
    role: RoleType = Field(nullable=False, default=RoleType.user)
    bio: Optional[str] = Field(
        default="这个人很懒，什么都没有留下。", max_length=300
    )  # 优化长度
    ip_address: Optional[str] = Field(default=None, max_length=45)
    longitude: Optional[float] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    city: Optional[str] = Field(default=None, max_length=50)  # 优化长度
    is_active: bool = Field(default=False, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    is_deleted: bool = Field(default=False, nullable=False)
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
    # 1. 一对一关系：用户头像
    avatar: Optional["Media"] = Relationship(
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "select",
            "primaryjoin": "and_(User.id==Media.user_id, Media.is_avatar==True)",
            "viewonly": True,
        }
    )

    # 2. 一对多关系：用户创建的内容（可以级联删除）
    medias: List["Media"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "user",
            "uselist": True,
            "lazy": "select",
        }
    )

    refresh_tokens: List["RefreshToken"] = Relationship(
        sa_relationship_kwargs={
            "uselist": True,
            "lazy": "select",
        }
    )

    codes: List["Code"] = Relationship(
        sa_relationship_kwargs={
            "uselist": True,
            "lazy": "select",
        }
    )

    social_accounts: List["Social_Account"] = Relationship(
        sa_relationship_kwargs={
            "uselist": True,
            "lazy": "select",
        }
    )

    # 3. 一对多关系：重要业务数据（不应级联删除，支持软删除）
    blogs: List["Blog"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "user",
            "uselist": True,
            "lazy": "select",
        }
    )

    blog_status: List["Blog_Status"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "user",
            "uselist": True,
            "lazy": "select",
        }
    )

    blog_comments: List["Blog_Comment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "user",
            "uselist": True,
            "lazy": "select",
        }
    )

    saved_blogs: List["Saved_Blog"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "user",
            "uselist": True,
            "lazy": "select",
        }
    )

    # 4. 重要业务关系：绝对不能级联删除
    payment_records: List["Payment_Record"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "user",
            "uselist": True,
            "lazy": "select",
        }
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role.name}, is_active={self.is_active})>"
