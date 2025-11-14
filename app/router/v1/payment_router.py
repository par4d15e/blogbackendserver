from fastapi import APIRouter, Depends, Request, Query, Response
from app.schemas.common import SuccessResponse
from app.services.payment_service import PaymentService, get_payment_service
from app.schemas.payment_schemas import PaymentIntentRequest
from app.core.i18n.i18n import get_language, get_message, Language
from app.router.v1.auth_router import get_current_user_dependency
from app.utils.pagination_headers import set_pagination_headers
from app.utils.offset_pagination import offset_paginator

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/create-payment-intent")
async def create_payment_intent(
    form_data: PaymentIntentRequest,
    language: Language = Depends(get_language),
    current_user=Depends(get_current_user_dependency),
    payment_service: PaymentService = Depends(get_payment_service),
):
    client_secret = await payment_service.create_payment_intent(
        user_id=current_user.id,
        project_id=form_data.project_id,
        cover_url=form_data.cover_url,
        project_name=form_data.project_name,
        project_description=form_data.project_description,
        project_price=form_data.project_price,
        tax_name=form_data.tax_name,
        tax_rate=form_data.tax_rate,
        tax_amount=form_data.tax_amount,
        final_amount=form_data.final_amount,
        language=language,
    )
    return SuccessResponse(
        message=get_message("payment.createPaymentIntent", language),
        data={"client_secret": client_secret},
    )


@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    language: Language = Depends(get_language),
    payment_service: PaymentService = Depends(get_payment_service),
):
    await payment_service.stripe_webhook(request)
    return SuccessResponse(
        message=get_message("payment.stripeWebhook", language),
        data={"status": "success"},
    )


@router.get("/success-details", response_model=SuccessResponse)
async def get_payment_success_details_router(
    payment_intent: str = Query(..., description="Payment intent ID"),
    language: Language = Depends(get_language),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """获取支付成功的产品详情"""
    payment_details = await payment_service.get_payment_success_details(
        payment_intent_id=payment_intent,
        language=language,
    )

    return SuccessResponse(
        message=get_message("payment.paymentSuccess.getSuccessDetailsSuccess", language),
        data=payment_details,
    )


@router.get("/get-payment-records", response_model=SuccessResponse)
async def get_payment_record_router(
    response: Response,
    language: Language = Depends(get_language),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    current_user=Depends(get_current_user_dependency),
    payment_service: PaymentService = Depends(get_payment_service),
):
    items, pagination_metadata = await payment_service.get_payment_record(
        language=language,
        page=page,
        size=size,
        role=current_user.role,
        user_id=current_user.id,
    )

    # 在响应头中添加分页信息
    set_pagination_headers(response, pagination_metadata)

    return SuccessResponse(
        message=get_message("payment.getPaymentRecord", language),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )
