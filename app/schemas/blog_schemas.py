from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import json


class CreateBlogRequest(BaseModel):
    section_id: int = Field(default=6, description="Section ID")
    seo_id: int = Field(default=1, description="SEO ID")
    chinese_title: str = Field(default="文章测试", description="Chinese Title")
    chinese_description: str = Field(
        default="文章测试", description="Chinese Description"
    )
    chinese_content: Dict[str, Any] = Field(
        default={"type": "doc", "content": []}, description="Chinese Content")
    cover_id: int = Field(default=89, description="Cover ID")
    blog_tags: List[int] = Field(default=[9, 10, 11], description="Blog Tags")

    @field_validator('chinese_content', mode='before')
    @classmethod
    def parse_chinese_content(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f'chinese_content must be valid JSON: {str(e)}')
        elif v is None:
            return {"type": "doc", "content": []}
        return v

    @field_validator('section_id', 'seo_id', 'cover_id', mode='before')
    @classmethod
    def parse_int_fields(cls, v):
        if v is None:
            raise ValueError('Field cannot be null')
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError(
                f'Field must be a valid integer, got: {type(v).__name__}')

    @field_validator('blog_tags', mode='before')
    @classmethod
    def parse_blog_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            # 过滤掉 null 值，只保留有效的整数
            valid_tags = []
            for item in v:
                if item is not None:
                    try:
                        valid_tags.append(int(item))
                    except (ValueError, TypeError):
                        # 跳过无效的值，不抛出错误
                        continue
            return valid_tags
        raise ValueError('blog_tags must be a list')


class UpdateBlogRequest(BaseModel):
    blog_slug: str = Field(..., description="Blog Slug")
    chinese_title: str = Field(default="文章测试", description="Chinese Title")
    chinese_description: str = Field(
        default="文章测试", description="Chinese Description"
    )
    chinese_content: Dict[str, Any] = Field(
        default={"type": "doc", "content": []}, description="Chinese Content")

    @field_validator('chinese_content', mode='before')
    @classmethod
    def parse_chinese_content(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f'chinese_content must be valid JSON: {str(e)}')
        elif v is None:
            return {"type": "doc", "content": []}
        return v


class CreateBlogCommentRequest(BaseModel):
    blog_id: int = Field(default=12, description="Blog ID")
    comment: str = Field(default="文章测试", description="Comment")
    parent_id: Optional[int] = Field(default=None, description="Parent ID")


class UpdateBlogCommentRequest(BaseModel):
    comment_id: int = Field(default=12, description="Comment ID")
    comment: str = Field(default="文章测试", description="Comment")


class SaveBlogButtonRequest(BaseModel):
    blog_id: int = Field(default=12, description="Blog ID")


class LikeBlogButtonRequest(BaseModel):
    blog_id: int = Field(default=12, description="Blog ID")


class UpdateBlogStatusRequest(BaseModel):
    blog_id: int = Field(..., description="Blog ID")
    is_published: Optional[bool] = Field(
        default=None, description="Is Published")
    is_archived: Optional[bool] = Field(
        default=None, description="Is Archived")
    is_featured: Optional[bool] = Field(
        default=None, description="Is Featured")
