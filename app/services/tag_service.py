from fastapi import Depends
from typing import Dict, Any, List, Optional, Tuple
from app.crud.tag_crud import TagCrud, get_tag_crud
from app.models.user_model import RoleType
from app.core.i18n.i18n import Language


class TagService:
    def __init__(self, tag_crud: TagCrud):
        self.tag_crud = tag_crud

    async def get_tag_lists(
        self,
        page: int = 1,
        size: int = 20,
        published_only: Optional[bool] = False,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Get tag lists with traditional pagination"""
        items, pagination_metadata = await self.tag_crud.get_tag_lists(
            page=page,
            size=size,
            published_only=published_only,
        )
        return items, pagination_metadata

    async def create_tag(
        self,
        role: RoleType,
        chinese_title: str,
    ) -> bool:
        return await self.tag_crud.create_tag(role=role, chinese_title=chinese_title)

    async def update_tag(
        self,
        tag_id: int,
        role: RoleType,
        chinese_title: str,
    ) -> bool:
        return await self.tag_crud.update_tag(
            tag_id=tag_id, role=role, chinese_title=chinese_title
        )

    async def delete_tag(
        self,
        tag_id: int,
        role: RoleType,
    ) -> bool:
        return await self.tag_crud.delete_tag(tag_id=tag_id, role=role)


def get_tag_service(tag_crud: TagCrud = Depends(get_tag_crud)) -> TagService:
    return TagService(tag_crud)
