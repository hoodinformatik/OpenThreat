"""
FastAPI main application for OpenThreat.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
import logging

from .database import get_db, engine
from .models import Base
from . import api
from .config.logging_config import setup_logging
from .utils.error_handlers import register_error_handlers
from .middleware.rate_limit import rate_limit_middleware

# Setup logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE")
)
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
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Include routers
from .api import vulnerabilities, stats, search, health, feeds, tasks
from .api.v1 import llm, data_sources

app.include_router(health.router, tags=["Health"])
app.include_router(vulnerabilities.router, prefix="/api/v1", tags=["Vulnerabilities"])
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
        }
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("🚀 OpenThreat API starting...")
    logger.info(f"📊 Database: {os.getenv('DATABASE_URL', 'Not configured')}")
    logger.info(f"🌐 CORS Origins: {allowed_origins}")
    logger.info(f"📝 Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("👋 OpenThreat API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
