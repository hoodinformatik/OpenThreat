"""
Redis-based distributed rate limiting middleware.

Supports multiple backend replicas by using Redis as shared state.
"""

import logging
import os
from datetime import datetime
from typing import Tuple

import redis
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis.

    Works across multiple backend instances/replicas.
    """

    def __init__(
        self,
        redis_url: str,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """
        Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL
            requests_per_minute: Maximum requests per minute per IP
            requests_per_hour: Maximum requests per hour per IP
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("Redis rate limiter connected successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def check_rate_limit(self, ip: str) -> Tuple[bool, str, dict]:
        """
        Check if IP has exceeded rate limit using Redis.

        Args:
            ip: Client IP address

        Returns:
            Tuple of (is_allowed, error_message, rate_limit_info)
        """
        now = datetime.now()
        minute_key = f"rate_limit:{ip}:minute:{now.strftime('%Y%m%d%H%M')}"
        hour_key = f"rate_limit:{ip}:hour:{now.strftime('%Y%m%d%H')}"

        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()

            # Increment and get minute counter
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)  # Expire after 60 seconds

            # Increment and get hour counter
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # Expire after 1 hour

            results = pipe.execute()

            minute_count = results[0]
            hour_count = results[2]

            # Calculate remaining requests
            minute_remaining = max(0, self.requests_per_minute - minute_count)
            hour_remaining = max(0, self.requests_per_hour - hour_count)

            rate_limit_info = {
                "limit_minute": self.requests_per_minute,
                "limit_hour": self.requests_per_hour,
                "remaining_minute": minute_remaining,
                "remaining_hour": hour_remaining,
                "used_minute": minute_count,
                "used_hour": hour_count,
            }

            # Check limits
            if minute_count > self.requests_per_minute:
                return (
                    False,
                    f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
                    rate_limit_info,
                )

            if hour_count > self.requests_per_hour:
                return (
                    False,
                    f"Rate limit exceeded: {self.requests_per_hour} requests per hour",
                    rate_limit_info,
                )

            return True, "", rate_limit_info

        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request if Redis is down
            return (
                True,
                "",
                {
                    "limit_minute": self.requests_per_minute,
                    "limit_hour": self.requests_per_hour,
                    "remaining_minute": self.requests_per_minute,
                    "remaining_hour": self.requests_per_hour,
                    "error": "rate_limiter_unavailable",
                },
            )

    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.

        Handles proxies (X-Forwarded-For, X-Real-IP).

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded.split(",")[0].strip()

        # Check for real IP (set by some proxies)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    def is_whitelisted(self, ip: str) -> bool:
        """
        Check if IP is whitelisted (bypass rate limiting).

        Args:
            ip: IP address to check

        Returns:
            True if whitelisted
        """
        # Get whitelist from environment variable
        whitelist = os.getenv("RATE_LIMIT_WHITELIST", "").split(",")
        whitelist = [ip.strip() for ip in whitelist if ip.strip()]

        return ip in whitelist


# Global rate limiter instance
from backend.database import REDIS_URL

redis_rate_limiter = RedisRateLimiter(
    redis_url=REDIS_URL,
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
    requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
)


async def redis_rate_limit_middleware(request: Request, call_next):
    """
    Redis-based rate limiting middleware for FastAPI.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response or rate limit error
    """
    # Skip rate limiting for health checks and docs
    skip_paths = ["/health", "/", "/docs", "/redoc", "/openapi.json", "/metrics"]
    if request.url.path in skip_paths:
        return await call_next(request)

    # Get client IP
    client_ip = redis_rate_limiter.get_client_ip(request)

    # Check if IP is whitelisted
    if redis_rate_limiter.is_whitelisted(client_ip):
        response = await call_next(request)
        response.headers["X-RateLimit-Bypass"] = "whitelisted"
        return response

    # Check rate limit
    is_allowed, error_message, rate_info = redis_rate_limiter.check_rate_limit(
        client_ip
    )

    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded for IP: {client_ip}",
            extra={
                "ip": client_ip,
                "path": request.url.path,
                "used_minute": rate_info.get("used_minute"),
                "used_hour": rate_info.get("used_hour"),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": error_message,
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "details": {
                    "retry_after": "60 seconds",
                    "limits": {
                        "per_minute": rate_info["limit_minute"],
                        "per_hour": rate_info["limit_hour"],
                    },
                    "remaining": {
                        "per_minute": rate_info["remaining_minute"],
                        "per_hour": rate_info["remaining_hour"],
                    },
                },
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit-Minute": str(rate_info["limit_minute"]),
                "X-RateLimit-Limit-Hour": str(rate_info["limit_hour"]),
                "X-RateLimit-Remaining-Minute": str(rate_info["remaining_minute"]),
                "X-RateLimit-Remaining-Hour": str(rate_info["remaining_hour"]),
            },
        )

    # Process request
    response = await call_next(request)

    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit-Minute"] = str(rate_info["limit_minute"])
    response.headers["X-RateLimit-Limit-Hour"] = str(rate_info["limit_hour"])
    response.headers["X-RateLimit-Remaining-Minute"] = str(
        rate_info["remaining_minute"]
    )
    response.headers["X-RateLimit-Remaining-Hour"] = str(rate_info["remaining_hour"])

    return response
