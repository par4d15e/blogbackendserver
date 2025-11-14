from pydantic import BaseModel, Field
from typing import Optional


class BoardIDSchema(BaseModel):
    board_id: int = Field(..., description="板块ID")


class BoardUpdateRequest(BoardIDSchema):
    chinese_title: str = Field(..., description="中文标题")
    chinese_description: Optional[str] = Field(..., description="中文描述")


class BoardCommentCreateRequest(BaseModel):
    board_id: int = Field(..., description="留言板ID")
    parent_id: Optional[int] = Field(None, description="父评论ID，用于回复功能")
    comment: str = Field(..., max_length=500, description="评论内容，最大500字符")


class BoardCommentUpdateRequest(BaseModel):
    board_comment_id: int = Field(..., description="评论ID")
    comment: str = Field(..., max_length=500, description="评论内容，最大500字符")


class BoardCommentDeleteRequest(BaseModel):
    board_comment_id: int = Field(..., description="评论ID")
