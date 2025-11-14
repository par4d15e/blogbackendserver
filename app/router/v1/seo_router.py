from fastapi import APIRouter, Depends, Response, Query
from app.schemas.seo_schemas import SeoCreateRequest, SeoUpdateRequest
from app.schemas.common import SuccessResponse
from app.router.v1.auth_router import get_current_user_dependency
from app.services.seo_service import get_seo_service, SeoService
from app.utils.offset_pagination import offset_paginator
from app.utils.pagination_headers import set_pagination_headers
from app.core.i18n.i18n import get_message, get_language, Language


router = APIRouter(prefix="/seo", tags=["Seo"])


@router.get("/admin/get-seo-lists", response_model=SuccessResponse)
async def get_seo_lists_router(
    response: Response,
    language: Language = Depends(get_language),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    current_user=Depends(get_current_user_dependency),
    seo_service: SeoService = Depends(get_seo_service),
):
    """获取SEO列表 - 使用传统分页方式"""
    items, pagination_metadata = await seo_service.get_seo_lists(
        page=page, size=size, language=language, role=current_user.role
    )

    # 在响应头中添加分页信息
    set_pagination_headers(response, pagination_metadata)

    return SuccessResponse(
        message=get_message("seo.getSeoLists", language),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.post("/admin/create-seo", response_model=SuccessResponse)
async def create_seo_router(
    form_data: SeoCreateRequest,
    current_user=Depends(get_current_user_dependency),
    seo_service: SeoService = Depends(get_seo_service),
    language: Language = Depends(get_language),
):
    result = await seo_service.create_seo(
        role=current_user.role,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        chinese_keywords=form_data.chinese_keywords,
        language=language,
    )
    return SuccessResponse(
        message=get_message("seo.createSeo.createSeoSuccess", language),
        data=result,
    )


@router.patch("/admin/update-seo", response_model=SuccessResponse)
async def update_seo_router(
    form_data: SeoUpdateRequest,
    current_user=Depends(get_current_user_dependency),
    seo_service: SeoService = Depends(get_seo_service),
    language: Language = Depends(get_language),
):
    result = await seo_service.update_seo(
        seo_id=form_data.seo_id,
        role=current_user.role,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        chinese_keywords=form_data.chinese_keywords,
        language=language,
    )
    return SuccessResponse(
        message=get_message("seo.updateSeo.updateSeoSuccess", language),
        data=result,
    )


@router.delete("/admin/delete-seo/{seo_id}", response_model=SuccessResponse)
async def delete_seo_router(
    seo_id: int,
    current_user=Depends(get_current_user_dependency),
    seo_service: SeoService = Depends(get_seo_service),
    language: Language = Depends(get_language),
):
    result = await seo_service.delete_seo(
        seo_id=seo_id,
        role=current_user.role,
        language=language,
    )
    return SuccessResponse(
        message=get_message("seo.deleteSeo", language),
        data=result,
    )
