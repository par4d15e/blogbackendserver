from pydantic import BaseModel, Field


class TagCreateRequest(BaseModel):
    chinese_title: str = Field(..., description="标签中文名")


class TagUpdateRequest(BaseModel):
    tag_id: int = Field(..., description="标签ID")
    chinese_title: str = Field(..., description="标签中文名")
