"""
Celery tasks for LLM processing of vulnerabilities.

This module handles background processing of CVEs to generate:
- Simple titles (< 10 words)
- Plain-language descriptions (2-3 sentences)
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from backend.celery_app import celery_app as celery
from backend.database import get_db
from backend.models import Vulnerability
from backend.llm_service import get_llm_service

logger = logging.getLogger(__name__)


@celery.task(name="tasks.process_cve_with_llm", bind=True, max_retries=3)
def process_cve_with_llm(self, cve_id: str) -> dict:
    """
    Process a single CVE with LLM to generate simple title and description.
    
    Args:
        cve_id: CVE ID to process
        
    Returns:
        Dict with status and results
    """
    db = next(get_db())
    try:
        # Fetch vulnerability
        vuln = db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
        
        if not vuln:
            logger.error(f"CVE not found: {cve_id}")
            return {"status": "error", "message": "CVE not found"}
        
        # Skip if already processed
        if vuln.llm_processed:
            logger.info(f"CVE already processed: {cve_id}")
            return {"status": "skipped", "message": "Already processed"}
        
        # Generate simple title and description using LLM
        llm_service = get_llm_service()
        
        try:
            result = llm_service.generate_cve_summary(
                cve_id=vuln.cve_id,
                original_title=vuln.title,
                description=vuln.description or "",
                cvss_score=vuln.cvss_score,
                severity=vuln.severity,
                vendors=vuln.vendors or [],
                products=vuln.products or [],
                published_at=vuln.published_at
            )
            
            simple_title = result.get("simple_title")
            simple_description = result.get("simple_description")
            
            logger.info(f"Generated summary for {cve_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate summary for {cve_id}: {e}")
            simple_title = None
            simple_description = None
        
        # Update database
        vuln.simple_title = simple_title
        vuln.simple_description = simple_description
        vuln.llm_processed = True
        vuln.llm_processed_at = datetime.utcnow()
        vuln.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Successfully processed {cve_id}")
        return {
            "status": "success",
            "cve_id": cve_id,
            "simple_title": simple_title,
            "simple_description": simple_description
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing {cve_id}: {e}")
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        
    finally:
        db.close()


@celery.task(name="tasks.process_llm_queue")
def process_llm_queue(batch_size: int = 10, priority: str = "high") -> dict:
    """
    Process a batch of unprocessed CVEs with LLM.
    
    Priority levels:
    - high: Exploited CVEs, CRITICAL severity, Recent (< 7 days)
    - medium: HIGH severity, Recent (< 30 days)
    - low: All others
    
    Args:
        batch_size: Number of CVEs to process in this batch
        priority: Priority level (high, medium, low)
        
    Returns:
        Dict with processing stats
    """
    db = next(get_db())
    try:
        # Build query for unprocessed CVEs
        query = db.query(Vulnerability).filter(
            Vulnerability.llm_processed == False
        )
        
        # Apply priority filtering
        if priority == "high":
            # High priority: Exploited OR Critical OR Recent
            from datetime import timedelta
            recent_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(
                (Vulnerability.exploited_in_the_wild == True) |
                (Vulnerability.severity == "CRITICAL") |
                (Vulnerability.published_at >= recent_date)
            )
        elif priority == "medium":
            # Medium priority: HIGH severity OR Recent (30 days)
            from datetime import timedelta
            recent_date = datetime.utcnow() - timedelta(days=30)
            query = query.filter(
                (Vulnerability.severity == "HIGH") |
                (Vulnerability.published_at >= recent_date)
            )
        
        # Order by priority score (highest first)
        query = query.order_by(Vulnerability.priority_score.desc())
        
        # Limit batch size
        vulns = query.limit(batch_size).all()
        
        if not vulns:
            logger.info(f"No unprocessed CVEs found for priority: {priority}")
            return {
                "status": "success",
                "processed": 0,
                "priority": priority,
                "message": "No CVEs to process"
            }
        
        # Queue tasks for each CVE
        processed = 0
        for vuln in vulns:
            try:
                process_cve_with_llm.delay(vuln.cve_id)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to queue {vuln.cve_id}: {e}")
        
        logger.info(f"Queued {processed} CVEs for LLM processing (priority: {priority})")
        return {
            "status": "success",
            "processed": processed,
            "priority": priority,
            "batch_size": batch_size
        }
        
    except Exception as e:
        logger.error(f"Error processing LLM queue: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()


@celery.task(name="tasks.process_new_cves")
def process_new_cves() -> dict:
    """
    Process newly added CVEs (added in last hour) with LLM.
    This task should run frequently (e.g., every 5 minutes).
    
    Returns:
        Dict with processing stats
    """
    db = next(get_db())
    try:
        from datetime import timedelta
        recent_date = datetime.utcnow() - timedelta(hours=1)
        
        # Find CVEs added in last hour that aren't processed
        vulns = db.query(Vulnerability).filter(
            Vulnerability.created_at >= recent_date,
            Vulnerability.llm_processed == False
        ).order_by(Vulnerability.priority_score.desc()).limit(20).all()
        
        if not vulns:
            logger.info("No new CVEs to process")
            return {
                "status": "success",
                "processed": 0,
                "message": "No new CVEs"
            }
        
        # Queue tasks
        processed = 0
        for vuln in vulns:
            try:
                process_cve_with_llm.delay(vuln.cve_id)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to queue {vuln.cve_id}: {e}")
        
        logger.info(f"Queued {processed} new CVEs for LLM processing")
        return {
            "status": "success",
            "processed": processed
        }
        
    except Exception as e:
        logger.error(f"Error processing new CVEs: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()


@celery.task(name="tasks.get_llm_stats")
def get_llm_stats() -> dict:
    """
    Get statistics about LLM processing progress.
    
    Returns:
        Dict with stats
    """
    db = next(get_db())
    try:
        total = db.query(Vulnerability).count()
        processed = db.query(Vulnerability).filter(Vulnerability.llm_processed == True).count()
        pending = total - processed
        
        # Count by priority
        from datetime import timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        high_priority = db.query(Vulnerability).filter(
            Vulnerability.llm_processed == False,
            (
                (Vulnerability.exploited_in_the_wild == True) |
                (Vulnerability.severity == "CRITICAL") |
                (Vulnerability.published_at >= recent_date)
            )
        ).count()
        
        return {
            "total_cves": total,
            "processed": processed,
            "pending": pending,
            "high_priority_pending": high_priority,
            "completion_percentage": round((processed / total * 100) if total > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting LLM stats: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()
