from typing import Optional, List, Dict, Any, Tuple
from fastapi import Depends, HTTPException
from app.core.i18n.i18n import Language, get_message
from app.core.logger import logger_manager
from app.models.project_model import ProjectType
from app.models.user_model import RoleType
from app.crud.project_crud import ProjectCrud, get_project_crud


class ProjectService:
    def __init__(self, project_crud: ProjectCrud):
        self.project_crud = project_crud
        self.logger = logger_manager.get_logger(__name__)

    async def get_project_lists(
        self,
        language: Language,
        page: int = 1,
        size: int = 20,
        published_only: bool = True,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return await self.project_crud.get_project_lists(
            language=language, page=page, size=size, published_only=published_only
        )

    async def create_project(
        self,
        language: Language,
        project_type: ProjectType,
        section_id: int,
        seo_id: Optional[int],
        cover_id: int,
        chinese_title: str,
        chinese_description: str,
        chinese_content: dict,
        role: RoleType,
        attachment_id: Optional[int],
        price: float = 0.0,
    ) -> str:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403,
                detail=get_message("common.insufficientPermissions", language),
            )
        return await self.project_crud.create_project(
            language=language,
            project_type=project_type,
            section_id=section_id,
            seo_id=seo_id,
            cover_id=cover_id,
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            chinese_content=chinese_content,
            attachment_id=attachment_id,
            price=price,
        )

    async def update_project(
        self,
        language: Language,
        project_slug: str,
        project_type: ProjectType,
        seo_id: Optional[int],
        cover_id: int,
        chinese_title: str,
        chinese_description: str,
        chinese_content: dict,
        role: RoleType,
        attachment_id: Optional[int],
        price: float = 0.0,
    ) -> str:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403,
                detail=get_message("common.insufficientPermissions", language),
            )
        return await self.project_crud.update_project(
            language=language,
            project_slug=project_slug,
            project_type=project_type,
            seo_id=seo_id,
            cover_id=cover_id,
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            chinese_content=chinese_content,
            attachment_id=attachment_id,
            price=price,
        )

    async def publish_Or_Unpublish_project(
        self,
        language: Language,
        project_id: int,
        is_publish: bool = True,
        role: RoleType = RoleType.admin,
    ) -> bool:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403,
                detail=get_message("common.insufficientPermissions", language),
            )
        return await self.project_crud.publish_Or_Unpublish_project(
            language=language, project_id=project_id, is_publish=is_publish
        )

    async def get_project_details(
        self,
        language: Language,
        project_slug: str,
        user_id: Optional[int] = None,
        is_editor: Optional[bool] = False,
    ) -> Dict[str, Any]:
        return await self.project_crud.get_project_details(
            language=language,
            project_slug=project_slug,
            user_id=user_id,
            is_editor=is_editor,
        )

    async def get_project_details_seo(
        self, language: Language, project_slug: str
    ) -> Dict[str, Any]:
        return await self.project_crud.get_project_details_seo(
            language=language, project_slug=project_slug
        )

    async def delete_project(
        self, language: Language, project_id: int, role: RoleType
    ) -> bool:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403,
                detail=get_message("common.insufficientPermissions", language),
            )
        return await self.project_crud.delete_project(
            language=language, project_id=project_id
        )


def get_project_service(
    project_crud: ProjectCrud = Depends(get_project_crud),
) -> ProjectService:
    return ProjectService(project_crud)
