"""
API endpoints for LLM processing management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.tasks.llm_tasks import process_cve_with_llm, process_llm_queue, get_llm_stats
from backend.models import User, UserRole
from backend.dependencies.auth import require_role

router = APIRouter(prefix="/llm", tags=["LLM Processing"])


@router.get("/stats")
async def get_processing_stats():
    """
    Get LLM processing statistics.
    
    Returns:
        - total_cves: Total number of CVEs
        - processed: Number of processed CVEs
        - pending: Number of pending CVEs
        - high_priority_pending: Number of high priority pending CVEs
        - completion_percentage: Percentage of completion
    """
    try:
        stats = get_llm_stats.delay()
        result = stats.get(timeout=10)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/{cve_id}", dependencies=[Depends(require_role(UserRole.ANALYST))])
async def process_single_cve(cve_id: str):
    """
    Manually trigger LLM processing for a single CVE.
    
    **Requires:** ANALYST role or higher
    
    Args:
        cve_id: CVE ID to process
        
    Returns:
        Task ID for tracking
    """
    try:
        task = process_cve_with_llm.delay(cve_id)
        return {
            "status": "queued",
            "task_id": task.id,
            "cve_id": cve_id,
            "message": "CVE queued for LLM processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/batch", dependencies=[Depends(require_role(UserRole.ANALYST))])
async def process_batch(
    batch_size: int = 10,
    priority: str = "high"
):
    """
    Manually trigger batch LLM processing.
    
    **Requires:** ANALYST role or higher
    
    Args:
        batch_size: Number of CVEs to process
        priority: Priority level (high, medium, low)
        
    Returns:
        Task ID for tracking
    """
    if priority not in ["high", "medium", "low"]:
        raise HTTPException(status_code=400, detail="Invalid priority. Must be: high, medium, or low")
    
    if batch_size < 1 or batch_size > 100:
        raise HTTPException(status_code=400, detail="Batch size must be between 1 and 100")
    
    try:
        task = process_llm_queue.delay(batch_size=batch_size, priority=priority)
        return {
            "status": "queued",
            "task_id": task.id,
            "batch_size": batch_size,
            "priority": priority,
            "message": f"Batch of {batch_size} CVEs queued for LLM processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a LLM processing task.
    
    Args:
        task_id: Task ID from process endpoint
        
    Returns:
        Task status and result
    """
    from celery.result import AsyncResult
    from backend.celery_app import celery_app
    
    try:
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state == "PENDING":
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed"
            }
        elif task.state == "STARTED":
            return {
                "task_id": task_id,
                "status": "running",
                "message": "Task is currently running"
            }
        elif task.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "success",
                "result": task.result
            }
        elif task.state == "FAILURE":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info)
            }
        else:
            return {
                "task_id": task_id,
                "status": task.state.lower()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
