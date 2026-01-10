from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from sqlalchemy import text, JSON, ForeignKey
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlmodel import (
    Index,
    Column,
    Field,
    Relationship,
    SQLModel,
    desc,
)


if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.section_model import Section
    from app.models.seo_model import Seo
    from app.models.media_model import Media
    from app.models.tag_model import Tag


class Blog(SQLModel, table=True):
    """博客表 - 存储博客文章的主要信息"""

    __tablename__ = "blogs"

    __table_args__ = (
        # 单列索引
        Index("idx_blogs_id", "id"),
        Index("idx_blogs_user_id", "user_id"),
        Index("idx_blogs_section_id", "section_id"),
        Index("idx_blogs_seo_id", "seo_id"),
        Index("idx_blogs_slug", "slug"),
        # 排序索引
        Index("idx_users_created_at_desc", desc("created_at")),
        Index("idx_users_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    )
    section_id: int = Field(
        sa_column=Column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    )
    seo_id: Optional[int] = Field(
        sa_column=Column(ForeignKey("seo.id", ondelete="SET NULL"), nullable=True)
    )
    cover_id: Optional[int] = Field(
        sa_column=Column(ForeignKey("media.id", ondelete="SET NULL"), nullable=True)
    )
    slug: Optional[str] = Field(max_length=255, nullable=True, unique=True)
    chinese_title: str = Field(nullable=False, max_length=200)  # 优化长度
    english_title: Optional[str] = Field(default=None, max_length=200)  # 优化长度
    chinese_description: Optional[str] = Field(default=None, max_length=500)
    english_description: Optional[str] = Field(default=None, max_length=500)
    chinese_content: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    english_content: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
    content_hash: Optional[str] = Field(
        max_length=64, default=None
    )  # 博客内容hash值，用于判断博客内容是否发生变化
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
    # 1. 多对一关系：每个博客属于特定的用户、栏目和SEO设置
    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blogs",
            "uselist": False,
            "lazy": "joined",  # 博客列表经常需要显示作者信息
        }
    )

    section: "Section" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blogs",
            "uselist": False,
            "lazy": "joined",  # 博客列表经常需要显示栏目信息
        }
    )

    seo: Optional["Seo"] = Relationship(
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "joined",  # SEO信息经常一起查询
        }
    )

    cover: Optional["Media"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "cover_for_blog",
            "uselist": False,
            "lazy": "joined",  # 封面经常一起查询
        }
    )

    # 2. 一对一关系：博客的扩展信息
    blog_status: "Blog_Status" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog",
            "uselist": False,
            "lazy": "joined",  # 博客状态经常需要检查
        }
    )

    blog_stats: "Blog_Stats" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog",
            "uselist": False,
            "lazy": "select",  # 统计信息按需加载
        }
    )

    blog_summary: "Blog_Summary" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog",
            "uselist": False,
            "lazy": "select",  # 摘要按需加载
        }
    )

    # 3. 一对多关系：博客的关联数据
    blog_tags: List["Blog_Tag"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog",
            "uselist": True,
            "lazy": "selectin",  # 批量加载标签，避免N+1查询
        }
    )

    blog_tts: List["Blog_TTS"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog",
            "uselist": True,
            "lazy": "select",  # TTS文件按需加载
        }
    )

    blog_comments: List["Blog_Comment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog",
            "uselist": True,
            "lazy": "select",  # 评论按需加载
        }
    )

    saved_blogs: List["Saved_Blog"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog",
            "uselist": True,
            "lazy": "select",  # 收藏记录按需加载
        }
    )

    def __repr__(self):
        return f"<Blog(id={self.id}, chinese_title={self.chinese_title}, user_id={self.user_id}, section_id={self.section_id})>"


class Blog_Status(SQLModel, table=True):
    """博客状态表 - 存储博客的发布状态信息"""

    __tablename__ = "blog_status"

    __table_args__ = (
        # 单列索引
        Index("idx_blog_status_id", "id"),
        Index("idx_blog_status_user_id", "user_id"),
        Index("idx_blog_status_blog_id", "blog_id"),
        Index("idx_blog_status_is_published", "is_published"),
        Index("idx_blog_status_is_archived", "is_archived"),
        Index("idx_blog_status_is_featured", "is_featured"),
        # 复合索引
        # 排序索引
        Index("idx_blog_status_created_at_desc", desc("created_at")),
        Index("idx_blog_status_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    )
    blog_id: int = Field(
        sa_column=Column(
            ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, unique=True
        )
    )
    is_published: bool = Field(nullable=False)
    is_archived: bool = Field(nullable=False)
    is_featured: bool = Field(nullable=False)
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

    # 关系字段 - 多对一：一个Blog_Status属于一个Blog和User
    blog: "Blog" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_status",  # 对应Blog模型中的blog_status字段
            "uselist": False,  # 一个Blog_Status只能对应一个Blog
            "lazy": "joined",  # 使用joined加载，适合一对一关系
        }
    )

    user: "User" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_status",  # 对应User模型中的blog_status字段
            "uselist": False,  # 一个Blog_Status只能对应一个User
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    def __repr__(self):
        return f"<Blog_status(id={self.id}, user_id={self.user_id}, blog_id={self.blog_id}, is_active={self.is_active}, is_published={self.is_published}, is_deleted={self.is_deleted}, is_archived={self.is_archived}, is_featured={self.is_featured})>"


