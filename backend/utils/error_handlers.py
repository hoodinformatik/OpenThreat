"""
Centralized error handling for OpenThreat API.

This module provides consistent error responses across all endpoints.
"""

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class OpenThreatException(Exception):
    """Base exception for OpenThreat application."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(OpenThreatException):
    """Database operation error."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class NotFoundError(OpenThreatException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier},
        )


class ValidationError(OpenThreatException):
    """Input validation error."""

    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )


class ExternalServiceError(OpenThreatException):
    """External service error."""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error ({service}): {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service},
        )


async def openthreat_exception_handler(
    request: Request, exc: OpenThreatException
) -> JSONResponse:
    """
    Handle OpenThreat custom exceptions.

    Args:
        request: FastAPI request
        exc: OpenThreat exception

    Returns:
        JSON error response
    """
    logger.error(
        f"OpenThreat error: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI validation errors.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON error response
    """
    logger.warning(
        f"Validation error: {exc.errors()}", extra={"path": request.url.path}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": exc.errors(),
            "path": str(request.url.path),
        },
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Args:
        request: FastAPI request
        exc: SQLAlchemy error

    Returns:
        JSON error response
    """
    logger.error(
        f"Database error: {str(exc)}", extra={"path": request.url.path}, exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "details": {"message": "An internal database error occurred"},
            "path": str(request.url.path),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSON error response
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "details": {"message": "An unexpected error occurred"},
            "path": str(request.url.path),
        },
    )


def register_error_handlers(app) -> None:
    """
    Register all error handlers with FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(OpenThreatException, openthreat_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
