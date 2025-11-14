from fastapi import APIRouter, Depends, Query
from app.schemas.common import SuccessResponse
from app.router.v1.auth_router import get_current_user_dependency
from app.services.analytic_service import get_analytic_service, AnalyticService

router = APIRouter(prefix="/analytic", tags=["Analytic"])


@router.get("/admin/overview", response_model=SuccessResponse)
async def get_overview_statistics_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取总览统计数据"""
    result = await analytic_service.get_overview_statistics(role=current_user.role)
    return SuccessResponse(
        message="总览统计数据获取成功",
        data=result,
    )


@router.get("/admin/user-location", response_model=SuccessResponse)
async def get_user_location_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取所有用户的地理位置（经纬度）"""
    result = await analytic_service.get_user_location(role=current_user.role)
    return SuccessResponse(
        message="用户地理位置数据获取成功",
        data=result
    )


@router.get("/admin/blog-statistics", response_model=SuccessResponse)
async def get_blog_statistics_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取博客统计数据"""
    result = await analytic_service.get_blog_statistics(role=current_user.role)
    return SuccessResponse(
        message="博客统计数据获取成功",
        data=result
    )


@router.get("/admin/top-ten-blog-performers", response_model=SuccessResponse)
async def get_top_ten_blog_performers_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取博客热门前十排行"""
    result = await analytic_service.get_top_ten_blog_performers(role=current_user.role)
    return SuccessResponse(
        message="博客热门前十排行数据获取成功",
        data=result,
    )


@router.get("/admin/tag-statistics", response_model=SuccessResponse)
async def get_tag_statistics_router(
    limit: int = Query(default=20, ge=1, le=100),
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取标签统计（热门标签）"""
    result = await analytic_service.get_tag_statistics(role=current_user.role, limit=limit)
    return SuccessResponse(
        message="标签统计数据获取成功",
        data=result
    )


@router.get("/admin/project-statistics", response_model=SuccessResponse)
async def get_project_statistics_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取项目统计数据"""
    result = await analytic_service.get_project_statistics(role=current_user.role)
    return SuccessResponse(
        message="项目统计数据获取成功",
        data=result
    )


@router.get("/admin/payment-statistics", response_model=SuccessResponse)
async def get_payment_statistics_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取支付统计数据"""
    result = await analytic_service.get_payment_statistics(role=current_user.role)
    return SuccessResponse(
        message="支付统计数据获取成功",
        data=result
    )


@router.get("/admin/top-ten-revenue-projects", response_model=SuccessResponse)
async def get_top_ten_revenue_projects_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取收入最高的前十项目"""
    result = await analytic_service.get_top_ten_revenue_projects(role=current_user.role)
    return SuccessResponse(
        message="收入最高的前十项目数据获取成功",
        data=result
    )


@router.get("/admin/user-statistics", response_model=SuccessResponse)
async def get_user_statistics_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取用户统计数据"""
    result = await analytic_service.get_user_statistics(role=current_user.role)
    return SuccessResponse(
        message="用户统计数据获取成功",
        data=result
    )


@router.get("/admin/media-statistics", response_model=SuccessResponse)
async def get_media_statistics_router(
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取媒体文件统计"""
    result = await analytic_service.get_media_statistics(role=current_user.role)
    return SuccessResponse(
        message="媒体文件统计数据获取成功",
        data=result
    )


@router.get("/admin/growth-trends", response_model=SuccessResponse)
async def get_growth_trends_router(
    days: int = Query(default=30, ge=1, le=365),
    analytic_service: AnalyticService = Depends(get_analytic_service),
    current_user=Depends(get_current_user_dependency),
):
    """获取增长趋势数据"""
    result = await analytic_service.get_growth_trends(role=current_user.role, days=days)
    return SuccessResponse(
        message="增长趋势数据获取成功",
        data=result
    )
