"""
CSRF Protection middleware for OpenThreat.

Protects against Cross-Site Request Forgery attacks.
"""

import logging

from fastapi import Request

logger = logging.getLogger(__name__)

# CSRF Protection is currently disabled for GET requests
# Will be fully implemented after Authentication is added
CSRF_ENABLED = False  # TODO: Enable after Auth implementation


def is_safe_method(method: str) -> bool:
    """
    Check if HTTP method is safe (doesn't need CSRF protection).

    Args:
        method: HTTP method

    Returns:
        True if method is safe
    """
    return method in ["GET", "HEAD", "OPTIONS", "TRACE"]


def should_skip_csrf(request: Request) -> bool:
    """
    Check if request should skip CSRF validation.

    Args:
        request: FastAPI request

    Returns:
        True if CSRF should be skipped
    """
    # Skip for safe methods
    # if is_safe_method(request.method):
    #    return True

    # Skip for specific paths
    skip_paths = [
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    if request.url.path in skip_paths:
        return True

    # Skip for API endpoints that use API keys (TODO: implement after Auth)
    # if request.headers.get("X-API-Key"):
    #     return True

    return False


async def csrf_protect_middleware(request: Request, call_next):
    """
    CSRF protection middleware (currently disabled).

    TODO: Enable after Authentication is implemented.
    CSRF protection makes most sense with authenticated sessions.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    # CSRF is disabled for now - will be enabled with Authentication
    if not CSRF_ENABLED:
        return await call_next(request)

    # Skip CSRF for safe methods and whitelisted paths
    if should_skip_csrf(request):
        return await call_next(request)

    # TODO: Implement CSRF validation after Auth
    # For now, just pass through
    logger.debug(f"CSRF check skipped for {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    return response
