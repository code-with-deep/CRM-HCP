"""Application-wide exception types and FastAPI handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.schemas.responses import ApiErrorResponse, ResponseMeta

logger = get_logger(__name__)


class ErrorResponse(BaseModel):
    """Legacy API error response schema."""

    success: bool = False
    error: str
    detail: str | list[Any] | dict[str, Any] | None = None
    status_code: int


class AppException(Exception):
    """Base class for application-level exceptions."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str | list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


class ValidationException(AppException):
    """Raised when business validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        detail: str | list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        *,
        detail: str | list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DatabaseException(AppException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        *,
        detail: str | list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class LangGraphException(AppException):
    """Raised when LangGraph agent execution fails."""

    def __init__(
        self,
        message: str = "LangGraph agent execution failed",
        *,
        detail: str | list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


class LLMTimeoutException(AppException):
    """Raised when the LLM provider times out."""

    def __init__(
        self,
        message: str = "LLM request timed out",
        *,
        detail: str | list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=detail)


class ToolFailureException(AppException):
    """Raised when a LangGraph tool execution fails."""

    def __init__(
        self,
        message: str = "Tool execution failed",
        *,
        detail: str | list[Any] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


def _meta_from_request(request: Request) -> ResponseMeta:
    """Build response metadata from request context."""
    return ResponseMeta(
        request_id=getattr(request.state, "request_id", None),
        correlation_id=getattr(request.state, "correlation_id", None),
    )


def _build_error_response(
    request: Request,
    *,
    message: str,
    status_code: int,
    detail: str | list[Any] | dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> JSONResponse:
    error_list = errors or [message]
    payload = ApiErrorResponse(
        success=False,
        message=message,
        errors=error_list,
        meta=_meta_from_request(request),
    )
    content = payload.model_dump()
    if detail is not None:
        content["detail"] = detail
    return JSONResponse(status_code=status_code, content=content)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.warning("Application exception: %s", exc.message)
    return _build_error_response(
        request,
        message=exc.message,
        status_code=exc.status_code,
        detail=exc.detail,
        errors=[exc.message],
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle FastAPI/Pydantic request validation errors."""
    logger.warning("Validation error: %s", exc.errors())
    return _build_error_response(
        request,
        message="Validation error",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=exc.errors(),
        errors=["Request validation failed."],
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database exceptions."""
    logger.error("Database error: %s", str(exc), exc_info=exc)
    return _build_error_response(
        request,
        message="Database error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="A database error occurred while processing the request.",
        errors=["Database operation failed."],
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error("Unhandled exception: %s", str(exc), exc_info=exc)
    return _build_error_response(
        request,
        message="Internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred while processing the request.",
        errors=["An unexpected error occurred."],
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
