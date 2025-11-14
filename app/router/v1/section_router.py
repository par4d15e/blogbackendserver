from fastapi import APIRouter, Depends
from app.schemas.section_schemas import UpdateSectionRequest
from app.schemas.common import SuccessResponse
from app.core.i18n.i18n import get_message, get_language, Language
from app.router.v1.auth_router import get_current_user_dependency
from app.services.section_service import get_section_service, SectionService

router = APIRouter(prefix="/section", tags=["Section"])


@router.get("/get-section-lists", response_model=SuccessResponse)
async def get_section_lists_router(
    language: Language = Depends(get_language),
    section_service: SectionService = Depends(get_section_service),
):
    result = await section_service.get_section_lists(language=language)
    return SuccessResponse(
        message=get_message("section.getSectionLists", language),
        data=result,
    )


@router.get("/get-section-seo-by-slug/{slug}", response_model=SuccessResponse)
async def get_section_seo_by_slug_router(
    slug: str,
    section_service: SectionService = Depends(get_section_service),
    language: Language = Depends(get_language),
):
    result = await section_service.get_section_seo_by_slug(slug, language)
    return SuccessResponse(
        message=get_message("section.getSectionSeoBySlug", language),
        data=result,
    )


@router.get("/get-section-details-by-slug/{slug}", response_model=SuccessResponse)
async def get_section_details_by_slug_router(
    slug: str,
    language: Language = Depends(get_language),
    section_service: SectionService = Depends(get_section_service),
):
    result = await section_service.get_section_details_by_slug(slug, language)
    return SuccessResponse(
        message=get_message("section.getSectionDetailsBySlug", language),
        data=result,
    )


@router.patch("/admin/update-section", response_model=SuccessResponse)
async def update_section_router(
    form_data: UpdateSectionRequest,
    current_user=Depends(get_current_user_dependency),
    section_service: SectionService = Depends(get_section_service),
    language: Language = Depends(get_language),
):
    result = await section_service.update_section(
        section_id=form_data.section_id,
        seo_id=form_data.seo_id,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        role=current_user.role,
        language=language,
        is_active=form_data.is_active,
    )
    return SuccessResponse(
        message=get_message("section.updateSection", language),
        data=result,
    )
