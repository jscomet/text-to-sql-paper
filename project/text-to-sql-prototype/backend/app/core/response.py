"""Standardized response utilities."""
from typing import Any, Dict, Generic, Optional, TypeVar, Union

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    """Standard API response schema.

    Attributes:
        code: Response code ("SUCCESS" for success, error code for errors)
        message: Response message
        data: Response data (generic type)
        error: Error details (only present for error responses)
    """

    code: str = Field(default="SUCCESS", description="Response code")
    message: str = Field(default="Success", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "SUCCESS",
                "message": "Success",
                "data": {},
                "error": None,
            }
        }


class PaginationSchema(BaseModel, Generic[T]):
    """Pagination data schema.

    Attributes:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        total_pages: Total number of pages
    """

    items: list[T] = Field(default_factory=list, description="List of items")
    total: int = Field(default=0, description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Number of items per page")
    total_pages: int = Field(default=0, description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
                "total_pages": 0,
            }
        }


def success_response(
    data: Any = None,
    message: str = "Success",
    code: str = "SUCCESS",
) -> Dict[str, Any]:
    """Create a standardized success response.

    Args:
        data: Response data (any type)
        message: Success message
        code: Success code

    Returns:
        Standardized success response dict

    Example:
        >>> success_response(data={"id": 1}, message="User created")
        {"code": "SUCCESS", "message": "User created", "data": {"id": 1}, "error": None}
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "error": None,
    }


def error_response(
    message: str = "An error occurred",
    code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        message: Error message
        code: Error code
        details: Additional error details

    Returns:
        Standardized error response dict

    Example:
        >>> error_response(message="Invalid input", code="VALIDATION_ERROR")
        {
            "code": "VALIDATION_ERROR",
            "message": "Invalid input",
            "data": None,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid input", "details": {}}
        }
    """
    return {
        "code": code,
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Success",
) -> Dict[str, Any]:
    """Create a standardized paginated response.

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        message: Success message

    Returns:
        Standardized paginated response dict

    Example:
        >>> paginated_response(items=[{"id": 1}], total=100, page=1, page_size=10)
        {
            "code": "SUCCESS",
            "message": "Success",
            "data": {
                "items": [{"id": 1}],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10
            },
            "error": None
        }
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
        message=message,
    )


def created_response(
    data: Any = None,
    message: str = "Resource created successfully",
) -> Dict[str, Any]:
    """Create a standardized created response.

    Args:
        data: Created resource data
        message: Success message

    Returns:
        Standardized created response dict
    """
    return success_response(data=data, message=message, code="CREATED")


def updated_response(
    data: Any = None,
    message: str = "Resource updated successfully",
) -> Dict[str, Any]:
    """Create a standardized updated response.

    Args:
        data: Updated resource data
        message: Success message

    Returns:
        Standardized updated response dict
    """
    return success_response(data=data, message=message, code="UPDATED")


def deleted_response(
    data: Any = None,
    message: str = "Resource deleted successfully",
) -> Dict[str, Any]:
    """Create a standardized deleted response.

    Args:
        data: Deleted resource data (optional)
        message: Success message

    Returns:
        Standardized deleted response dict
    """
    return success_response(data=data, message=message, code="DELETED")
