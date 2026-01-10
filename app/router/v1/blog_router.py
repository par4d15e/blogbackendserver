from fastapi import APIRouter, Depends, Query, Request, Response
from app.schemas.blog_schemas import CreateBlogRequest, UpdateBlogRequest
from app.schemas.common import SuccessResponse
from typing import Optional
from app.services.blog_service import get_blog_service, BlogService
from app.router.v1.auth_router import get_current_user_dependency
from app.utils.offset_pagination import offset_paginator
from app.utils.pagination_headers import set_pagination_headers
from app.core.i18n.i18n import get_message, Language, get_language
from app.schemas.blog_schemas import (
    CreateBlogCommentRequest,
    UpdateBlogCommentRequest,
    SaveBlogButtonRequest,
    LikeBlogButtonRequest,
    UpdateBlogStatusRequest,
)


router = APIRouter(prefix="/blog", tags=["Blog"])


@router.get("/get-blog-lists", response_model=SuccessResponse)
async def get_blog_lists(
    response: Response,
    language: Language = Depends(get_language),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    section_id: int = Query(..., description="栏目ID，必填"),
    blog_service: BlogService = Depends(get_blog_service),
    published_only: bool = Query(True, description="是否只返回已发布博客"),
):
    items, pagination_metadata = await blog_service.get_blog_lists(
        language=language,
        section_id=section_id,
        page=page,
        size=size,
        published_only=published_only,
    )
    set_pagination_headers(response, pagination_metadata)
    # 返回标准分页数据结构
    return SuccessResponse(
        message=get_message("blog.getBlogLists", language),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.post("/admin/create-blog", response_model=SuccessResponse)
async def create_blog(
    form_data: CreateBlogRequest,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.create_blog(
        user_id=current_user.id,
        section_id=form_data.section_id,
        seo_id=form_data.seo_id,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        chinese_content=form_data.chinese_content,
        cover_id=form_data.cover_id,
        blog_tags=form_data.blog_tags,
    )

    return SuccessResponse(
        message=get_message("blog.createBlog", language), data=result
    )


@router.patch("/admin/update-blog", response_model=SuccessResponse)
async def update_blog(
    form_data: UpdateBlogRequest,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.update_blog(
        language=language,
        user_id=current_user.id,
        blog_slug=form_data.blog_slug,
        seo_id=form_data.seo_id,
        cover_id=form_data.cover_id,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        chinese_content=form_data.chinese_content,
        blog_tags=form_data.blog_tags,
    )

    return SuccessResponse(
        message=get_message("blog.updateBlog", language), data=result
    )


@router.get("/get-blog-details-seo/{blog_slug}", response_model=SuccessResponse)
async def get_blog_details_seo(
    blog_slug: str,
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.get_blog_details_seo(
        blog_slug=blog_slug,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.getBlogDetailsSeo", language), data=result
    )


@router.get("/get-blog-details/{blog_slug}", response_model=SuccessResponse)
async def get_blog_details(
    request: Request,
    blog_slug: str,
    language: Language = Depends(get_language),
    is_editor: bool = Query(False, description="是否编辑器"),
    blog_service: BlogService = Depends(get_blog_service),
    user_id: Optional[int] = Query(None, description="用户ID，可选"),
):
    result = await blog_service.get_blog_details(
        request=request,
        blog_slug=blog_slug,
        language=language,
        is_editor=is_editor,
        user_id=user_id,
    )
    return SuccessResponse(
        message=get_message("blog.getBlogDetails", language), data=result
    )


@router.get("/get-blog-tts/{blog_id}", response_model=SuccessResponse)
async def get_blog_tts(
    blog_id: int,
    language: Language = Depends(get_language),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.get_blog_tts(
        blog_id=blog_id,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.getBlogTTS.getBlogTTSSuccess", language), data=result
    )


@router.get("/get-blog-summary/{blog_id}", response_model=SuccessResponse)
async def get_blog_summary(
    blog_id: int,
    language: Language = Depends(get_language),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.get_blog_summary(
        blog_id=blog_id,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.getBlogSummary.getBlogSummarySuccess", language),
        data=result,
    )


@router.get("/get-blog-comment-lists/{blog_id}", response_model=SuccessResponse)
async def get_blog_comment_lists(
    blog_id: int,
    limit: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    language: Language = Depends(get_language),
    cursor: Optional[str] = Query(None, description="游标，可选"),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.get_blog_comment_lists(
        blog_id=blog_id,
        limit=limit,
        cursor=cursor,
        language=language,
    )
    return SuccessResponse(
        message=get_message(
            "blog.getBlogCommentLists.getBlogCommentListsSuccess", language
        ),
        data=result,
    )


@router.post("/create-blog-comment", response_model=SuccessResponse)
async def create_blog_comment(
    form_data: CreateBlogCommentRequest,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.create_blog_comment(
        user_id=current_user.id,
        blog_id=form_data.blog_id,
        comment=form_data.comment,
        parent_id=form_data.parent_id,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.createBlogComment", language), data=result
    )


@router.patch("/update-blog-comment", response_model=SuccessResponse)
async def update_blog_comment(
    form_data: UpdateBlogCommentRequest,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.update_blog_comment(
        user_id=current_user.id,
        comment_id=form_data.comment_id,
        comment=form_data.comment,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.updateBlogComment", language), data=result
    )


@router.delete("/delete-blog-comment/{comment_id}", response_model=SuccessResponse)
async def delete_blog_comment(
    comment_id: int,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.delete_blog_comment(
        user_id=current_user.id,
        role=current_user.role,
        comment_id=comment_id,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.deleteBlogComment", language), data=result
    )


@router.post("/save-blog-button", response_model=SuccessResponse)
async def save_blog_button(
    form_data: SaveBlogButtonRequest,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.save_blog_button(
        user_id=current_user.id,
        blog_id=form_data.blog_id,
        language=language,
    )

    if result:
        return SuccessResponse(
            message=get_message("blog.saveBlogButton.saveBlogButtonSuccess", language),
            data=result,
        )
    else:
        return SuccessResponse(
            message=get_message(
                "blog.saveBlogButton.unsaveBlogButtonSuccess", language
            ),
            data=result,
        )


@router.post("/like-blog-button", response_model=SuccessResponse)
async def like_blog_button(
    request: Request,
    form_data: LikeBlogButtonRequest,
    language: Language = Depends(get_language),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.like_blog_button(
        request=request,
        blog_id=form_data.blog_id,
        language=language,
    )

    if result:
        return SuccessResponse(
            message=get_message("blog.likeBlogButton.likedBlogButtonSuccess", language),
            data=result,
        )
    else:
        return SuccessResponse(
            message=get_message(
                "blog.likeBlogButton.unlikeBlogButtonSuccess", language
            ),
            data=result,
        )


@router.patch("/update-blog-status", response_model=SuccessResponse)
async def update_blog_status(
    form_data: UpdateBlogStatusRequest,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.update_blog_status(
        blog_id=form_data.blog_id,
        language=language,
        is_published=form_data.is_published,
        is_archived=form_data.is_archived,
        is_featured=form_data.is_featured,
        role=current_user.role,
    )
    if result and form_data.is_published:
        return SuccessResponse(
            message=get_message("blog.updateBlogStatus.blogPublishedSuccess", language),
            data=result,
        )
    elif result and not form_data.is_published:
        return SuccessResponse(
            message=get_message(
                "blog.updateBlogStatus.blogUnpublishedSuccess", language
            ),
            data=result,
        )
    elif result and form_data.is_archived:
        return SuccessResponse(
            message=get_message("blog.updateBlogStatus.blogArchivedSuccess", language),
            data=result,
        )
    elif result and not form_data.is_archived:
        return SuccessResponse(
            message=get_message(
                "blog.updateBlogStatus.blogUnarchivedSuccess", language
            ),
            data=result,
        )
    elif result and form_data.is_featured:
        return SuccessResponse(
            message=get_message("blog.updateBlogStatus.blogFeaturedSuccess", language),
            data=result,
        )
    else:
        return SuccessResponse(
            message=get_message(
                "blog.updateBlogStatus.blogUnfeaturedSuccess", language
            ),
            data=result,
        )


@router.get("/get-blog-navigation/{blog_id}", response_model=SuccessResponse)
async def get_blog_navigation(
    blog_id: int,
    language: Language = Depends(get_language),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.get_blog_navigation(
        blog_id=blog_id,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.getBlogNavigation", language), data=result
    )


@router.get("/get-blog-stats/{blog_id}", response_model=SuccessResponse)
async def get_blog_stats(
    blog_id: int,
    language: Language = Depends(get_language),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.get_blog_stats(
        blog_id=blog_id,
        language=language,
    )
    return SuccessResponse(
        message=get_message("blog.getBlogStats.getBlogStatsSuccess", language),
        data=result,
    )


@router.delete("/admin/delete-blog/{blog_id}", response_model=SuccessResponse)
async def delete_blog(
    blog_id: int,
    current_user=Depends(get_current_user_dependency),
    blog_service: BlogService = Depends(get_blog_service),
    language: Language = Depends(get_language),
):
    result = await blog_service.delete_blog(
        blog_id=blog_id,
        language=language,
        role=current_user.role,
    )
    return SuccessResponse(
        message=get_message("blog.deleteBlog.deleteBlogSuccess", language), data=result
    )


@router.get("/get-saved-blog-lists", response_model=SuccessResponse)
async def get_saved_blog_lists(
    user_id: int,
    language: Language = Depends(get_language),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.get_saved_blog_lists(
        user_id=user_id,
        language=language,
        page=page,
        size=size,
    )
    return SuccessResponse(
        message=get_message("blog.getSavedBlogLists", language), data=result
    )


@router.get("/get-recent-popular-blog", response_model=SuccessResponse)
async def get_recent_popular_blog(
    language: Language = Depends(get_language),
    blog_service: BlogService = Depends(get_blog_service),
):
    result = await blog_service.get_recent_populor_blog(language=language)

    return SuccessResponse(
        message=get_message("blog.getRecentPopularBlog", language), data=result
    )


@router.get("/get-blog-lists-by-tag-slug/{tag_slug}", response_model=SuccessResponse)
async def get_blog_lists_by_tag_slug(
    response: Response,
    tag_slug: str,
    language: Language = Depends(get_language),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    blog_service: BlogService = Depends(get_blog_service),
):
    """根据标签slug获取博客列表 - 使用传统分页方式"""
    items, pagination_metadata = await blog_service.get_blog_lists_by_tag_slug(
        tag_slug=tag_slug,
        language=language,
        page=page,
        size=size,
    )

    # 在响应头中添加分页信息
    set_pagination_headers(response, pagination_metadata)

    # 返回标准分页数据结构
    return SuccessResponse(
        message=get_message("blog.getBlogListsByTagSlug", language),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.get("/get-archived-blog-lists", response_model=SuccessResponse)
async def get_archived_blog_lists(
    language: Language = Depends(get_language),
    limit: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    cursor: Optional[str] = Query(None, description="游标，可选"),
    blog_service: BlogService = Depends(get_blog_service),
):
    """获取归档的博客列表 - 使用 cursor pagination"""
    result = await blog_service.get_archived_blog_lists(
        language=language,
        cursor=cursor,
        limit=limit,
    )
    return SuccessResponse(
        message=get_message("blog.getArchivedBlogLists", language),
        data=result,
    )
