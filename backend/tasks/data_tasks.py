"""
Celery tasks for data fetching and enrichment.

This module handles background tasks for:
- Fetching data from external sources
- Enriching existing vulnerabilities
- Updating metadata
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from backend.celery_app import celery_app as celery
from backend.database import get_db
from backend.services.bsi_cert_service import get_bsi_cert_service
from backend.services.cisa_kev_service import get_cisa_kev_service

logger = logging.getLogger(__name__)


@celery.task(name="tasks.fetch_bsi_cert", bind=True, max_retries=3)
def fetch_bsi_cert_task(self) -> dict:
    """
    Fetch BSI CERT-Bund advisories and enrich CVEs.
    
    This task:
    1. Fetches latest security advisories from BSI CERT-Bund
    2. Extracts CVE references
    3. Enriches existing CVEs with German descriptions
    4. Adds BSI references and severity ratings
    
    Returns:
        Dict with status and results
    """
    db = next(get_db())
    try:
        logger.info("Starting BSI CERT-Bund fetch task")
        
        # Get BSI CERT service
        bsi_service = get_bsi_cert_service()
        
        # Fetch advisories
        advisories = bsi_service.fetch_advisories()
        
        if not advisories:
            logger.warning("No BSI CERT-Bund advisories fetched")
            return {
                "status": "success",
                "advisories_fetched": 0,
                "vulnerabilities_enriched": 0,
                "message": "No advisories available"
            }
        
        logger.info(f"Fetched {len(advisories)} BSI CERT-Bund advisories")
        
        # Count CVE references
        total_cves = sum(len(adv.get("cve_ids", [])) for adv in advisories)
        
        # Enrich vulnerabilities
        enriched = bsi_service.enrich_vulnerabilities(db)
        
        logger.info(f"BSI CERT-Bund task complete: {enriched} vulnerabilities enriched")
        
        return {
            "status": "success",
            "advisories_fetched": len(advisories),
            "cve_references_found": total_cves,
            "vulnerabilities_enriched": enriched,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"BSI CERT-Bund task failed: {e}")
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        
    finally:
        db.close()


@celery.task(name="tasks.fetch_cisa_kev", bind=True, max_retries=3)
def fetch_cisa_kev_task(self) -> dict:
    """
    Fetch CISA Known Exploited Vulnerabilities catalog.
    
    This task:
    1. Fetches the latest CISA KEV catalog
    2. Marks CVEs as exploited in the wild
    3. Updates priority scores
    4. Adds CISA KEV as a source
    
    Returns:
        Dict with status and results
    """
    db = next(get_db())
    try:
        logger.info("Starting CISA KEV fetch task")
        
        # Get CISA KEV service
        kev_service = get_cisa_kev_service()
        
        # Fetch and update
        result = kev_service.update_exploited_vulnerabilities(db)
        
        if result["status"] == "success":
            logger.info(
                f"CISA KEV task complete: {result['updated']} vulnerabilities updated"
            )
        else:
            logger.warning(f"CISA KEV task completed with warnings: {result}")
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"CISA KEV task failed: {e}")
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        
    finally:
        db.close()
