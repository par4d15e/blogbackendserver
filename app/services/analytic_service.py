from typing import List, Dict, Any
from fastapi import Depends, HTTPException
from app.models.user_model import RoleType
from app.crud.analytic_crud import AnalyticCrud, get_analytic_crud


class AnalyticService:
    def __init__(self, analytic_crud: AnalyticCrud):
        self.analytic_crud = analytic_crud

    async def get_user_location(self, role: RoleType) -> List[Dict[str, Any]]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_user_location()

    async def get_blog_statistics(self, role: RoleType) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_blog_statistics()

    async def get_top_ten_blog_performers(self, role: RoleType) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_top_ten_blog_performers()

    async def get_tag_statistics(
        self, role: RoleType, limit: int = 20
    ) -> List[Dict[str, Any]]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_tag_statistics(limit)

    async def get_project_statistics(self, role: RoleType) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_project_statistics()

    async def get_payment_statistics(self, role: RoleType) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_payment_statistics()

    async def get_top_ten_revenue_projects(
        self, role: RoleType
    ) -> List[Dict[str, Any]]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_top_ten_revenue_projects()

    async def get_user_statistics(self, role: RoleType) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_user_statistics()

    async def get_media_statistics(self, role: RoleType) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_media_statistics()

    async def get_growth_trends(self, role: RoleType, days: int = 30) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_growth_trends(days)

    async def get_overview_statistics(self, role: RoleType) -> Dict[str, Any]:
        if role != RoleType.admin:
            raise HTTPException(
                status_code=403, detail="You are not authorized to access this resource"
            )
        return await self.analytic_crud.get_overview_statistics()


def get_analytic_service(
    analytic_crud: AnalyticCrud = Depends(get_analytic_crud),
) -> AnalyticService:
    return AnalyticService(analytic_crud)
