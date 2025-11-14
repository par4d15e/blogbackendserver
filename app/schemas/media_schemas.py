from typing import Union, List
from pydantic import BaseModel, Field


class DeleteMediaRequest(BaseModel):
    """删除媒体文件请求模型 - 简化版本，只使用media_ids"""

    media_ids: Union[int, List[int]] = Field(
        ..., description="媒体ID，可以是单个ID或ID列表"
    )


class DownloadMediaRequest(BaseModel):
    """下载媒体文件请求模型 - 简化版本，只使用media_ids"""

    media_ids: Union[int, List[int]] = Field(
        ..., description="媒体ID，可以是单个ID或ID列表"
    )