class Blog_Stats(SQLModel, table=True):
    """博客统计表 - 存储博客的统计数据"""

    __tablename__ = "blog_stats"

    __table_args__ = (
        Index("idx_blog_stats_id", "id"),
        Index("idx_blog_stats_blog_id", "blog_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    blog_id: int = Field(
        sa_column=Column(
            ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, unique=True
        )
    )
    views: int = Field(nullable=False, default=0)
    likes: int = Field(nullable=False, default=0)
    comments: int = Field(nullable=False, default=0)
    saves: int = Field(nullable=False, default=0)

    # 关系字段 - 一对一：一个Blog_Stats对应一个Blog
    blog: "Blog" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_stats",  # 对应Blog模型中的blog_stats字段
            "uselist": False,  # 一个Blog_Stats只能对应一个Blog
            "lazy": "joined",  # 使用joined加载，适合一对一关系
        }
    )

    def __repr__(self):
        return f"<Blog_Stats(id={self.id}, blog_id={self.blog_id}, views={self.views}, likes={self.likes}, comments={self.comments}, saves={self.saves})>"


class Blog_Comment(SQLModel, table=True):
    """博客评论表 - 存储博客的评论信息"""

    __tablename__ = "blog_comment"

    __table_args__ = (
        # 单列索引
        Index("idx_blog_comment_id", "id"),
        Index("idx_blog_comment_blog_id", "blog_id"),
        Index("idx_blog_comment_user_id", "user_id"),
        Index("idx_blog_comment_parent_id", "parent_id"),
        Index("idx_blog_comment_is_deleted", "is_deleted"),
        # 复合索引
        # 排序索引
        Index("idx_blog_comment_created_at_desc", desc("created_at")),
        Index("idx_blog_comment_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    blog_id: int = Field(
        sa_column=Column(ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False)
    )
    user_id: int = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    comment: str = Field(nullable=False, max_length=255)
    is_deleted: bool = Field(default=False, nullable=False)
    parent_id: Optional[int] = Field(default=None, foreign_key="blog_comment.id")
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

    # 关系字段 - 多对一：一个Blog_Comment属于一个Blog和User
    blog: "Blog" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_comments",  # 对应Blog模型中的blog_comments字段
            "uselist": False,  # 一个Blog_Comment只能对应一个Blog
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    user: "User" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_comments",  # 对应User模型中的blog_comments字段
            "uselist": False,  # 一个Blog_Comment只能对应一个User
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    # 自引用关系：评论的父子关系
    parent: Optional["Blog_Comment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "children",  # 对应Blog_Comment模型中的children字段
            "uselist": False,  # 一个Blog_Comment只能有一个父评论
            "lazy": "joined",  # 使用joined加载，适合多对一关系
            "remote_side": "Blog_Comment.id",  # 指定远程端
        }
    )

    children: List["Blog_Comment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "parent",  # 对应Blog_Comment模型中的parent字段
            "uselist": True,  # 一个Blog_Comment可以有多个子评论
            "lazy": "select",  # 使用selectin加载，适合一对多关系
        }
    )

    def __repr__(self):
        return f"<Blog_comment(id={self.id}, blog_id={self.blog_id}, user_id={self.user_id}, comment={self.comment}, is_deleted={self.is_deleted}, parent_id={self.parent_id})>"


