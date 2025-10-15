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

from .celery_app import celery_app
from .database import SessionLocal
from .models import Vulnerability, IngestionRun, SearchCache


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


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.update_vulnerabilities_task")
def update_vulnerabilities_task(self):
    """
    Scheduled task to update vulnerabilities from all data sources.
    Runs every 2 hours.
    """
    try:
        print(f"[{datetime.utcnow()}] Starting vulnerability update...")
        
        # Get project root directory
        project_root = Path(__file__).parent.parent
        connectors_dir = project_root / "Data_Sample_Connectors"
        output_dir = connectors_dir / "out"
        
        # Ensure output directory exists
        output_dir.mkdir(exist_ok=True)
        
        # Step 1: Run all data connectors
        print("Step 1/3: Collecting data from sources...")
        run_all_script = connectors_dir / "run_all.py"
        
        result = subprocess.run(
            ["python", str(run_all_script)],
            cwd=str(connectors_dir),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"Data collection failed: {result.stderr}")
        
        print(f"Data collection completed. Output:\n{result.stdout}")
        
        # Step 2: Run deduplication
        print("Step 2/3: Deduplicating data...")
        dedup_script = connectors_dir / "deduplicator.py"
        
        result = subprocess.run(
            ["python", str(dedup_script)],
            cwd=str(connectors_dir),
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"Deduplication failed: {result.stderr}")
        
        print(f"Deduplication completed. Output:\n{result.stdout}")
        
        # Step 3: Ingest into database
        print("Step 3/3: Ingesting into database...")
        deduplicated_file = output_dir / "deduplicated_cves.ndjson"
        
        if not deduplicated_file.exists():
            raise Exception(f"Deduplicated file not found: {deduplicated_file}")
        
        # Import ingestion module
        from .ingestion import ingest_from_ndjson
        
        # Run ingestion
        stats = ingest_from_ndjson(
            str(deduplicated_file),
            run_type="scheduled_update",
            db=self.db
        )
        
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


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.clean_cache_task")
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


@celery_app.task(base=DatabaseTask, bind=True, name="backend.tasks.update_stats_cache_task")
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


@celery_app.task(name="backend.tasks.manual_update_task")
def manual_update_task():
    """
    Manual trigger for vulnerability update.
    Can be called via API or CLI.
    """
    return update_vulnerabilities_task()


@celery_app.task(name="backend.tasks.test_task")
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
