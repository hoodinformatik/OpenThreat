"""Utilities module for OpenThreat backend."""

from .error_handlers import (
    DatabaseError,
    ExternalServiceError,
    NotFoundError,
    OpenThreatException,
    ValidationError,
    register_error_handlers,
)

__all__ = [
    "OpenThreatException",
    "DatabaseError",
    "NotFoundError",
    "ValidationError",
    "ExternalServiceError",
    "register_error_handlers",
]
