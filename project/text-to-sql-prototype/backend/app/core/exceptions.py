"""Application exceptions and error handlers."""
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, **(details or {})},
        )


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(
        self,
        message: str = "Validation error",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": field, **(details or {})},
        )


class AuthenticationException(AppException):
    """Authentication error exception."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details or {},
        )


class AuthorizationException(AppException):
    """Authorization error exception (403 Forbidden)."""

    def __init__(
        self,
        message: str = "Permission denied",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {},
        )


class ConflictException(AppException):
    """Resource conflict exception (409 Conflict)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details or {},
        )


def create_error_response(
    message: str,
    code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create standardized error response.

    Args:
        message: Error message
        code: Error code
        details: Additional error details

    Returns:
        Standardized error response dict
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


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.message,
            code=exc.code,
            details=exc.details,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: ValidationException
) -> JSONResponse:
    """Handle validation exceptions."""
    return await app_exception_handler(request, exc)


async def not_found_exception_handler(
    request: Request, exc: NotFoundException
) -> JSONResponse:
    """Handle not found exceptions."""
    return await app_exception_handler(request, exc)


async def authentication_exception_handler(
    request: Request, exc: AuthenticationException
) -> JSONResponse:
    """Handle authentication exceptions."""
    return await app_exception_handler(request, exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            message="An unexpected error occurred",
            code="INTERNAL_SERVER_ERROR",
            details={"error": str(exc)} if isinstance(exc, Exception) else {},
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with FastAPI app.

    Args:
        app: FastAPI application instance

    Usage:
        from fastapi import FastAPI
        from app.core.exceptions import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
    """
    # Register application exception handler
    app.add_exception_handler(AppException, app_exception_handler)

    # Register specific exception handlers
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(AuthenticationException, authentication_exception_handler)

    # Register generic exception handler as catch-all
    app.add_exception_handler(Exception, generic_exception_handler)
