from typing import Dict, Any, List, Optional, Tuple
from fastapi import Depends
from app.crud.seo_crud import get_seo_crud, SeoCrud
from app.models.user_model import RoleType
from app.core.i18n.i18n import Language


class SeoService:
    def __init__(self, seo_crud: SeoCrud):
        self.seo_crud = seo_crud

    async def get_seo_lists(
        self,
        language: str,
        page: int = 1,
        size: int = 20,
        role: Optional[RoleType] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Get seo lists with traditional pagination"""
        items, pagination_metadata = await self.seo_crud.get_seo_lists(
            page=page, size=size, language=language, role=role
        )
        return items, pagination_metadata

    async def create_seo(
        self,
        role: RoleType,
        chinese_title: str,
        chinese_description: str,
        chinese_keywords: str,
        language: Language,
    ) -> bool:
        return await self.seo_crud.create_seo(
            role=role,
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            chinese_keywords=chinese_keywords,
            language=language,
        )

    async def update_seo(
        self,
        seo_id: int,
        role: RoleType,
        chinese_title: str,
        chinese_description: str,
        chinese_keywords: str,
        language: Language,
    ) -> bool:
        return await self.seo_crud.update_seo(
            seo_id=seo_id,
            role=role,
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            chinese_keywords=chinese_keywords,
            language=language,
        )

    async def delete_seo(
        self,
        seo_id: int,
        role: RoleType,
        language: Language,
    ) -> bool:
        return await self.seo_crud.delete_seo(
            seo_id=seo_id, role=role, language=language
        )


def get_seo_service(seo_crud: SeoCrud = Depends(get_seo_crud)) -> SeoService:
    return SeoService(seo_crud)
