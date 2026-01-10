from typing import Dict, Any, List, Tuple
from fastapi import Depends
from app.crud.subscriber_crud import get_subscriber_crud, SubscriberCrud
from app.models.subscriber_model import Subscriber


class SubscriberService:
    def __init__(self, subscriber_crud: SubscriberCrud):
        self.subscriber_crud = subscriber_crud

    async def get_subscriber_lists(
        self, page: int = 1, size: int = 100
    ) -> Tuple[List[Subscriber], Dict[str, Any]]:
        """Get subscriber lists with traditional pagination"""
        items, pagination_metadata = await self.subscriber_crud.get_subscriber_lists(
            page=page, size=size
        )
        return items, pagination_metadata

    async def create_subscriber(self, email: str) -> Any:
        return await self.subscriber_crud.create_subscriber(email=email)

    async def unsubscribe_subscriber(self, email: str) -> Any:
        return await self.subscriber_crud.unsubscribe_subscriber(email=email)


def get_subscriber_service(
    subscriber_crud: SubscriberCrud = Depends(get_subscriber_crud),
) -> SubscriberService:
    return SubscriberService(subscriber_crud=subscriber_crud)
