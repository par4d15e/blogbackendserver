from fastapi import APIRouter, Depends
from app.schemas.section_schemas import UpdateSectionRequest
from app.schemas.common import SuccessResponse
from app.core.i18n.i18n import get_message
from app.router.v1.auth_router import get_current_user_dependency
from app.services.section_service import get_section_service, SectionService

router = APIRouter(prefix="/section", tags=["Section"])


@router.get("/get-section-lists", response_model=SuccessResponse)
async def get_section_lists_router(
    section_service: SectionService = Depends(get_section_service),
):
    result = await section_service.get_section_lists()
    return SuccessResponse(
        message=get_message("section.getSectionLists"),
        data=result,
    )


@router.get("/get-section-seo-by-slug/{slug}", response_model=SuccessResponse)
async def get_section_seo_by_slug_router(
    slug: str,
    section_service: SectionService = Depends(get_section_service),
):
    result = await section_service.get_section_seo_by_slug(slug)
    return SuccessResponse(
        message=get_message("section.getSectionSeoBySlug"),
        data=result,
    )


@router.get("/get-section-details-by-slug/{slug}", response_model=SuccessResponse)
async def get_section_details_by_slug_router(
    slug: str,
    section_service: SectionService = Depends(get_section_service),
):
    result = await section_service.get_section_details_by_slug(slug)
    return SuccessResponse(
        message=get_message("section.getSectionDetailsBySlug"),
        data=result,
    )


@router.patch("/admin/update-section", response_model=SuccessResponse)
async def update_section_router(
    form_data: UpdateSectionRequest,
    current_user=Depends(get_current_user_dependency),
    section_service: SectionService = Depends(get_section_service),
):
    result = await section_service.update_section(
        section_id=form_data.section_id,
        seo_id=form_data.seo_id,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        role=current_user.role,
        
        is_active=form_data.is_active,
    )
    return SuccessResponse(
        message=get_message("section.updateSection"),
        data=result,
    )
