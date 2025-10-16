"""
Rate limiting middleware for OpenThreat API.

Prevents abuse by limiting requests per IP address.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per IP
            requests_per_hour: Maximum requests per hour per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store: {ip: [(timestamp, count_minute, count_hour)]}
        self.request_counts: Dict[str, Tuple[datetime, int, int]] = {}
    
    def _clean_old_entries(self) -> None:
        """Remove entries older than 1 hour."""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        
        self.request_counts = {
            ip: data
            for ip, data in self.request_counts.items()
            if data[0] > cutoff
        }
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """
        Check if IP has exceeded rate limit.
        
        Args:
            ip: Client IP address
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        now = datetime.now()
        
        # Clean old entries periodically
        if len(self.request_counts) > 10000:
            self._clean_old_entries()
        
        if ip not in self.request_counts:
            self.request_counts[ip] = (now, 1, 1)
            return True, ""
        
        last_request, count_minute, count_hour = self.request_counts[ip]
        
        # Reset counters if time windows have passed
        if now - last_request > timedelta(minutes=1):
            count_minute = 0
        if now - last_request > timedelta(hours=1):
            count_hour = 0
        
        # Increment counters
        count_minute += 1
        count_hour += 1
        
        # Check limits
        if count_minute > self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        if count_hour > self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Update counts
        self.request_counts[ip] = (now, count_minute, count_hour)
        
        return True, ""
    
    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.
        
        Args:
            request: FastAPI request
            
        Returns:
            Client IP address
        """
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        return request.client.host if request.client else "unknown"


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=60,  # 60 requests per minute
    requests_per_hour=1000   # 1000 requests per hour
)


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response or rate limit error
    """
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Get client IP
    client_ip = rate_limiter.get_client_ip(request)
    
    # Check rate limit
    is_allowed, error_message = rate_limiter.check_rate_limit(client_ip)
    
    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded for IP: {client_ip}",
            extra={"ip": client_ip, "path": request.url.path}
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": error_message,
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "details": {
                    "retry_after": "60 seconds",
                    "limits": {
                        "per_minute": rate_limiter.requests_per_minute,
                        "per_hour": rate_limiter.requests_per_hour
                    }
                }
            },
            headers={"Retry-After": "60"}
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit-Minute"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Limit-Hour"] = str(rate_limiter.requests_per_hour)
    
    return response
