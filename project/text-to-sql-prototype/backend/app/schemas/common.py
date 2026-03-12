"""Common schemas for request and response validation."""
from typing import Generic, TypeVar, List

from pydantic import BaseModel


class PaginationInfo(BaseModel):
    """Pagination information."""
    total: int
    total_pages: int


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with list and pagination info."""
    list: List[T]
    pagination: PaginationInfo

    class Config:
        """Pydantic configuration."""
        from_attributes = True
