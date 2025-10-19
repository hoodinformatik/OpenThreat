"""
FastAPI main application for OpenThreat.
"""

import logging
import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import api
from .config.logging_config import setup_logging
from .database import engine, get_db

# CSRF Protection
from .middleware.csrf_protect import csrf_protect_middleware

# Use Redis-based rate limiting for multi-replica support
from .middleware.redis_rate_limit import redis_rate_limit_middleware
from .models import Base
from .utils.error_handlers import register_error_handlers

# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"), log_file=os.getenv("LOG_FILE"))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OpenThreat API",
    description="Public Threat Intelligence Dashboard - Democratizing Threat Intelligence",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register error handlers
register_error_handlers(app)

# CORS middleware
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "OPTIONS",
    ],  # Explicit methods
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",
        "X-Request-ID",
    ],  # Explicit headers
    expose_headers=[
        "X-CSRF-Token",
        "X-Request-ID",
        "X-RateLimit-Limit-Minute",
        "X-RateLimit-Remaining-Minute",
    ],
)

# CSRF Protection middleware (must be before rate limiting)
app.middleware("http")(csrf_protect_middleware)

# Rate limiting middleware (Redis-based for distributed systems)
app.middleware("http")(redis_rate_limit_middleware)

# Metrics middleware
from .middleware.metrics import metrics_endpoint, metrics_middleware

app.middleware("http")(metrics_middleware)

# Metrics endpoint
app.add_api_route(
    "/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False
)

# Include routers
from .api import admin, auth, comments, csrf, feeds, health, search, stats, tasks, vulnerabilities
from .api.v1 import data_sources, llm

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(csrf.router, prefix="/api/v1", tags=["Security"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(vulnerabilities.router, prefix="/api/v1", tags=["Vulnerabilities"])
app.include_router(comments.router, prefix="/api/v1", tags=["Comments"])
app.include_router(stats.router, prefix="/api/v1", tags=["Statistics"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(feeds.router, prefix="/api/v1", tags=["Feeds"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(llm.router, prefix="/api/v1", tags=["LLM Processing"])
app.include_router(data_sources.router, prefix="/api/v1", tags=["Data Sources"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenThreat API",
        "version": "0.1.0",
        "description": "Public Threat Intelligence Dashboard",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "vulnerabilities": "/api/v1/vulnerabilities",
            "search": "/api/v1/search",
            "stats": "/api/v1/stats",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("🚀 OpenThreat API starting...")
    logger.info(f"📊 Database: {os.getenv('DATABASE_URL', 'Not configured')}")
    logger.info(f"🌐 CORS Origins: {allowed_origins}")
    logger.info(f"📝 Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
    logger.info(f"🛡️  CSRF Protection: Enabled")
    logger.info(f"🚦 Rate Limiting: Redis-based (distributed)")
    logger.info(f"   - Per minute: {os.getenv('RATE_LIMIT_PER_MINUTE', '60')}")
    logger.info(f"   - Per hour: {os.getenv('RATE_LIMIT_PER_HOUR', '1000')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("👋 OpenThreat API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
