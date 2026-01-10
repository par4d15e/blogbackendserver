from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
import json
from app.models.project_model import ProjectType


class ProjectIDSchema(BaseModel):
    project_id: int = Field(..., description="项目ID")


class ProjectRequestSchema(BaseModel):
    project_type: ProjectType = Field(..., description="项目类型")
    section_id: Optional[int] = Field(default=None, description="栏目ID")
    seo_id: Optional[int] = Field(default=None, description="SEO ID")
    cover_id: int = Field(..., description="封面ID")
    chinese_title: str = Field(..., description="中文标题")
    chinese_description: str = Field(..., description="中文描述")
    chinese_content: Dict[str, Any] = Field(..., description="中文内容")
    attachment_id: Optional[int] = Field(default=None, description="附件ID")
    price: float = Field(default=0.0, description="价格")

    @field_validator("chinese_content", mode="before")
    @classmethod
    def parse_chinese_content(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("chinese_content must be valid JSON")
        return v


class ProjectCreateRequest(ProjectRequestSchema):
    pass


class ProjectUpdateRequest(ProjectRequestSchema):
    project_slug: str = Field(..., description="项目Slug")


class PublishOrUnpublishRequest(
    ProjectIDSchema,
):
    is_publish: bool = Field(
        default=True, description="发布状态，True为发布，False为取消发布"
    )
