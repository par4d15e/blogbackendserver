from app.core.config.base import EnvBaseSettings
from typing import List
from pydantic import Field


class FilesSettings(EnvBaseSettings):
    # File size limits by type (in bytes)
    S3_IMAGE_MAX_SIZE: int = Field(default=10485760, description="10 MB")
    S3_VIDEO_MAX_SIZE: int = Field(default=1073741824, description="1 GB")
    S3_AUDIO_MAX_SIZE: int = Field(default=52428800, description="50 MB")
    S3_DOCUMENT_MAX_SIZE: int = Field(default=52428800, description="50 MB")
    S3_OTHER_MAX_SIZE: int = Field(default=524288000, description="500 MB")

    # S3 Media paths for original files
    S3_IMAGE_ORIGINAL_PATH: str = Field(
        default="original/images", description="S3 image original path"
    )
    S3_VIDEO_ORIGINAL_PATH: str = Field(
        default="original/videos", description="S3 video original path"
    )
    S3_AUDIO_ORIGINAL_PATH: str = Field(
        default="original/audios", description="S3 audio original path"
    )
    S3_DOCUMENT_ORIGINAL_PATH: str = Field(
        default="original/documents", description="S3 document original path"
    )
    S3_OTHER_ORIGINAL_PATH: str = Field(
        default="original/others", description="S3 other original path"
    )

    # S3 Media paths for thumbnails
    S3_IMAGE_THUMBNAIL_PATH: str = Field(
        default="thumbnails/images", description="S3 image thumbnail path"
    )
    S3_VIDEO_THUMBNAIL_PATH: str = Field(
        default="thumbnails/videos", description="S3 video thumbnail path"
    )

    # S3 Media paths for watermarked files
    S3_IMAGE_WATERMARK_PATH: str = Field(
        default="watermarked/images", description="S3 image watermark path"
    )
    S3_VIDEO_WATERMARK_PATH: str = Field(
        default="watermarked/videos", description="S3 video watermark path"
    )

    # S3 Media file extensions
    S3_IMAGE_EXTENSIONS: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif"], description="S3 image extensions"
    )
    S3_VIDEO_EXTENSIONS: List[str] = Field(
        default=["mp4", "avi", "mov", "mkv"], description="S3 video extensions"
    )
    S3_AUDIO_EXTENSIONS: List[str] = Field(
        default=["mp3", "wav", "aac"], description="S3 audio extensions"
    )
    S3_DOCUMENT_EXTENSIONS: List[str] = Field(
        default=["pdf", "docx", "xlsx", "ppt", "pptx", "txt"],
        description="S3 document extensions",
    )
    S3_OTHER_EXTENSIONS: List[str] = Field(
        default=["zip", "gz"], description="S3 other extensions"
    )
