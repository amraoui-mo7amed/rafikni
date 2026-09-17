"""
Common Pydantic Schemas for Rafikni API.
Defines standard response envelopes and pagination metadata.
"""

from typing import Generic, List, Optional, TypeVar, Any
from ninja import Schema

T = TypeVar("T")


class ApiResponseSchema(Schema, Generic[T]):
    """Standard unified response envelope for all endpoints."""
    success: bool = True
    message: str = "تمت العملية بنجاح"
    errors: List[str] = []
    data: Optional[T] = None


class PaginationMetaSchema(Schema):
    """Metadata for paginated list endpoints."""
    page: int
    num_pages: int
    total_count: int
    has_next: bool = False
    has_prev: bool = False


class PaginatedDataSchema(Schema, Generic[T]):
    """Generic payload schema containing items list and pagination metadata."""
    items: List[T]
    pagination: PaginationMetaSchema
