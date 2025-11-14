from typing import Dict, Any, List, Optional, Tuple
from fastapi import Depends
from app.crud.user_crud import UserCrud, get_user_crud
from app.core.i18n.i18n import Language


class UserService:
    def __init__(self, user_crud: UserCrud):
        self.user_crud = user_crud

    async def get_profile(self, user_id: int, language: Language) -> Dict[str, Any]:
        """Get my profile"""
        user = await self.user_crud.get_profile(user_id=user_id, language=language)
        return user

    async def update_my_bio(self, user_id: int, bio: str) -> bool:
        """Update my bio"""
        await self.user_crud.update_my_bio(user_id=user_id, bio=bio)
        return True

    async def get_my_avatar(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get my avatar"""
        result = await self.user_crud.get_my_avatar(user_id=user_id)
        if not result:
            return None

        return {"media_id": result["media_id"]}

    async def get_user_lists(
        self,
        language: Language,
        page: int = 1,
        size: int = 20,
        role: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Get all users with traditional pagination"""
        items, pagination_metadata = await self.user_crud.get_user_lists(
            language=language, page=page, size=size, role=role
        )
        return items, pagination_metadata

    async def delete_user(
        self, user_id: int, role: int, current_user_id: int, language: Language
    ) -> bool:
        """Delete user by id"""
        await self.user_crud.delete_user(
            user_id=user_id,
            role=role,
            current_user_id=current_user_id,
            language=language,
        )
        return True

    async def enable_or_disable_user(
        self,
        user_id: int,
        is_active: bool,
        current_user_id: int,
        role: int,
        language: Language,
    ) -> bool:
        """Enable or disable user by id"""
        await self.user_crud.enable_or_disable_user(
            user_id=user_id,
            is_active=is_active,
            current_user_id=current_user_id,
            role=role,
            language=language,
        )
        return True


def get_user_service(user_crud: UserCrud = Depends(get_user_crud)) -> UserService:
    return UserService(user_crud)
