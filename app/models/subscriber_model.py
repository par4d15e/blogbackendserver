from sqlmodel import SQLModel, Field, Column
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import DateTime


class Subscriber(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    is_active: bool = True  # 是否订阅
    subscribed_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
        )
    )
    unsubscribed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )  # 用户取消订阅时间

    def __str__(self):
        return f"Subscriber(id={self.id}, email={self.email}, is_active={self.is_active})"
