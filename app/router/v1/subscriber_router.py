from fastapi import APIRouter, Depends, Response, Query
from app.schemas.common import SuccessResponse
from app.services.subscriber_service import get_subscriber_service, SubscriberService
from app.schemas.auth_schemas import EmailSchema
from app.utils.offset_pagination import offset_paginator
from app.utils.pagination_headers import set_pagination_headers
from app.core.i18n.i18n import get_message


router = APIRouter(prefix="/subscriber", tags=["Subscriber"])


@router.get("/admin/get-subscriber-lists", response_model=SuccessResponse)
async def get_subscriber_lists_router(
    response: Response,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(100, ge=1, le=1000, description="每页数量，最大1000"),
    subscriber_service: SubscriberService = Depends(get_subscriber_service),
):
    """获取订阅者列表 - 使用传统分页方式"""

    items, pagination_metadata = await subscriber_service.get_subscriber_lists(
        page=page,
        size=size,
    )

    # 在响应头中添加分页信息
    set_pagination_headers(response, pagination_metadata)

    return SuccessResponse(
        message=get_message("subscriber.getSubscriberLists"),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.post("/create-subscriber", response_model=SuccessResponse)
async def create_subscriber_router(
    form_data: EmailSchema,
    subscriber_service: SubscriberService = Depends(get_subscriber_service),
):
    """创建订阅者"""

    result = await subscriber_service.create_subscriber(email=form_data.email)
    return SuccessResponse(
        message=get_message("subscriber.createSubscriber"),
        data=result,
    )


@router.post("/unsubscribe-subscriber", response_model=SuccessResponse)
async def unsubscribe_subscriber_router(
    form_data: EmailSchema,
    subscriber_service: SubscriberService = Depends(get_subscriber_service),
):
    """取消订阅者"""

    result = await subscriber_service.unsubscribe_subscriber(email=form_data.email)
    return SuccessResponse(
        message=get_message("subscriber.unsubscribeSubscriber"),
        data=result,
    )
