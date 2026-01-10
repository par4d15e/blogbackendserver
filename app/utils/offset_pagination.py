from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.i18n.i18n import Language, get_message


class OffsetPaginator:
    """
    Traditional page-based pagination helper:
    - Uses page number and page size for pagination
    - Provides total count, total pages, and pagination metadata
    - Supports ordering and filtering
    """

    def __init__(self, default_page_size: int = 20, max_page_size: int = 100):
        """
        Initialize the paginator.

        Args:
            default_page_size: Default page size if not specified
            max_page_size: Maximum allowed page size
        """
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size

    def validate_pagination_params(self, page: int, size: int) -> Tuple[int, int]:
        """
        Validate and normalize pagination parameters.

        Args:
            page: Page number (1-based)
            size: Page size

        Returns:
            Tuple of (normalized_page, normalized_size)

        Raises:
            ValueError: If parameters are invalid
        """
        if page < 1:
            raise ValueError("Page number must be greater than 0")

        if size < 1:
            size = self.default_page_size
        elif size > self.max_page_size:
            size = self.max_page_size

        return page, size

    def calculate_offset(self, page: int, size: int) -> int:
        """
        Calculate the offset for SQL LIMIT/OFFSET.

        Args:
            page: Page number (1-based)
            size: Page size

        Returns:
            Offset value for SQL query
        """
        return (page - 1) * size

    def apply_pagination(self, stmt: Any, page: int, size: int) -> Any:
        """
        Apply pagination to a SQLModel/SQLAlchemy statement.

        Args:
            stmt: SQLModel/SQLAlchemy statement
            page: Page number (1-based)
            size: Page size

        Returns:
            Paginated statement
        """
        page, size = self.validate_pagination_params(page, size)
        offset = self.calculate_offset(page, size)

        return stmt.offset(offset).limit(size)

    def create_pagination_metadata(
        self, total_count: int, page: int, size: int
    ) -> Dict[str, Any]:
        """
        Create pagination metadata.

        Args:
            total_count: Total number of items
            page: Current page number
            size: Page size

        Returns:
            Dictionary containing pagination metadata
        """
        page, size = self.validate_pagination_params(page, size)

        total_pages = (total_count + size - 1) // size if total_count > 0 else 0

        return {
            "current_page": page,
            "page_size": size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "start_index": (page - 1) * size + 1 if total_count > 0 else 0,
            "end_index": min(page * size, total_count),
        }

    async def get_paginated_result(
        self,
        db: AsyncSession,
        model_class: Any,
        page: int = 1,
        size: int = 20,
        order_by: Optional[List[Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        join_options: Optional[List[Any]] = None,
        language: Language = Language.EN_US,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Get paginated result with metadata.

        Args:
            db: Database session
            model_class: SQLModel class
            page: Page number (1-based)
            size: Page size
            order_by: List of ordering expressions
            filters: Dictionary of filters to apply
            join_options: List of join options (e.g., lazyload, joinedload)

        Returns:
            Tuple of (items, pagination_metadata)
        """
        # Validate parameters
        page, size = self.validate_pagination_params(page, size)

        # Build base query
        stmt = select(model_class)

        # Apply join options
        if join_options:
            for option in join_options:
                stmt = stmt.options(option)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(model_class, field) and value is not None:
                    if isinstance(value, (list, tuple)):
                        stmt = stmt.where(getattr(model_class, field).in_(value))
                    else:
                        stmt = stmt.where(getattr(model_class, field) == value)

        # Get total count
        count_stmt = select(func.count(model_class.id))
        if filters:
            for field, value in filters.items():
                if hasattr(model_class, field) and value is not None:
                    if isinstance(value, (list, tuple)):
                        count_stmt = count_stmt.where(
                            getattr(model_class, field).in_(value)
                        )
                    else:
                        count_stmt = count_stmt.where(
                            getattr(model_class, field) == value
                        )

        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar()
        if total_count == 0:
            raise HTTPException(
                status_code=404,
                detail=get_message("common.noDataFound", language),
            )

        # Apply ordering
        if order_by:
            stmt = stmt.order_by(*order_by)
        else:
            # Default ordering by id desc
            stmt = stmt.order_by(model_class.id.desc())

        # Apply pagination
        stmt = self.apply_pagination(stmt, page, size)

        # Execute query
        result = await db.execute(stmt)
        items = result.scalars().all()

        # Create pagination metadata
        pagination_metadata = self.create_pagination_metadata(total_count, page, size)

        return items, pagination_metadata

    async def get_paginated_join_result(
        self,
        db: AsyncSession,
        base_stmt: Any,
        count_stmt: Any,
        page: int = 1,
        size: int = 20,
        order_by: Optional[List[Any]] = None,
        language: Language = Language.EN_US,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Get paginated result for complex JOIN queries.

        Args:
            db: Database session
            base_stmt: Base SELECT statement with JOINs
            count_stmt: COUNT statement for total count
            page: Page number (1-based)
            size: Page size
            order_by: List of ordering expressions

        Returns:
            Tuple of (items, pagination_metadata)
        """
        # Validate parameters
        page, size = self.validate_pagination_params(page, size)

        # Get total count
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar()

        if total_count == 0:
            raise HTTPException(
                status_code=404,
                detail=get_message("common.noDataFound", language),
            )

        # Apply ordering
        if order_by:
            base_stmt = base_stmt.order_by(*order_by)

        # Apply pagination
        base_stmt = self.apply_pagination(base_stmt, page, size)

        # Execute query
        result = await db.execute(base_stmt)
        items = result.all()  # Use .all() instead of .scalars().all() for JOIN results

        # Create pagination metadata
        pagination_metadata = self.create_pagination_metadata(total_count, page, size)

        return items, pagination_metadata

    def create_response_data(
        self, items: List[Any], pagination_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create standardized response data structure.

        Args:
            items: List of items
            pagination_metadata: Pagination metadata

        Returns:
            Dictionary with items and pagination info
        """
        return {
            "pagination": pagination_metadata,
            "items": items,
        }


# Create default instance for convenience
offset_paginator = OffsetPaginator()
