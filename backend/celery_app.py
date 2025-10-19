"""
Celery application for background tasks and scheduled jobs.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "openthreat",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.tasks", "backend.tasks.llm_tasks", "backend.tasks.data_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Scheduled tasks (Beat schedule)
celery_app.conf.beat_schedule = {
    # Update vulnerabilities every 5 minutes (frequent CVE fetching)
    "update-vulnerabilities": {
        "task": "backend.tasks.update_vulnerabilities_task",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    # Clean old cache entries daily at 3 AM
    "clean-cache": {
        "task": "backend.tasks.clean_cache_task",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM
    },
    # Update statistics cache every 15 minutes
    "update-stats-cache": {
        "task": "backend.tasks.update_stats_cache_task",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    
    # Data Fetching Tasks
    # Fetch BSI CERT-Bund advisories daily at 08:00 UTC
    "fetch-bsi-cert": {
        "task": "tasks.fetch_bsi_cert",
        "schedule": crontab(minute=0, hour=8),  # Daily at 08:00 UTC
    },
    
    # LLM Processing Tasks - Only for NEW CVEs
    # Historical CVEs are marked as processed (skip LLM)
    # Only new CVEs will be processed with LLM
    "process-new-cves": {
        "task": "backend.tasks.llm_tasks.process_new_cves",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
}

# Import and register tasks manually to avoid circular imports
from backend.tasks import llm_tasks, data_tasks  # noqa: E402, F401

# Import core task functions from the tasks.py module (not the tasks package)
import sys
from pathlib import Path
tasks_module_path = Path(__file__).parent / "tasks.py"
spec = __import__('importlib.util').util.spec_from_file_location("backend.tasks_module", tasks_module_path)
tasks_module = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(tasks_module)

# Register core tasks manually
celery_app.task(base=tasks_module.DatabaseTask, bind=True, name="backend.tasks.update_vulnerabilities_task")(tasks_module.update_vulnerabilities_task)
celery_app.task(base=tasks_module.DatabaseTask, bind=True, name="backend.tasks.clean_cache_task")(tasks_module.clean_cache_task)
celery_app.task(base=tasks_module.DatabaseTask, bind=True, name="backend.tasks.update_stats_cache_task")(tasks_module.update_stats_cache_task)

if __name__ == "__main__":
    celery_app.start()
