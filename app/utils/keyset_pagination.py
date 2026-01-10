import base64
from datetime import datetime
from typing import Optional, Tuple, Any, List, Dict, cast
from sqlmodel import and_, or_


class KeysetPaginator:
    """
    Keyset pagination helper with integrated cursor encoding/decoding:
    - asc=False: paginate by (created_at DESC, id DESC) using '<' comparisons
    - asc=True:  paginate by (created_at ASC,  id ASC)  using '>' comparisons
    """

    def __init__(self, asc: bool = False, delimiter: str = "|") -> None:
        """
        Initialize the paginator.

        Args:
            asc: Whether to paginate in ascending order
            delimiter: Delimiter used in cursor encoding (default: "|")
        """
        self.asc = asc
        self.delimiter = delimiter

    def decode_cursor(
        self, cursor: Optional[str]
    ) -> Tuple[Optional[datetime], Optional[int]]:
        """
        Decode a base64 cursor string to (created_at, id) tuple.

        Args:
            cursor: Base64 encoded cursor string

        Returns:
            Tuple of (created_at, id) or (None, None) if invalid
        """
        if not cursor:
            return None, None
        try:
            raw = base64.urlsafe_b64decode(cursor.encode()).decode()
            created_at_str, id_str = raw.split(self.delimiter, 1)
            return datetime.fromisoformat(created_at_str), int(id_str)
        except (ValueError, AttributeError, UnicodeDecodeError):
            return None, None

    def encode_cursor(self, created_at: datetime, row_id: int) -> str:
        """
        Encode (created_at, id) tuple to base64 cursor string.

        Args:
            created_at: Creation timestamp
            row_id: Row ID

        Returns:
            Base64 encoded cursor string
        """
        raw_cursor = f"{created_at.isoformat()}{self.delimiter}{row_id}"
        return base64.urlsafe_b64encode(raw_cursor.encode()).decode()

    def apply_filters(
        self, stmt: Any, created_at_col: Any, id_col: Any, cursor: Optional[str]
    ) -> Any:
        """
        Apply keyset WHERE filters based on a base64 cursor string.

        Args:
            stmt: SQLModel/SQLAlchemy statement to filter
            created_at_col: Column reference for created_at
            id_col: Column reference for id
            cursor: Base64 encoded cursor string

        Returns:
            Filtered statement
        """
        created_at_val, id_val = self.decode_cursor(cursor)
        if created_at_val is None or id_val is None:
            return stmt

        if self.asc:
            return stmt.where(
                or_(
                    created_at_col > created_at_val,
                    and_(created_at_col == created_at_val, id_col > id_val),
                )
            )
        else:
            return stmt.where(
                or_(
                    created_at_col < created_at_val,
                    and_(created_at_col == created_at_val, id_col < id_val),
                )
            )

    def order_by(self, created_at_col: Any, id_col: Any) -> List[Any]:
        """
        Return an ordering list compatible with SQLModel/SQLAlchemy's order_by(*cols).

        Args:
            created_at_col: Column reference for created_at
            id_col: Column reference for id

        Returns:
            List of ordering expressions
        """
        if self.asc:
            return [created_at_col.asc(), id_col.asc()]
        return [created_at_col.desc(), id_col.desc()]

    def create_response_data(
        self,
        items: List[Any],
        limit: int,
        has_next: bool = False,
        next_cursor: Optional[str] = None,
        prev_cursor: Optional[str] = None,
        items_key: str = "items",
    ) -> Dict[str, Any]:
        """
        Create standardized keyset pagination response data structure.

        Args:
            items: List of items
            limit: Maximum number of items per page
            has_next: Whether there are more items available
            next_cursor: Cursor for the next page
            prev_cursor: Cursor for the previous page
            items_key: Key name for the items in response (default: "items", can be "comments", etc.)

        Returns:
            Dictionary with items and keyset pagination info
        """
        response = {
            "pagination": {
                "has_next": has_next,
                "has_prev": prev_cursor is not None,
                "limit": limit,
                "next_cursor": next_cursor,
                "prev_cursor": prev_cursor,
                "count": len(items),
            },
            items_key: items,
        }

        # 如果 prev_cursor 为 None，从响应中移除该字段以保持简洁
        if prev_cursor is None:
            cast(Dict[str, Any], response["pagination"]).pop(
                "prev_cursor", None)

        return response

    # Convenience methods for backward compatibility
    def decode(self, cursor: Optional[str]) -> Tuple[Optional[datetime], Optional[int]]:
        """Alias for decode_cursor for backward compatibility."""
        return self.decode_cursor(cursor)

    def encode(self, created_at: datetime, row_id: int) -> str:
        """Alias for encode_cursor for backward compatibility."""
        return self.encode_cursor(created_at, row_id)


# Create default instances for convenience
paginator_asc = KeysetPaginator(asc=True)
paginator_desc = KeysetPaginator(asc=False)
