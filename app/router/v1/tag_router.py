from fastapi import APIRouter, Depends, Response, Query
from app.schemas.tag_schemas import TagCreateRequest, TagUpdateRequest
from app.schemas.common import SuccessResponse
from app.router.v1.auth_router import get_current_user_dependency
from app.services.tag_service import get_tag_service, TagService
from app.utils.offset_pagination import offset_paginator
from app.utils.pagination_headers import set_pagination_headers
from app.core.i18n.i18n import get_message, get_language, Language


router = APIRouter(prefix="/tag", tags=["Tag"])


@router.get("/get-tag-lists", response_model=SuccessResponse)
async def get_tag_lists_router(
    response: Response,
    language: Language = Depends(get_language),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    tag_service: TagService = Depends(get_tag_service),
    published_only: bool = Query(False, description="是否只返回已发布标签"),
):
    """获取标签列表 - 使用传统分页方式"""

    items, pagination_metadata = await tag_service.get_tag_lists(
        language=language,
        page=page,
        size=size,
        published_only=published_only,
    )

    # 在响应头中添加分页信息
    set_pagination_headers(response, pagination_metadata)

    return SuccessResponse(
        message=get_message("tag.getTagLists", language),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.post("/admin/create-tag", response_model=SuccessResponse)
async def create_tag_router(
    form_data: TagCreateRequest,
    current_user=Depends(get_current_user_dependency),
    tag_service: TagService = Depends(get_tag_service),
    language: Language = Depends(get_language),
):
    result = await tag_service.create_tag(
        role=current_user.role,
        chinese_title=form_data.chinese_title,
        language=language,
    )
    return SuccessResponse(
        message=get_message("tag.createTag.createTagSuccess", language),
        data=result,
    )


@router.patch("/admin/update-tag", response_model=SuccessResponse)
async def update_tag_router(
    form_data: TagUpdateRequest,
    current_user=Depends(get_current_user_dependency),
    tag_service: TagService = Depends(get_tag_service),
    language: Language = Depends(get_language),
):
    result = await tag_service.update_tag(
        tag_id=form_data.tag_id,
        role=current_user.role,
        chinese_title=form_data.chinese_title,
        language=language,
    )
    return SuccessResponse(
        message=get_message("tag.updateTag", language),
        data=result,
    )


@router.delete("/admin/delete-tag/{tag_id}", response_model=SuccessResponse)
async def delete_tag_router(
    tag_id: int,
    current_user=Depends(get_current_user_dependency),
    tag_service: TagService = Depends(get_tag_service),
    language: Language = Depends(get_language),
):
    result = await tag_service.delete_tag(
        tag_id=tag_id,
        role=current_user.role,
        language=language,
    )
    return SuccessResponse(
        message=get_message("tag.deleteTag", language),
        data=result,
    )
