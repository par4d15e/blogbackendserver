from fastapi import Depends, HTTPException
from typing import Dict, Any, Optional, Tuple, List
from app.crud.friend_crud import FriendCrud, get_friend_crud
from app.models.friend_model import FriendType, Friend_List
from app.models.user_model import RoleType
from app.core.i18n.i18n import Language


class FriendService:
    def __init__(self, friend_crud: FriendCrud):
        self.friend_crud = friend_crud

    async def get_friend_details(
        self,
    ) -> Dict[str, Any]:
        """获取友链详情信息"""
        return await self.friend_crud.get_friend_details()

    async def update_friend(
        self,
        role: RoleType,
        friend_id: int,
        chinese_title: str,
        chinese_description: str,
    ) -> bool:
        """更新友链分类"""
        return await self.friend_crud.update_friend(
            role=role,
            friend_id=friend_id,
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            
        )

    async def get_friend_list(
        self,
        friend_id: int,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取友链列表（分页）"""
        return await self.friend_crud.get_friend_list(
            friend_id=friend_id, limit=limit, cursor=cursor
        )

    async def get_friend_lists_by_offset_pagination(
        self,
        role: RoleType,
        page: int = 1,
        size: int = 10,
    ) -> Tuple[List[Friend_List], Dict[str, Any]]:
        """获取友链列表（分页）"""

        if role != RoleType.admin:
            raise HTTPException(status_code=403, detail="你没有权限访问这个接口")
        return await self.friend_crud.get_friend_lists_by_offset_pagination(
            page=page, size=size
        )

    async def create_single_friend(
        self,
        friend_id: int,
        user_id: int,
        logo_url: str,
        site_url: str,
        chinese_title: str,
        chinese_description: str,
    ) -> bool:
        """创建单个友链"""
        return await self.friend_crud.create_single_friend(
            friend_id=friend_id,
            user_id=user_id,
            logo_url=logo_url,
            site_url=site_url,
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            
        )

    async def delete_single_friend(
        self,
        role: RoleType,
        friend_list_id: int,
    ) -> bool:
        """删除单个友链"""
        return await self.friend_crud.delete_single_friend(
            role=role, friend_list_id=friend_list_id
        )

    async def update_friend_list_type(
        self,
        friend_list_id: int,
        type: FriendType,
        role: RoleType,
    ) -> bool:
        """更新友链类型"""
        return await self.friend_crud.update_friend_list_type(
            friend_list_id=friend_list_id, type=type, role=role
        )


def get_friend_service(
    friend_crud: FriendCrud = Depends(get_friend_crud),
) -> FriendService:
    return FriendService(friend_crud)
