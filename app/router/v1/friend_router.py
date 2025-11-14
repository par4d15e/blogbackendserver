from fastapi import APIRouter, Depends, Query
from app.services.friend_service import FriendService, get_friend_service
from app.schemas.friend_schemas import (
    FriendUpdateRequest,
    SingleFriendCreateRequest,
    FriendListTypeUpdateRequest,
)
from app.schemas.common import SuccessResponse
from app.router.v1.auth_router import get_current_user_dependency
from app.core.i18n.i18n import get_message, get_language, Language
from app.utils.offset_pagination import offset_paginator


router = APIRouter(prefix="/friend", tags=["Friend"])


@router.get("/get-friend-details", response_model=SuccessResponse)
async def get_friend_details(
    language: Language = Depends(get_language),
    friend_service: FriendService = Depends(get_friend_service),
):
    result = await friend_service.get_friend_details(language=language)
    return SuccessResponse(
        message=get_message("friend.getFriendDetails", language),
        data=result,
    )


@router.patch("/admin/update-friend", response_model=SuccessResponse)
async def update_friend(
    form_data: FriendUpdateRequest,
    current_user=Depends(get_current_user_dependency),
    friend_service: FriendService = Depends(get_friend_service),
    language: Language = Depends(get_language),
):
    result = await friend_service.update_friend(
        role=current_user.role,
        friend_id=form_data.friend_id,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        language=language,
    )
    return SuccessResponse(
        message=get_message("friend.updateFriend", language),
        data=result,
    )


@router.get("/get-friend-list/{friend_id}", response_model=SuccessResponse)
async def get_friend_list(
    friend_id: int,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    friend_service: FriendService = Depends(get_friend_service),
    language: Language = Depends(get_language),
):
    """获取友链列表（分页）"""
    result = await friend_service.get_friend_list(
        friend_id=friend_id, limit=limit, cursor=cursor, language=language
    )
    return SuccessResponse(
        message=get_message("friend.getFriendList", language),
        data=result,
    )


@router.get("/admin/get-friend-lists", response_model=SuccessResponse)
async def get_friend_lists(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    current_user=Depends(get_current_user_dependency),
    friend_service: FriendService = Depends(get_friend_service),
):
    items, pagination_metadata = await friend_service.get_friend_lists_by_offset_pagination(
        role=current_user.role,
        page=page,
        size=size
    )
    return SuccessResponse(
        message="获取友链列表成功",
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.post("/create-single-friend", response_model=SuccessResponse)
async def create_single_friend(
    form_data: SingleFriendCreateRequest,
    current_user=Depends(get_current_user_dependency),
    friend_service: FriendService = Depends(get_friend_service),
    language: Language = Depends(get_language),
):
    """创建单个友链"""
    result = await friend_service.create_single_friend(
        friend_id=form_data.friend_id,
        user_id=current_user.id,
        logo_url=form_data.logo_url,
        site_url=form_data.site_url,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        language=language,
    )
    return SuccessResponse(
        message=get_message("friend.createSingleFriend", language),
        data=result,
    )


@router.delete("/delete-single-friend/{friend_list_id}", response_model=SuccessResponse)
async def delete_single_friend(
    friend_list_id: int,
    current_user=Depends(get_current_user_dependency),
    friend_service: FriendService = Depends(get_friend_service),
    language: Language = Depends(get_language),
):
    """删除单个友链"""
    result = await friend_service.delete_single_friend(
        role=current_user.role, friend_list_id=friend_list_id, language=language
    )
    return SuccessResponse(
        message=get_message("friend.deleteSingleFriend", language),
        data=result,
    )


@router.patch("/admin/update-friend-list-type", response_model=SuccessResponse)
async def update_friend_list_type(
    form_data: FriendListTypeUpdateRequest,
    current_user=Depends(get_current_user_dependency),
    friend_service: FriendService = Depends(get_friend_service),
    language: Language = Depends(get_language),
):
    """更新友链类型"""
    result = await friend_service.update_friend_list_type(
        friend_list_id=form_data.friend_list_id,
        type=form_data.type,
        role=current_user.role,
        language=language,
    )
    return SuccessResponse(
        message="朋友列表类型更新成功",
        data=result,
    )
