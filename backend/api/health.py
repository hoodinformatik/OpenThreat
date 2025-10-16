"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import psutil
import os

from ..database import get_db
from ..schemas import HealthResponse
from ..models import Vulnerability

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint.
    
    Returns API status and database connectivity.
    """
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with system metrics.
    
    Returns comprehensive system health information.
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "checks": {}
    }
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        vuln_count = db.query(Vulnerability).count()
        health_data["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": "<10",
            "vulnerability_count": vuln_count
        }
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free // (1024 * 1024 * 1024)
        }
        
        # Warn if resources are low
        if memory.percent > 90 or disk.percent > 90:
            health_data["status"] = "degraded"
            health_data["checks"]["system"]["warning"] = "High resource usage"
            
    except Exception as e:
        health_data["checks"]["system"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Environment check
    health_data["checks"]["environment"] = {
        "python_version": os.sys.version.split()[0],
        "database_url_configured": bool(os.getenv("DATABASE_URL")),
        "redis_url_configured": bool(os.getenv("REDIS_URL"))
    }
    
    # Set HTTP status based on health
    http_status = status.HTTP_200_OK
    if health_data["status"] == "degraded":
        http_status = status.HTTP_200_OK  # Still operational
    elif health_data["status"] == "unhealthy":
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=health_data, status_code=http_status)


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe.
    
    Returns 200 if service is ready to accept traffic.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(
            content={"status": "not ready"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe.
    
    Returns 200 if service is alive.
    """
    return {"status": "alive"}
