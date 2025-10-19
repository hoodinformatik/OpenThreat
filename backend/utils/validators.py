"""
Input validation utilities.

Provides validators for CVE IDs, URLs, and other user inputs.
"""

import re

from fastapi import HTTPException, status

# CVE ID pattern: CVE-YYYY-NNNNN (where YYYY is year, NNNNN is 4+ digits)
CVE_ID_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$")

# URL pattern (basic validation)
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def validate_cve_id(cve_id: str) -> str:
    """
    Validate CVE ID format.

    Args:
        cve_id: CVE identifier to validate

    Returns:
        Validated CVE ID (uppercase)

    Raises:
        HTTPException: If CVE ID format is invalid
    """
    cve_id = cve_id.strip().upper()

    if not CVE_ID_PATTERN.match(cve_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CVE ID format: {cve_id}. Expected format: CVE-YYYY-NNNNN",
        )

    return cve_id


def validate_url(url: str) -> str:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        HTTPException: If URL format is invalid
    """
    url = url.strip()

    if not URL_PATTERN.match(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid URL format: {url}"
        )

    return url


def sanitize_search_query(query: str, max_length: int = 500) -> str:
    """
    Sanitize search query to prevent injection attacks.

    Args:
        query: Search query string
        max_length: Maximum allowed length

    Returns:
        Sanitized query string

    Raises:
        HTTPException: If query is too long or contains invalid characters
    """
    query = query.strip()

    if len(query) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search query too long. Maximum length: {max_length} characters",
        )

    if len(query) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query too short. Minimum length: 2 characters",
        )

    # Remove potentially dangerous characters for PostgreSQL full-text search
    # Allow: alphanumeric, spaces, hyphens, underscores, dots
    dangerous_chars = [
        "\\",
        ";",
        "--",
        "/*",
        "*/",
        "xp_",
        "sp_",
        "DROP",
        "DELETE",
        "INSERT",
        "UPDATE",
    ]
    query_upper = query.upper()

    for dangerous in dangerous_chars:
        if dangerous in query_upper:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query contains invalid characters",
            )

    return query


def validate_page_params(
    page: int, page_size: int, max_page_size: int = 100
) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (validated_page, validated_page_size)

    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be >= 1"
        )

    if page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be >= 1"
        )

    if page_size > max_page_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page size too large. Maximum: {max_page_size}",
        )

    return page, page_size


def validate_batch_size(batch_size: int, max_batch_size: int = 1000) -> int:
    """
    Validate batch size for bulk operations.

    Args:
        batch_size: Requested batch size
        max_batch_size: Maximum allowed batch size

    Returns:
        Validated batch size

    Raises:
        HTTPException: If batch size is invalid
    """
    if batch_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Batch size must be >= 1"
        )

    if batch_size > max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size too large. Maximum: {max_batch_size}",
        )

    return batch_size
