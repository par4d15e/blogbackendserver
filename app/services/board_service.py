from fastapi import Depends
from typing import Dict, Any, Optional
from app.crud.board_crud import BoardCrud, get_board_crud
from app.models.user_model import RoleType
from app.core.i18n.i18n import Language


class BoardService:
    def __init__(self, board_crud: BoardCrud):
        self.board_crud = board_crud

    async def get_board_details(
        self,
        language: str,
    ) -> Dict[str, any]:
        return await self.board_crud.get_board_details(language=language)

    async def update_board(
        self,
        board_id: int,
        role: RoleType,
        chinese_title: str,
        chinese_description: str,
        language: Language,
    ) -> bool:
        return await self.board_crud.update_board(
            board_id=board_id,
            role=role,
            chinese_title=chinese_title,
            chinese_description=chinese_description,
            language=language,
        )

    async def create_board_comment(
        self,
        board_id: int,
        user_id: int,
        parent_id: Optional[int],
        comment: str,
        language: Language,
    ) -> bool:
        return await self.board_crud.create_board_comment(
            board_id=board_id,
            user_id=user_id,
            parent_id=parent_id,
            comment=comment,
            language=language,
        )

    async def get_board_comment_lists(
        self,
        board_id: int,
        language: Language,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self.board_crud.get_board_comment_lists(
            board_id=board_id, limit=limit, cursor=cursor, language=language
        )

    async def update_board_comment(
        self,
        user_id: int,
        board_comment_id: int,
        comment: str,
        language: Language,
    ) -> bool:
        return await self.board_crud.update_board_comment(
            user_id=user_id,
            board_comment_id=board_comment_id,
            comment=comment,
            language=language,
        )

    async def delete_board_comment(
        self,
        user_id: int,
        role: RoleType,
        board_comment_id: int,
        language: Language,
    ) -> bool:
        return await self.board_crud.delete_board_comment(
            user_id=user_id, board_comment_id=board_comment_id, language=language,
            role=role,
        )


def get_board_service(
    board_crud: BoardCrud = Depends(get_board_crud),
) -> BoardService:
    return BoardService(board_crud=board_crud)
