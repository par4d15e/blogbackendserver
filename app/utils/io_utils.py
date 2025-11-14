import tempfile
from pathlib import Path
from typing import Union, List
from app.utils.s3_bucket import create_s3_bucket
from app.core.logger import logger_manager


logger = logger_manager.get_logger(__name__)


def download_inputs_if_needed(
    input_paths: Union[str, Path, List[Union[str, Path]]],
) -> List[Path]:
    """Ensure all inputs are local files. Download from S3 if a path is an S3 key.

    Returns a list of local file Paths.
    """
    if isinstance(input_paths, (str, Path)):
        candidates = [Path(input_paths)]
    else:
        candidates = [Path(p) for p in input_paths]

    local_files: List[Path] = []
    temp_dir = Path(tempfile.mkdtemp(prefix="media_task_in_"))

    with create_s3_bucket() as s3_bucket:
        for candidate in candidates:
            if candidate.is_file():
                local_files.append(candidate)
                continue

            # Treat as S3 key and download
            s3_key = str(candidate)
            local_path = temp_dir / Path(s3_key).name
            try:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                if s3_bucket.download_file(
                    s3_key=s3_key, local_file_path=str(local_path)
                ):
                    local_files.append(local_path)
                else:
                    logger.warning(f"S3下载失败，跳过: {s3_key}")
            except Exception as e:
                logger.error(f"下载S3文件失败: {s3_key}, 错误: {e}")

    return local_files
