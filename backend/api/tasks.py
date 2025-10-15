"""
Task management and monitoring endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from ..celery_app import celery_app
from ..tasks import (
    update_vulnerabilities_task,
    clean_cache_task,
    update_stats_cache_task,
    test_task,
)

router = APIRouter()


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/tasks/update-vulnerabilities", response_model=TaskResponse)
async def trigger_vulnerability_update():
    """
    Manually trigger a vulnerability update.
    
    This will:
    1. Collect data from all sources (CISA, NVD, etc.)
    2. Deduplicate and merge data
    3. Ingest into database
    
    **Note:** This is a long-running task (10-30 minutes).
    Use the task ID to check status.
    """
    task = update_vulnerabilities_task.delay()
    
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Vulnerability update task started. This may take 10-30 minutes."
    )


@router.post("/tasks/clean-cache", response_model=TaskResponse)
async def trigger_cache_cleanup():
    """
    Manually trigger cache cleanup.
    
    Removes cache entries older than 24 hours.
    """
    task = clean_cache_task.delay()
    
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Cache cleanup task started."
    )


@router.post("/tasks/update-stats", response_model=TaskResponse)
async def trigger_stats_update():
    """
    Manually trigger statistics cache update.
    
    Recalculates dashboard statistics.
    """
    task = update_stats_cache_task.delay()
    
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Statistics update task started."
    )


@router.post("/tasks/test", response_model=TaskResponse)
async def trigger_test_task(message: str = "Test message"):
    """
    Test task to verify Celery is working.
    
    Returns immediately with a simple message.
    """
    task = test_task.delay(message)
    
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Test task started with message: {message}"
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a background task.
    
    **Status values:**
    - `PENDING`: Task is waiting to be executed
    - `STARTED`: Task has started
    - `SUCCESS`: Task completed successfully
    - `FAILURE`: Task failed
    - `RETRY`: Task is being retried
    """
    task_result = celery_app.AsyncResult(task_id)
    
    response = TaskStatusResponse(
        task_id=task_id,
        status=task_result.status,
    )
    
    if task_result.successful():
        response.result = task_result.result
    elif task_result.failed():
        response.error = str(task_result.info)
    
    return response


@router.get("/tasks/scheduled/list")
async def list_scheduled_tasks():
    """
    List all scheduled tasks (Beat schedule).
    
    Shows which tasks run automatically and their schedules.
    """
    schedule = celery_app.conf.beat_schedule
    
    tasks = []
    for name, config in schedule.items():
        tasks.append({
            "name": name,
            "task": config["task"],
            "schedule": str(config["schedule"]),
            "description": _get_task_description(config["task"])
        })
    
    return {
        "scheduled_tasks": tasks,
        "total": len(tasks)
    }


@router.get("/tasks/workers/status")
async def get_workers_status():
    """
    Get status of Celery workers.
    
    Shows which workers are active and their statistics.
    """
    try:
        # Inspect active workers
        inspect = celery_app.control.inspect()
        
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        stats = inspect.stats()
        
        if not active_workers:
            return {
                "status": "no_workers",
                "message": "No Celery workers are running",
                "workers": []
            }
        
        workers = []
        for worker_name in active_workers.keys():
            worker_info = {
                "name": worker_name,
                "active_tasks": len(active_workers.get(worker_name, [])),
                "registered_tasks": len(registered_tasks.get(worker_name, [])),
                "stats": stats.get(worker_name, {})
            }
            workers.append(worker_info)
        
        return {
            "status": "healthy",
            "workers": workers,
            "total_workers": len(workers)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Celery workers: {str(e)}"
        )


def _get_task_description(task_name: str) -> str:
    """Get human-readable description for a task."""
    descriptions = {
        "backend.tasks.update_vulnerabilities_task": "Update vulnerabilities from all data sources",
        "backend.tasks.clean_cache_task": "Clean old cache entries",
        "backend.tasks.update_stats_cache_task": "Update statistics cache",
    }
    return descriptions.get(task_name, "No description available")
