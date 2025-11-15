from enum import IntEnum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from sqlalchemy import text, JSON, ForeignKey
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlmodel import (
    Index,
    Column,
    Field,
    Relationship,
    SQLModel,
)

if TYPE_CHECKING:
    from app.models.section_model import Section
    from app.models.seo_model import Seo
    from app.models.media_model import Media
    from app.models.payment_model import Payment_Record, Tax


class ProjectType(IntEnum):
    """项目类型枚举"""

    web = 1
    mobile = 2
    desktop = 3
    other = 4


class Project(SQLModel, table=True):
    """项目模型"""

    __tablename__ = "projects"
    __table_args__ = (
        # 单列索引
        Index("idx_projects_id", "id"),
        Index("idx_projects_type", "type"),
        Index("idx_projects_seo_id", "seo_id"),
        Index("idx_projects_chinese_title", "chinese_title"),
        Index("idx_projects_is_published", "is_published"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    type: ProjectType = Field(nullable=False, default=ProjectType.web)
    section_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey(
            "sections.id", ondelete="SET NULL"), nullable=True),
    )
    seo_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("seo.id", ondelete="SET NULL"), nullable=True
        ),
    )
    cover_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey(
            "media.id", ondelete="SET NULL"), nullable=True),
    )
    is_published: bool = Field(nullable=False)
    chinese_title: str = Field(max_length=200, nullable=True, unique=True)
    english_title: Optional[str] = Field(
        default=None, max_length=200, nullable=True)
    slug: str = Field(max_length=300, nullable=False, unique=True)
    chinese_description: str = Field(max_length=300, nullable=False)
    english_description: Optional[str] = Field(
        default=None, max_length=300, nullable=True
    )
    chinese_content: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False))
    english_content: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
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
    section: "Section" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "project",
            "uselist": False,
            "lazy": "joined",  # 项目列表经常需要显示栏目信息
        }
    )
    seo: Optional["Seo"] = Relationship(
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "joined",  # 项目列表经常需要显示SEO信息
        }
    )
    cover: Optional["Media"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "cover_for_project",
            "uselist": False,
            "lazy": "joined",  # 项目列表经常需要显示封面信息
        }
    )
    project_attachments: "Project_Attachment" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "project",
            "uselist": False,
            "lazy": "joined",  # 项目附件经常需要显示项目信息
        }
    )
    project_monetization: "Project_Monetization" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "project",
            "uselist": False,
            "lazy": "joined",  # 项目变现经常需要显示项目信息
        }
    )
    payment_records: List["Payment_Record"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "project",
            "uselist": True,
            "lazy": "select",  # 项目支付记录经常需要显示项目信息
        }
    )


class Project_Attachment(SQLModel, table=True):
    """项目附件模型"""

    __tablename__ = "project_attachments"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(ForeignKey(
            "projects.id", ondelete="CASCADE"), nullable=False)
    )
    attachment_id: int = Field(
        sa_column=Column(ForeignKey(
            "media.id", ondelete="CASCADE"), nullable=False)
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

    # 关系字段定义
    project: "Project" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "project_attachments",
            "uselist": False,
            "lazy": "joined",  # 项目附件经常需要显示项目信息
        }
    )
    attachment: "Media" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "project_attachments",
            "uselist": False,
            "lazy": "joined",  # 项目附件经常需要显示附件信息
        }
    )


class Project_Monetization(SQLModel, table=True):
    """项目 monetization 模型"""

    __tablename__ = "project_monetizations"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(ForeignKey(
            "projects.id", ondelete="CASCADE"), nullable=False)
    )
    tax_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey(
            "taxes.id", ondelete="SET NULL"), nullable=True),
    )
    price: float = Field(nullable=False, default=0.0)
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
    project: "Project" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "project_monetization",
            "uselist": False,
            "lazy": "joined",  # 项目变现经常需要显示项目信息
        }
    )

    tax: "Tax" = Relationship(
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "joined",  # 项目变现经常需要显示税费信息
        }
    )
