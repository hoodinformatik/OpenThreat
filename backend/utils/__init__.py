"""Utilities module for OpenThreat backend."""

from .error_handlers import (
    OpenThreatException,
    DatabaseError,
    NotFoundError,
    ValidationError,
    ExternalServiceError,
    register_error_handlers
)

__all__ = [
    "OpenThreatException",
    "DatabaseError",
    "NotFoundError",
    "ValidationError",
    "ExternalServiceError",
    "register_error_handlers"
]
