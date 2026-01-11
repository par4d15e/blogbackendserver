from typing import Optional, List, Dict, Any
from fastapi import Depends
from app.core.logger import logger_manager
from app.core.i18n.i18n import Language
from app.crud.section_crud import get_section_crud, SectionCrud


class SectionService:
    def __init__(self, section_crud: SectionCrud):
        self.section_crud = section_crud
        self.logger = logger_manager.get_logger(__name__)

    async def get_section_lists(self) -> List[Dict[str, Any]]:
        return await self.section_crud.get_section_lists()

    async def get_section_seo_by_slug(
        self, slug: str
    ) -> Optional[Dict[str, Any]]:
        return await self.section_crud.get_section_seo_by_slug(
            slug=slug
        )

    async def get_section_details_by_slug(
        self, slug: str
    ) -> Optional[Dict[str, Any]]:
        return await self.section_crud.get_section_details_by_slug(
            slug=slug
        )

    async def update_section(
        self,
        seo_id: Optional[int],
        section_id: int,
        chinese_title: str,
        chinese_description: str,
        role: str,
        is_active: Optional[bool] = True,
    ) -> bool:
        return await self.section_crud.update_section(
            section_id=section_id,
            
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            role=role,
            seo_id=seo_id,
            is_active=is_active,
        )


def get_section_service(
    section_crud: SectionCrud = Depends(get_section_crud),
) -> SectionService:
    return SectionService(section_crud)
