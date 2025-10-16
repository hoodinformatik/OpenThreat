"""
Prometheus metrics middleware for OpenThreat.

Collects and exposes metrics for monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import time
import logging

logger = logging.getLogger(__name__)

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress'
)

# Application metrics
vulnerabilities_total = Gauge(
    'vulnerabilities_total',
    'Total number of vulnerabilities in database'
)

exploited_vulnerabilities_total = Gauge(
    'exploited_vulnerabilities_total',
    'Total number of exploited vulnerabilities'
)

# Error metrics
http_errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'status']
)


async def metrics_middleware(request: Request, call_next):
    """
    Middleware to collect Prometheus metrics.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response with metrics collected
    """
    # Skip metrics collection for metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)
    
    # Track in-progress requests
    http_requests_in_progress.inc()
    
    # Record start time
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Track errors
        if response.status_code >= 400:
            http_errors_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
        
        return response
        
    finally:
        # Decrement in-progress counter
        http_requests_in_progress.dec()


def update_application_metrics(db_session):
    """
    Update application-specific metrics.
    
    Args:
        db_session: Database session
    """
    try:
        from backend.models import Vulnerability
        
        # Update vulnerability counts
        total = db_session.query(Vulnerability).count()
        exploited = db_session.query(Vulnerability).filter(
            Vulnerability.exploited_in_the_wild == True
        ).count()
        
        vulnerabilities_total.set(total)
        exploited_vulnerabilities_total.set(exploited)
        
    except Exception as e:
        logger.error(f"Failed to update application metrics: {e}")


async def metrics_endpoint(request: Request):
    """
    Prometheus metrics endpoint.
    
    Args:
        request: FastAPI request
        
    Returns:
        Prometheus metrics in text format
    """
    # Update application metrics before exposing
    try:
        from backend.database import get_db
        db = next(get_db())
        update_application_metrics(db)
    except Exception as e:
        logger.warning(f"Could not update metrics: {e}")
    
    # Generate and return metrics
    metrics_data = generate_latest()
    
    return FastAPIResponse(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )
