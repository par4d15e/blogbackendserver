from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum


class SuccessResponse(BaseModel):
    status: int = 200
    message: str
    data: Optional[Any] = None


class LargeContentTranslationType(str, Enum):
    BLOG = "blog"
    PROJECT = "project"


class NotificationType(Enum):
    FRIEND_REQUEST = "friend_request"
    PAYMENT_REQUEST = "payment_request"
