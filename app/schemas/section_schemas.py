from pydantic import BaseModel, Field
from typing import Optional


class SectionIDSchema(BaseModel):
    section_id: int = Field(default=2, description="Section ID")


class UpdateSectionRequest(SectionIDSchema):
    seo_id: Optional[int] = Field(default=None, description="SEO ID")
    chinese_title: str = Field(default="测试", description="Chinese Title")
    chinese_description: str = Field(default="测试", description="Chinese Description")
    is_active: Optional[bool] = Field(default=True, description="Is Active")
