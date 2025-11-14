from pydantic import BaseModel, Field


class SeoIDSchema(BaseModel):
    seo_id: int = Field(..., description="SEO ID")


class SeoCreateRequest(BaseModel):
    chinese_title: str = Field(..., description="SEO title")
    chinese_description: str = Field(..., description="SEO description")
    chinese_keywords: str = Field(..., description="SEO keywords")


class SeoUpdateRequest(BaseModel):
    seo_id: int = Field(..., description="SEO ID")
    chinese_title: str = Field(..., description="SEO title")
    chinese_description: str = Field(
        default="这是一个用于seo测试的博客文章的描述", description="SEO description"
    )
    chinese_keywords: str = Field(
        default="测试，文章， 博客", description="SEO keywords"
    )
