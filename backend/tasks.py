"""
Celery background tasks for automated data collection and processing.
"""
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from celery import Task
from sqlalchemy import func, delete
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Vulnerability, IngestionRun, SearchCache

# Lazy import celery_app to avoid circular import
def get_celery_app():
    from .celery_app import celery_app
    return celery_app


class DatabaseTask(Task):
    """Base task with database session management."""
    _db = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


def update_vulnerabilities_task(self):
    """
    Scheduled task to update vulnerabilities from all data sources.
    Fetches recent CVEs from NVD (last 7 days).
    """
    try:
        print(f"[{datetime.utcnow()}] Starting vulnerability update...")
        
        # Import NVD service
        from .services.nvd_complete_service import get_nvd_service
        
        # Fetch recent CVEs (last 7 days)
        print("Fetching CVEs modified in last 7 days from NVD...")
        nvd_service = get_nvd_service()
        stats = nvd_service.fetch_recent_cves(days=7)
        
        print(f"Ingestion completed: {stats}")
        
        # Update task result
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
            "message": "Vulnerability update completed successfully"
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "Task timed out"
        print(f"ERROR: {error_msg}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_msg
        }
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_msg
        }


def clean_cache_task(self):
    """
    Clean old cache entries from the database.
    Runs daily at 3 AM.
    """
    try:
        print(f"[{datetime.utcnow()}] Starting cache cleanup...")
        
        # Delete cache entries older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        result = self.db.execute(
            delete(SearchCache).where(SearchCache.created_at < cutoff_time)
        )
        
        deleted_count = result.rowcount
        self.db.commit()
        
        print(f"Cache cleanup completed. Deleted {deleted_count} old entries.")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        self.db.rollback()
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_msg
        }


def update_stats_cache_task(self):
    """
    Update statistics cache for faster dashboard loading.
    Runs every 15 minutes.
    """
    try:
        print(f"[{datetime.utcnow()}] Updating statistics cache...")
        
        # Calculate statistics
        total_vulns = self.db.query(func.count(Vulnerability.id)).scalar()
        exploited_vulns = self.db.query(func.count(Vulnerability.id)).filter(
            Vulnerability.exploited_in_the_wild == True
        ).scalar()
        
        critical_vulns = self.db.query(func.count(Vulnerability.id)).filter(
            Vulnerability.severity == "CRITICAL"
        ).scalar()
        
        high_vulns = self.db.query(func.count(Vulnerability.id)).filter(
            Vulnerability.severity == "HIGH"
        ).scalar()
        
        # Recent updates (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_updates = self.db.query(func.count(Vulnerability.id)).filter(
            Vulnerability.updated_at >= seven_days_ago
        ).scalar()
        
        stats = {
            "total_vulnerabilities": total_vulns,
            "exploited_vulnerabilities": exploited_vulns,
            "critical_vulnerabilities": critical_vulns,
            "high_vulnerabilities": high_vulns,
            "recent_updates": recent_updates,
            "last_update": datetime.utcnow().isoformat()
        }
        
        print(f"Statistics cache updated: {stats}")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_msg
        }


def manual_update_task():
    """
    Manual trigger for vulnerability update.
    Can be called via API or CLI.
    """
    return update_vulnerabilities_task()


def test_task(message: str = "Hello from Celery!"):
    """
    Simple test task to verify Celery is working.
    """
    print(f"[{datetime.utcnow()}] Test task executed: {message}")
    return {
        "status": "success",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
