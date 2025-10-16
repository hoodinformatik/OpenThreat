"""
API endpoints for data source management.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.tasks.data_tasks import fetch_bsi_cert_task

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


@router.post("/bsi-cert/fetch")
async def trigger_bsi_cert_fetch():
    """
    Manually trigger BSI CERT-Bund data fetch.
    
    This will:
    1. Fetch latest security advisories from BSI CERT-Bund
    2. Extract CVE references
    3. Enrich existing CVEs with German descriptions
    
    Returns task ID for tracking.
    """
    try:
        task = fetch_bsi_cert_task.delay()
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "BSI CERT-Bund fetch task started",
            "source": "bsi_cert"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bsi-cert/status")
async def get_bsi_cert_status():
    """
    Get status of BSI CERT-Bund integration.
    
    Returns information about the last fetch and enrichment.
    """
    from backend.database import get_db
    from backend.models import Vulnerability
    
    db = next(get_db())
    try:
        # Count vulnerabilities with BSI source
        bsi_count = db.query(Vulnerability).filter(
            Vulnerability.sources.contains(["bsi_cert"])
        ).count()
        
        # Count vulnerabilities with BSI references
        bsi_refs = db.query(Vulnerability).filter(
            Vulnerability.references.op('@>')(
                '[{"source": "bsi_cert"}]'
            )
        ).count()
        
        return {
            "source": "bsi_cert",
            "status": "active",
            "vulnerabilities_with_bsi_source": bsi_count,
            "vulnerabilities_with_bsi_references": bsi_refs,
            "rss_feed": "https://wid.cert-bund.de/content/public/securityAdvisory/rss"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/list")
async def list_data_sources():
    """
    List all configured data sources.
    
    Returns information about available data sources and their status.
    """
    sources = [
        {
            "id": "nvd",
            "name": "National Vulnerability Database (NVD)",
            "type": "primary",
            "status": "active",
            "update_frequency": "Every 2 hours",
            "description": "Official CVE database from NIST"
        },
        {
            "id": "cisa_kev",
            "name": "CISA Known Exploited Vulnerabilities",
            "type": "primary",
            "status": "active",
            "update_frequency": "Daily",
            "description": "Known exploited vulnerabilities catalog"
        },
        {
            "id": "bsi_cert",
            "name": "BSI CERT-Bund",
            "type": "enrichment",
            "status": "active",
            "update_frequency": "Daily at 08:00 UTC",
            "description": "German security advisories and recommendations"
        }
    ]
    
    return {
        "sources": sources,
        "total": len(sources)
    }
