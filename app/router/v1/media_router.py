import os
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    Response,
)
from fastapi.responses import FileResponse
from typing import List, Optional
from fastapi import Query
from app.models.media_model import MediaType
from app.services.media_service import get_media_service, MediaService
from app.schemas.common import SuccessResponse
from app.schemas.media_schemas import DeleteMediaRequest
from app.core.logger import logger_manager
from app.router.v1.auth_router import get_current_user_dependency
from app.utils.offset_pagination import offset_paginator
from app.utils.pagination_headers import set_pagination_headers
from app.core.i18n.i18n import get_language, get_message, Language

logger = logger_manager.get_logger(__name__)

# 创建媒体路由
router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/admin/get-media-lists", response_model=SuccessResponse)
async def get_media_lists_router(
    response: Response,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    current_user=Depends(get_current_user_dependency),
    media_service: MediaService = Depends(get_media_service),
    language: Language = Depends(get_language),
    media_type: Optional[MediaType] = Query(None, description="媒体类型"),
):
    """
    获取媒体列表
    """
    items, pagination_metadata = await media_service.get_media_lists(
        user_id=current_user.id,
        page=page,
        size=size,
        language=language,
        media_type=media_type,
    )
    set_pagination_headers(response, pagination_metadata)
    return SuccessResponse(
        message=get_message("media.getMediaLists", language),
        data=offset_paginator.create_response_data(items, pagination_metadata),
    )


@router.post("/admin/upload-media", response_model=SuccessResponse)
async def upload_router(
    files: List[UploadFile] = File(...),
    current_user=Depends(get_current_user_dependency),
    media_service: MediaService = Depends(get_media_service),
    language: Language = Depends(get_language),
):
    """
    批量上传媒体文件

    Args:
        files: 要上传的多个文件
        current_user: 当前用户

    Returns:
        上传结果（批量）
    """
    try:
        if not files:
            raise HTTPException(
                status_code=400,
                detail=get_message("media.uploadMedia", language),
            )

        # 处理上传文件（验证、保存到临时文件）
        temp_paths = await media_service.process_upload_files(files)

        try:
            # 上传到S3
            if len(temp_paths) == 1:
                result = await media_service.upload_single_media_to_s3(
                    local_file_path=temp_paths[0],
                    user_id=current_user.id,
                    is_avatar=False,
                    language=language,
                )
            else:
                result = await media_service.upload_multiple_media_to_s3(
                    local_file_paths=temp_paths,
                    user_id=current_user.id,
                    is_avatar=False,
                    language=language,
                )

            zh_message = (
                "上传完成"
                if len(temp_paths) == 1
                else (
                    "批量文件上传完成"
                    if result.get("failed", 0) == 0
                    else f"批量文件上传完成，{result.get('failed', 0)} 个文件失败"
                )
            )
            en_message = (
                "Upload completed"
                if len(temp_paths) == 1
                else (
                    "Batch file upload completed"
                    if result.get("failed", 0) == 0
                    else f"Batch file upload completed, {result.get('failed', 0)} files failed"
                )
            )

            return SuccessResponse(
                message=zh_message if language == Language.ZH_CN else en_message,
                data=result,
            )

        finally:
            # 清理临时文件
            for path in temp_paths:
                try:
                    os.unlink(path)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量上传异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="批量上传失败"
        )


@router.get("/admin/download-media")
async def download_router(
    media_id: int,
    current_user=Depends(get_current_user_dependency),
    media_service: MediaService = Depends(get_media_service),
    language: Language = Depends(get_language),
):
    """
    下载源媒体文件

    简化参数，只使用media_id，提升性能和安全性

    Args:
        media_id: 媒体ID
        current_user: 当前用户

    Returns:
        文件下载响应
    """
    try:
        # 调用服务层下载媒体文件
        local_file_path = await media_service.download_media_from_s3(
            media_id=media_id,
            language=language,
        )

        # 获取文件名
        file_name = Path(local_file_path).name

        # 记录下载操作日志
        logger.info(
            f"用户 {current_user.id} 下载媒体文件: "
            f"media_id={media_id}, "
            f"本地路径={local_file_path}"
        )

        # 返回文件下载响应
        return FileResponse(
            path=local_file_path,
            filename=file_name,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载媒体文件异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="下载媒体文件失败"
        )


@router.delete("/admin/delete-media", response_model=SuccessResponse)
async def delete_router(
    delete_request: DeleteMediaRequest,
    current_user=Depends(get_current_user_dependency),
    media_service: MediaService = Depends(get_media_service),
    language: Language = Depends(get_language),
):
    """
    删除媒体文件，支持单个或多个文件删除

    简化参数，只使用media_ids，提升性能和安全性

    Args:
        delete_request: 删除请求，包含媒体ID
        current_user: 当前用户

    Returns:
        删除结果详情
    """
    try:
        # 调用服务层删除媒体文件
        result = await media_service.delete_media_from_s3(
            media_ids=delete_request.media_ids,
            user_id=current_user.id,
            language=language,
        )

        # 记录删除操作日志
        logger.info(
            f"用户 {current_user.id} 删除媒体文件: "
            f"media_ids={delete_request.media_ids}, "
            f"结果={result}"
        )

        return SuccessResponse(
            message=result.get("message", "删除媒体文件完成"), data=result
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"删除媒体文件参数验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"参数验证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"删除媒体文件异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除媒体文件失败"
        )
