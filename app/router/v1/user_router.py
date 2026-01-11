import os
from fastapi import APIRouter, Depends, Response, Query, UploadFile, File
from app.schemas.user_schemas import BioRequest, EnableDisableUserRequest
from app.schemas.common import SuccessResponse
from app.router.v1.auth_router import get_current_user_dependency
from app.services.user_service import get_user_service, UserService
from app.services.media_service import get_media_service, MediaService
from app.utils.offset_pagination import offset_paginator
from app.utils.pagination_headers import set_pagination_headers
from app.core.i18n.i18n import get_message
from app.core.logger import logger_manager
from app.core.database.redis import redis_manager

logger = logger_manager.get_logger(__name__)


router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me/get-my-profile", response_model=SuccessResponse)
async def get_my_profile_router(
    current_user=Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service),
):
    result = await user_service.get_profile(user_id=current_user.id)
    return SuccessResponse(
        message=get_message("user.getMyProfile"),
        data=result,
    )


@router.patch("/me/update-my-bio", response_model=SuccessResponse)
async def update_my_bio_router(
    form_data: BioRequest,
    current_user=Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service),
):
    result = await user_service.update_my_bio(
        user_id=current_user.id, bio=form_data.bio
    )
    return SuccessResponse(
        message=get_message("user.updateMyBio"),
        data=result,
    )


@router.post("/me/change-my-avatar", response_model=SuccessResponse)
async def change_my_avatar_router(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service),
    media_service: MediaService = Depends(get_media_service),
):
    temp_paths = await media_service.process_upload_files(files=[file])
    temp_path = temp_paths[0]  # 获取第一个（也是唯一一个）文件路径

    try:
        # 删除旧的avatar
        old_avatar = await user_service.get_my_avatar(current_user.id)
        if old_avatar:
            await media_service.delete_media_from_s3(
                media_ids=old_avatar["media_id"],
                user_id=current_user.id,
                
            )

        result = await media_service.upload_single_media_to_s3(
            local_file_path=temp_path,
            user_id=current_user.id,
            is_avatar=True,
            
        )

        # 删除缓存
        await redis_manager.delete_async(f"user_profile_{current_user.id}")

        return SuccessResponse(
            message=get_message("user.changeMyAvatar"),
            data=result,
        )
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")


@router.get("/other/get-other-user-profile/{user_id}", response_model=SuccessResponse)
async def get_user_profile_router(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    result = await user_service.get_profile(user_id=user_id)
    return SuccessResponse(
        message=get_message("user.getOtherUserProfile"),
        data=result,
    )


@router.get("/admin/get-user-lists", response_model=SuccessResponse)
async def get_user_lists_router(
    response: Response,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    current_user=Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service),
):
    """获取用户列表 - 使用传统分页方式"""
    items, pagination_metadata = await user_service.get_user_lists(
        page=page, size=size, role=current_user.role
    )

    # 在响应头中添加分页信息
    set_pagination_headers(response, pagination_metadata)

    return SuccessResponse(
        message=get_message("user.getUserLists"),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.patch("/admin/enable-disable-user")
async def enable_disable_user_router(
    form_data: EnableDisableUserRequest,
    current_user=Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service),
):
    result = await user_service.enable_or_disable_user(
        user_id=form_data.user_id,
        is_active=form_data.is_active,
        current_user_id=current_user.id,
        role=current_user.role,
        
    )
    return SuccessResponse(
        message=get_message("user.enableDisableUser.enableUserSuccess")
        if form_data.is_active
        else get_message("user.enableDisableUser.disableUserSuccess"),
        data=result,
    )


@router.delete("/admin/delete-user/{user_id}", response_model=SuccessResponse)
async def delete_user_router(
    user_id: int,
    current_user=Depends(get_current_user_dependency),
    user_service: UserService = Depends(get_user_service),
):
    result = await user_service.delete_user(
        user_id=user_id,
        role=current_user.role,
        current_user_id=current_user.id,
        
    )
    return SuccessResponse(
        message=get_message("user.deleteUser"),
        data=result,
    )
