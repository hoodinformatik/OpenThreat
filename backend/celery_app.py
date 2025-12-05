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
    include=[
        "backend.tasks",
        "backend.tasks.llm_tasks",
        "backend.tasks.data_tasks",
        "backend.tasks.news_tasks",
    ],
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
    # Refresh stats cache every 5 minutes
    "refresh-stats-cache": {
        "task": "tasks.refresh_stats_cache",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    # LLM Processing Tasks - Only for NEW CVEs
    "process-new-cves": {
        "task": "backend.tasks.llm_tasks.process_new_cves",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    # News fetching - Every 30 minutes
    "fetch-news-articles": {
        "task": "tasks.fetch_news_articles",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    # News LLM processing - Every 15 minutes
    "process-news-with-llm": {
        "task": "tasks.process_news_with_llm",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}

# Import task modules
from backend.tasks import data_tasks, llm_tasks, news_tasks  # noqa: E402, F401

if __name__ == "__main__":
    celery_app.start()
