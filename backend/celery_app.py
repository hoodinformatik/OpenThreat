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
    include=["backend.tasks"]
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
    # Update vulnerabilities every 2 hours
    "update-vulnerabilities": {
        "task": "backend.tasks.update_vulnerabilities_task",
        "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours at :00
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
    
    # LLM Processing Tasks
    # Process new CVEs every 5 minutes
    "process-new-cves": {
        "task": "tasks.process_new_cves",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    # Process high priority queue every 10 minutes
    "process-high-priority": {
        "task": "tasks.process_llm_queue",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
        "kwargs": {"batch_size": 10, "priority": "high"}
    },
    # Process medium priority queue every 30 minutes
    "process-medium-priority": {
        "task": "tasks.process_llm_queue",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "kwargs": {"batch_size": 20, "priority": "medium"}
    },
    # Process low priority queue every 2 hours
    "process-low-priority": {
        "task": "tasks.process_llm_queue",
        "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
        "kwargs": {"batch_size": 50, "priority": "low"}
    },
}

if __name__ == "__main__":
    celery_app.start()
