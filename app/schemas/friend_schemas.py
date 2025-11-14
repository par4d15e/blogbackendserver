from pydantic import BaseModel, Field
from app.models.friend_model import FriendType


class FriendIDSchema(BaseModel):
    friend_id: int = Field(..., description="友链ID")


class FriendUpdateRequest(FriendIDSchema):
    chinese_title: str = Field(..., description="中文标题")
    chinese_description: str = Field(..., description="中文描述")


class SingleFriendCreateRequest(BaseModel):
    friend_id: int = Field(..., description="友链ID")
    logo_url: str = Field(..., description="Logo URL")
    site_url: str = Field(..., description="网站 URL")
    chinese_title: str = Field(..., description="中文标题")
    chinese_description: str = Field(..., description="中文描述")


class FriendListTypeUpdateRequest(BaseModel):
    friend_list_id: int = Field(..., description="友链列表ID")
    type: FriendType = Field(..., description="友链类型")


class SingleFriendDeleteRequest(BaseModel):
    friend_list_id: int = Field(..., description="友链列表ID")
