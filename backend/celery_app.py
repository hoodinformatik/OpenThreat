"""
Celery application for background tasks and scheduled jobs.
"""

import os

from celery import Celery
from celery.schedules import crontab

from backend.database import REDIS_URL

# Create Celery app
celery_app = Celery(
    "openthreat",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.tasks", "backend.tasks.llm_tasks", "backend.tasks.data_tasks"],
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
    # Fetch CISA KEV (Known Exploited Vulnerabilities) daily at 09:00 UTC
    "fetch-cisa-kev": {
        "task": "tasks.fetch_cisa_kev",
        "schedule": crontab(minute=0, hour=9),  # Daily at 09:00 UTC
    },
    # LLM Processing Tasks - Only for NEW CVEs
    "process-new-cves": {
        "task": "backend.tasks.llm_tasks.process_new_cves",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
}

# Import task modules
from backend.tasks import data_tasks, llm_tasks  # noqa: E402, F401

if __name__ == "__main__":
    celery_app.start()
