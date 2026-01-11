from typing import Optional
from fastapi import APIRouter, Depends, Response, Query
from app.schemas.project_schemas import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    PublishOrUnpublishRequest,
)
from app.schemas.common import SuccessResponse
from app.router.v1.auth_router import get_current_user_dependency
from app.services.project_service import get_project_service, ProjectService
from app.utils.offset_pagination import offset_paginator
from app.utils.pagination_headers import set_pagination_headers
from app.core.i18n.i18n import get_message


router = APIRouter(prefix="/project", tags=["Project"])


@router.get("/get-project-lists", response_model=SuccessResponse)
async def get_project_lists_router(
    response: Response,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    published_only: bool = Query(True, description="是否只返回已发布项目"),
    project_service: ProjectService = Depends(get_project_service),
):
    items, pagination_metadata = await project_service.get_project_lists(
         page=page, size=size, published_only=published_only
    )
    set_pagination_headers(response, pagination_metadata)
    return SuccessResponse(
        message=get_message("project.getProjectLists"),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.post("/admin/create-project", response_model=SuccessResponse)
async def create_project_router(
    request: ProjectCreateRequest,
    current_user=Depends(get_current_user_dependency),
    project_service: ProjectService = Depends(get_project_service),
):
    result = await project_service.create_project(
        
        project_type=request.project_type,
        section_id=request.section_id,
        seo_id=request.seo_id,
        cover_id=request.cover_id,
        chinese_title=request.chinese_title,
        chinese_description=request.chinese_description,
        chinese_content=request.chinese_content,
        attachment_id=request.attachment_id,
        price=request.price,
        role=current_user.role,
    )
    return SuccessResponse(
        message=get_message("project.createProject"),
        data=result,
    )


@router.patch("/admin/update-project", response_model=SuccessResponse)
async def update_project_router(
    request: ProjectUpdateRequest,
    current_user=Depends(get_current_user_dependency),
    project_service: ProjectService = Depends(get_project_service),
):
    result = await project_service.update_project(
        
        project_slug=request.project_slug,
        project_type=request.project_type,
        seo_id=request.seo_id,
        cover_id=request.cover_id,
        chinese_title=request.chinese_title,
        chinese_description=request.chinese_description,
        chinese_content=request.chinese_content,
        attachment_id=request.attachment_id,
        price=request.price,
        role=current_user.role,
    )
    return SuccessResponse(
        message=get_message("project.updateProject"),
        data=result,
    )


@router.patch("/admin/publish-or-unpublish-project", response_model=SuccessResponse)
async def publish_or_unpublish_project_router(
    request: PublishOrUnpublishRequest,
    current_user=Depends(get_current_user_dependency),
    project_service: ProjectService = Depends(get_project_service),
):
    result = await project_service.publish_Or_Unpublish_project(
        
        project_id=request.project_id,
        is_publish=request.is_publish,
        role=current_user.role,
    )

    if request.is_publish:
        message_key = "project.publishOrUnpublishProject.publishProjectSuccess"
    else:
        message_key = "project.publishOrUnpublishProject.unpublishProjectSuccess"

    return SuccessResponse(
        message=get_message(message_key),
        data=result,
    )


@router.get("/get-project-details/{project_slug}", response_model=SuccessResponse)
async def get_project_details_router(
    project_slug: str,
    user_id: Optional[int] = Query(None, description="用户ID，用于检查支付状态"),
    is_editor: Optional[bool] = Query(False, description="是否为编辑模式"),
    project_service: ProjectService = Depends(get_project_service),
):
    result = await project_service.get_project_details(
        
        project_slug=project_slug,
        user_id=user_id,
        is_editor=is_editor,
    )
    return SuccessResponse(
        message=get_message("project.getProjectDetails"),
        data=result,
    )


@router.get("/get-project-details-seo/{project_slug}", response_model=SuccessResponse)
async def get_project_details_seo_router(
    project_slug: str,
    project_service: ProjectService = Depends(get_project_service),
):
    result = await project_service.get_project_details_seo(
         project_slug=project_slug
    )
    return SuccessResponse(
        message=get_message("project.getProjectDetailsSeo"),
        data=result,
    )


@router.delete("/admin/delete-project/{project_id}", response_model=SuccessResponse)
async def delete_project_router(
    project_id: int,
    current_user=Depends(get_current_user_dependency),
    project_service: ProjectService = Depends(get_project_service),
):
    result = await project_service.delete_project(
         project_id=project_id, role=current_user.role
    )
    return SuccessResponse(
        message=get_message("project.deleteProject"),
        data=result,
    )
