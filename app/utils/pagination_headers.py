from fastapi import Response
from typing import Dict, Any


def set_pagination_headers(response: Response, pagination_metadata: Dict[str, Any]):
    """设置分页响应头"""
    response.headers["X-Total-Count"] = str(pagination_metadata["total_count"])
    response.headers["X-Total-Pages"] = str(pagination_metadata["total_pages"])
    response.headers["X-Current-Page"] = str(pagination_metadata["current_page"])
    response.headers["X-Page-Size"] = str(pagination_metadata["page_size"])
    response.headers["X-Has-Next"] = str(pagination_metadata["has_next"]).lower()
    response.headers["X-Has-Prev"] = str(pagination_metadata["has_prev"]).lower()
