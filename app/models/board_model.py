from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import DateTime, ForeignKey
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
    from app.models.section_model import Section
    from app.models.user_model import User


class Board(SQLModel, table=True):
    """留言板表 - 存储留言板信息"""

    __tablename__ = "boards"

    __table_args__ = (
        # 单列索引
        Index("idx_boards_id", "id"),
        Index("idx_boards_section_id", "section_id"),
        Index("idx_boards_chinese_title", "chinese_title"),
        # 复合索引
        # 排序索引
        Index("idx_boards_created_at_desc", desc("created_at")),
        Index("idx_boards_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    section_id: int = Field(
        sa_column=Column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    )
    chinese_title: str = Field(nullable=False, max_length=100, unique=True)  # 优化长度
    english_title: Optional[str] = Field(default=None, max_length=100)  # 优化长度
    chinese_description: Optional[str] = Field(default=None, max_length=200)  # 优化长度
    english_description: Optional[str] = Field(default=None, max_length=200)  # 优化长度
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

    # 关系字段 - 多对一：一个Board属于一个Section和Seo
    section: "Section" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "boards",  # 对应Section模型中的boards字段
            "uselist": False,  # 一个Board只能对应一个Section
            "lazy": "joined",  # 使用joined加载，适合一对一关系
        }
    )

    # 关系字段 - 一对多：一个Board可以有多个Board_Comment
    board_comments: List["Board_Comment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "board",  # 对应Board_Comment模型中的board字段
            "uselist": True,  # 一个Board可以对应多个Board_Comment
            "lazy": "select",  # 使用selectin加载，适合一对多关系
        }
    )

    def __repr__(self):
        return f"<Board(id={self.id}, chinese_title={self.chinese_title}, english_title={self.english_title}, section_id={self.section_id})>"


class Board_Comment(SQLModel, table=True):
    """留言板评论表 - 存储留言板的评论信息"""

    __tablename__ = "board_comments"

    __table_args__ = (
        # 单列索引
        Index("idx_board_comments_id", "id"),
        Index("idx_board_comments_board_id", "board_id"),
        Index("idx_board_comments_user_id", "user_id"),
        Index("idx_board_comments_parent_id", "parent_id"),
        Index("idx_board_comments_is_deleted", "is_deleted"),
        # 复合索引
        Index("idx_board_comments_board_id_user_id", "board_id", "user_id"),
        Index("idx_board_comments_board_created", "board_id", "created_at"),
        # 排序索引
        Index("idx_board_comments_created_at_desc", desc("created_at")),
        Index("idx_board_comments_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    board_id: int = Field(
        sa_column=Column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    )
    user_id: int = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    parent_id: Optional[int] = Field(
        sa_column=Column(
            ForeignKey("board_comments.id", ondelete="CASCADE"), nullable=True
        )
    )
    is_deleted: bool = Field(default=False)
    comment: str = Field(nullable=False, max_length=500)  # 优化长度
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

    # 关系字段 - 多对一：一个Board_Comment属于一个Board和User
    board: "Board" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "board_comments",  # 对应Board模型中的board_comments字段
            "uselist": False,  # 一个Board_Comment只能对应一个Board
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    user: "User" = Relationship(
        sa_relationship_kwargs={
            "uselist": False,  # 一个Board_Comment只能对应一个User
            "lazy": "joined",  # 使用joined加载，适合多对一关系
        }
    )

    parent: Optional["Board_Comment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "children",  # 对应Board_Comment模型中的children字段
            "uselist": False,  # 一个Board_Comment只能对应一个Board_Comment
            "lazy": "joined",  # 使用joined加载，适合多对一关系
            "remote_side": "Board_Comment.id",
        }
    )

    children: List["Board_Comment"] = Relationship(
        sa_relationship_kwargs={
            "back_populates": "parent",  # 对应Board_Comment模型中的parent字段
            "uselist": True,  # 一个Board_Comment可以对应多个Board_Comment
            "lazy": "select",  # 子评论按需加载
        }
    )

    def __repr__(self):
        return f"<Board_Comment(id={self.id}, board_id={self.board_id}, user_id={self.user_id}, comment={self.comment})>"