class Saved_Blog(SQLModel, table=True):
    """收藏博客表 - 存储用户收藏的博客信息"""

    __tablename__ = "saved_blog"

    __table_args__ = (
        # 单列索引
        Index("idx_saved_blog_id", "id"),
        Index("idx_saved_blog_user_id", "user_id"),
        Index("idx_saved_blog_blog_id", "blog_id"),
        # 复合索引
        Index("idx_saved_blog_user_id_blog_id", "user_id", "blog_id"),
        # 排序索引
        Index("idx_saved_blog_created_at_desc", desc("created_at")),
        Index("idx_saved_blog_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    blog_id: int = Field(
        sa_column=Column(ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False)
    )
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

    # 关系字段 - 多对一：一个Saved_Blog属于一个Blog和User
    blog: "Blog" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "saved_blogs",  # 对应Blog模型中的saved_blogs字段
            "uselist": False,  # 一个Saved_Blog只能对应一个Blog
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    user: "User" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "saved_blogs",  # 对应User模型中的saved_blogs字段
            "uselist": False,  # 一个Saved_Blog只能对应一个User
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    def __repr__(self):
        return f"<Saved_Blog(id={self.id}, user_id={self.user_id}, blog_id={self.blog_id})>"


class Blog_Tag(SQLModel, table=True):
    """博客标签关联表 - 存储博客和标签的多对多关系"""

    __tablename__ = "blog_tag"

    __table_args__ = (
        # 单列索引
        Index("idx_blog_tag_id", "id"),
        Index("idx_blog_tag_blog_id", "blog_id"),
        Index("idx_blog_tag_tag_id", "tag_id"),
        # 复合索引
        Index("idx_blog_tag_blog_id_tag_id", "blog_id", "tag_id"),
        # 排序索引
        Index("idx_blog_tag_created_at_desc", desc("created_at")),
        Index("idx_blog_tag_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    blog_id: int = Field(
        sa_column=Column(ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False)
    )
    tag_id: int = Field(
        sa_column=Column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    )
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

    # 关系字段 - 多对一：一个Blog_Tag属于一个Blog和Tag
    blog: "Blog" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_tags",  # 对应Blog模型中的blog_tags字段
            "uselist": False,  # 一个Blog_Tag只能对应一个Blog
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    tag: "Tag" = Relationship(
        sa_relationship_kwargs={
            "uselist": False,  # 一个Blog_Tag只能对应一个Tag
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    def __repr__(self):
        return f"<Blog_Tag(id={self.id}, blog_id={self.blog_id}, tag_id={self.tag_id})>"


class Blog_Summary(SQLModel, table=True):
    """博客摘要表 - 存储博客的摘要信息"""

    __tablename__ = "blog_summary"

    __table_args__ = (
        # 单列索引
        Index("idx_blog_summary_id", "id"),
        Index("idx_blog_summary_blog_id", "blog_id"),
        # 复合索引
        # 排序索引
        Index("idx_blog_summary_created_at_desc", desc("created_at")),
        Index("idx_blog_summary_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    blog_id: int = Field(
        sa_column=Column(
            ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, unique=True
        )
    )
    chinese_summary: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    english_summary: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
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

    # 关系字段 - 一对一：一个Blog_Summary对应一个Blog
    blog: "Blog" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_summary",  # 对应Blog模型中的blog_summary字段
            "uselist": False,  # 一个Blog_Summary只能对应一个Blog
            "lazy": "joined",  # 使用joined加载，适合一对一关系
        }
    )

    def __repr__(self):
        return f"<Blog_summary(id={self.id}, blog_id={self.blog_id}, summary={self.summary})>"


class Blog_TTS(SQLModel, table=True):
    """博客TTS表 - 存储博客的文本转语音信息"""

    __tablename__ = "blog_tts"

    __table_args__ = (
        # 单列索引
        Index("idx_blog_tts_id", "id"),
        Index("idx_blog_tts_blog_id", "blog_id"),
        Index("idx_blog_tts_chinese_tts_id", "chinese_tts_id"),
        Index("idx_blog_tts_english_tts_id", "english_tts_id"),
        # 复合索引 - 优化查询性能
        Index("idx_blog_tts_blog_id_chinese_tts_id", "blog_id", "chinese_tts_id"),
        Index("idx_blog_tts_blog_id_english_tts_id", "blog_id", "english_tts_id"),
        Index(
            "idx_blog_tts_blog_id_chinese_tts_id_english_tts_id",
            "blog_id",
            "chinese_tts_id",
            "english_tts_id",
        ),
        # 排序索引
        Index("idx_blog_tts_created_at_desc", desc("created_at")),
        Index("idx_blog_tts_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    blog_id: int = Field(
        sa_column=Column(ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False)
    )
    chinese_tts_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("media.id", ondelete="CASCADE"), nullable=True),
    )
    english_tts_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("media.id", ondelete="CASCADE"), nullable=True),
    )
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

    # 关系字段 - 多对一：一个Blog_TTS属于一个Blog
    blog: "Blog" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "blog_tts",  # 对应Blog模型中的blog_tts字段
            "uselist": False,  # 一个Blog_TTS只能对应一个Blog
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    # 关系字段 - 多对一：一个Blog_TTS对应两个Media（中文和英文TTS）
    chinese_tts: "Media" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Blog_TTS.chinese_tts_id]",
            "uselist": False,  # 一个Blog_TTS只能对应一个中文Media
            "lazy": "joined",  # 使用joined加载，适合一对一关系
        }
    )

    english_tts: "Media" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Blog_TTS.english_tts_id]",
            "uselist": False,  # 一个Blog_TTS只能对应一个英文Media
            "lazy": "joined",  # 使用joined加载，适合一对一关系
        }
    )

    def __repr__(self):
        return f"<Blog_TTS(id={self.id}, blog_id={self.blog_id}, chinese_tts_id={self.chinese_tts_id}, english_tts_id={self.english_tts_id})>"
