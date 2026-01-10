from enum import IntEnum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import text, ForeignKey
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlmodel import (
    Column,
    Field,
    Relationship,
    SQLModel,
    Index,
    desc,
)


if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.project_model import Project


class PaymentType(IntEnum):
    card = 1
    link = 2
    klarna = 3
    afterpay_clearpay = 4
    alipay = 5


class PaymentStatus(IntEnum):
    cancel = 1
    success = 2
    failed = 3


class Payment_Record(SQLModel, table=True):
    """支付记录表 - 存储博客支付记录信息"""

    __tablename__ = "payment_records"

    __table_args__ = (
        # 单列索引
        Index("idx_payment_record_id", "id"),
        Index("idx_payment_record_user_id", "user_id"),
        Index("idx_payment_record_project_id", "project_id"),
        Index("idx_payment_record_tax_name", "tax_name"),
        Index("idx_payment_record_order_number", "order_number"),
        Index("idx_payment_record_payment_type", "payment_type"),
        Index("idx_payment_record_payment_status", "payment_status"),
        # 复合索引
        # 排序索引
        Index("idx_payment_record_created_at_desc", desc("created_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    )
    project_id: Optional[int] = Field(
        sa_column=Column(ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True)
    )
    # 税费相关字段 - 存储支付时的快照
    tax_name: Optional[str] = Field(default=None, max_length=100)  # 税费名称
    tax_rate: Optional[float] = Field(default=None)  # 税费率
    tax_amount: Optional[float] = Field(default=None)  # 税费金额
    order_number: str = Field(nullable=False, max_length=64, unique=True)  # 优化长度
    payment_type: PaymentType = Field(nullable=False)
    amount: float = Field(nullable=False)
    payment_status: PaymentStatus = Field(nullable=False)
    created_at: datetime = Field(
        nullable=False,
        sa_type=TIMESTAMP,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    # 关系字段定义 - 支付记录的关联实体
    # 重要：支付记录作为重要业务数据，不应被级联删除
    user: "User" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "payment_records",
            "uselist": False,
            "lazy": "joined",  # 支付记录经常需要用户信息
        }
    )

    project: "Project" = Relationship(
        sa_relationship_kwargs={
            "back_populates": "payment_records",
            "uselist": False,
            "lazy": "joined",  # 支付记录经常需要项目信息
        }
    )

    def __repr__(self):
        return f"<Payment_Record(id={self.id}, order_number={self.order_number}, payment_type={self.payment_type.name}, amount={self.amount}, payment_status={self.payment_status.name}, user_id={self.user_id}, project_id={self.project_id}, tax_name={self.tax_name}, tax_rate={self.tax_rate}, tax_amount={self.tax_amount})>"


class Tax(SQLModel, table=True):
    """税费表 - 存储税费信息"""

    __tablename__ = "taxes"

    __table_args__ = (
        # 单列索引
        Index("idx_taxes_id", "id"),
        Index("idx_taxes_tax_name", "tax_name"),
        Index("idx_taxes_is_active", "is_active"),
        # 复合索引
        Index("idx_taxes_active_name", "is_active", "tax_name"),
        # 排序索引
        Index("idx_taxes_created_at_desc", desc("created_at")),
        Index("idx_taxes_updated_at_desc", desc("updated_at")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    tax_name: str = Field(nullable=False, max_length=100, unique=True)  # 优化长度
    tax_rate: float = Field(nullable=False, default=0.0)
    is_active: bool = Field(default=True, nullable=True)
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
        return f"<Tax(id={self.id}, tax_name={self.tax_name}, tax_rate={self.tax_rate}, is_active={self.is_active})>"
