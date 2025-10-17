"""
CSRF token endpoints.
"""
from fastapi import APIRouter, Request, Response
from fastapi_csrf_protect import CsrfProtect
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/csrf-token")
async def get_csrf_token(request: Request, response: Response):
    """
    Get CSRF token for the current session.
    
    This endpoint generates and returns a CSRF token that must be included
    in the headers of state-changing requests (POST, PUT, DELETE, PATCH).
    
    **Usage:**
    1. Call this endpoint to get a CSRF token
    2. Include the token in the `X-CSRF-Token` header for subsequent requests
    3. The token is also set as a cookie automatically
    
    **Example:**
    ```javascript
    // Get CSRF token
    const response = await fetch('/api/v1/csrf-token');
    const data = await response.json();
    const csrfToken = data.csrf_token;
    
    // Use token in subsequent requests
    await fetch('/api/v1/vulnerabilities', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({...})
    });
    ```
    
    Returns:
        CSRF token and cookie
    """
    csrf_protect = CsrfProtect()
    
    # Generate CSRF token (returns tuple: (token, signed_token))
    csrf_tokens = csrf_protect.generate_csrf()
    csrf_token = csrf_tokens[1] if isinstance(csrf_tokens, tuple) else csrf_tokens
    
    # Set CSRF cookie
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=3600,  # 1 hour
        httponly=True,
        secure=True,  # Only send over HTTPS in production
        samesite="lax"
    )
    
    logger.debug(f"CSRF token generated for IP: {request.client.host if request.client else 'unknown'}")
    
    return {
        "csrf_token": csrf_token,
        "expires_in": 3600,
        "usage": "Include this token in the X-CSRF-Token header for POST/PUT/DELETE/PATCH requests"
    }


@router.post("/csrf-token/refresh")
async def refresh_csrf_token(request: Request, response: Response):
    """
    Refresh CSRF token.
    
    Generates a new CSRF token, useful when the old one expires.
    
    Returns:
        New CSRF token
    """
    csrf_protect = CsrfProtect()
    
    # Generate new CSRF token (returns tuple: (token, signed_token))
    csrf_tokens = csrf_protect.generate_csrf()
    csrf_token = csrf_tokens[1] if isinstance(csrf_tokens, tuple) else csrf_tokens
    
    # Set new CSRF cookie
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=3600,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    logger.info(f"CSRF token refreshed for IP: {request.client.host if request.client else 'unknown'}")
    
    return {
        "csrf_token": csrf_token,
        "expires_in": 3600,
        "message": "CSRF token refreshed successfully"
    }
