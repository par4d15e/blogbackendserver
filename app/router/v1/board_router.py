from fastapi import APIRouter, Depends, Query
from app.schemas.board_schemas import (
    BoardUpdateRequest,
    BoardCommentCreateRequest,
    BoardCommentUpdateRequest,
)
from app.schemas.common import SuccessResponse
from app.router.v1.auth_router import get_current_user_dependency
from app.services.board_service import get_board_service, BoardService
from app.core.i18n.i18n import get_message, get_language, Language


router = APIRouter(prefix="/board", tags=["Board"])


@router.get("/get-board-details", response_model=SuccessResponse)
async def get_board_details_router(
    board_service: BoardService = Depends(get_board_service),
    language: Language = Depends(get_language),
):
    result = await board_service.get_board_details(language=language)
    return SuccessResponse(
        message=get_message("board.getBoardDetails", language),
        data=result,
    )


@router.patch("/admin/update-board", response_model=SuccessResponse)
async def update_board_router(
    form_data: BoardUpdateRequest,
    current_user=Depends(get_current_user_dependency),
    board_service: BoardService = Depends(get_board_service),
    language: Language = Depends(get_language),
):
    result = await board_service.update_board(
        board_id=form_data.board_id,
        role=current_user.role,
        chinese_title=form_data.chinese_title,
        chinese_description=form_data.chinese_description,
        language=language,
    )
    return SuccessResponse(
        message=get_message("board.updateBoard", language),
        data=result,
    )


@router.post("/create-board-comment", response_model=SuccessResponse)
async def create_board_comment_router(
    form_data: BoardCommentCreateRequest,
    current_user=Depends(get_current_user_dependency),
    board_service: BoardService = Depends(get_board_service),
    language: Language = Depends(get_language),
):
    """创建留言板评论"""
    result = await board_service.create_board_comment(
        board_id=form_data.board_id,
        user_id=current_user.id,
        parent_id=form_data.parent_id,
        comment=form_data.comment,
        language=language,
    )
    return SuccessResponse(
        message=get_message(
            "board.createBoardComment.createBoardCommentSuccess", language
        ),
        data=result,
    )


@router.get("/get-board-comment-lists/{board_id}", response_model=SuccessResponse)
async def get_board_comment_lists_router(
    board_id: int,
    limit: int = Query(10, ge=1, le=100),
    cursor: str | None = Query(None),
    board_service: BoardService = Depends(get_board_service),
    language: Language = Depends(get_language),
):
    """获取留言板评论列表 - 使用 keyset pagination"""
    result = await board_service.get_board_comment_lists(
        board_id=board_id, limit=limit, cursor=cursor, language=language
    )

    return SuccessResponse(
        message=get_message("board.getBoardCommentLists", language),
        data=result,
    )


@router.patch("/update-board-comment", response_model=SuccessResponse)
async def update_board_comment_router(
    form_data: BoardCommentUpdateRequest,
    current_user=Depends(get_current_user_dependency),
    board_service: BoardService = Depends(get_board_service),
    language: Language = Depends(get_language),
):
    result = await board_service.update_board_comment(
        user_id=current_user.id,
        board_comment_id=form_data.board_comment_id,
        comment=form_data.comment,
        language=language,
    )
    return SuccessResponse(
        message=get_message("board.updateBoardComment", language),
        data=result,
    )


@router.delete(
    "/delete-board-comment/{board_comment_id}", response_model=SuccessResponse
)
async def delete_board_comment_router(
    board_comment_id: int,
    current_user=Depends(get_current_user_dependency),
    board_service: BoardService = Depends(get_board_service),
    language: Language = Depends(get_language),
):
    result = await board_service.delete_board_comment(
        user_id=current_user.id,
        role=current_user.role,
        board_comment_id=board_comment_id,
        language=language,
    )
    return SuccessResponse(
        message=get_message("board.deleteBoardComment", language),
        data=result,
    )
