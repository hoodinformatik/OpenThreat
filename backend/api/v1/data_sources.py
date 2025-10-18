"""
API endpoints for data source management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from backend.tasks.data_tasks import fetch_bsi_cert_task
from backend.services.nvd_complete_service import get_nvd_service
from backend.models import User, UserRole
from backend.dependencies.auth import require_admin
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])

# Thread pool for long-running tasks
executor = ThreadPoolExecutor(max_workers=2)


@router.post("/bsi-cert/fetch", dependencies=[Depends(require_admin)])
async def trigger_bsi_cert_fetch():
    """
    Manually trigger BSI CERT-Bund data fetch.
    
    **Requires:** ADMIN role
    
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
    from sqlalchemy import text
    
    db = next(get_db())
    try:
        # Count vulnerabilities with BSI source
        bsi_count = db.query(Vulnerability).filter(
            text("sources::jsonb @> '[\"bsi_cert\"]'::jsonb")
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


@router.post("/nvd/fetch-all", dependencies=[Depends(require_admin)])
async def trigger_nvd_fetch_all(start_year: int = 1999, end_year: int = None):
    """
    Trigger complete NVD database fetch.
    
    **Requires:** ADMIN role
    
    **Warning:** This will fetch ALL CVEs from NVD (300,000+) and may take several hours.
    
    Args:
        start_year: Starting year (default: 1999)
        end_year: Ending year (default: current year)
    
    Returns:
        Status message with information about the fetch process.
    """
    try:
        # Start fetch in background
        def run_fetch():
            nvd_service = get_nvd_service()
            return nvd_service.fetch_all_cves(start_year=start_year, end_year=end_year)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, run_fetch)
        
        return {
            "status": "started",
            "message": f"NVD fetch started for years {start_year}-{end_year or 'present'}",
            "source": "nvd",
            "warning": "This process will take several hours. Check logs for progress.",
            "note": "Get a free NVD API key at https://nvd.nist.gov/developers/request-an-api-key for faster fetching"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nvd/fetch-recent", dependencies=[Depends(require_admin)])
async def trigger_nvd_fetch_recent(days: int = 7):
    """
    Fetch CVEs modified in the last N days from NVD.
    
    **Requires:** ADMIN role
    
    This is much faster than fetching all CVEs and is useful for updates.
    
    Args:
        days: Number of days to look back (default: 7)
    
    Returns:
        Status message with task information.
    """
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    try:
        def run_fetch():
            nvd_service = get_nvd_service()
            return nvd_service.fetch_recent_cves(days=days)
        
        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, run_fetch)
        
        return {
            "status": "started",
            "message": f"Fetching CVEs modified in last {days} days",
            "source": "nvd",
            "estimated_time": "5-30 minutes depending on API key"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nvd/status")
async def get_nvd_status():
    """
    Get status of NVD integration.
    
    Returns information about CVEs from NVD in the database.
    """
    from backend.database import get_db
    from backend.models import Vulnerability
    from sqlalchemy import func, text
    
    db = next(get_db())
    try:
        # Count vulnerabilities with NVD source
        # Use raw SQL for JSON containment check
        nvd_count = db.query(Vulnerability).filter(
            text("sources::jsonb @> '[\"nvd\"]'::jsonb")
        ).count()
        
        # Get latest CVE from NVD
        latest_cve = db.query(Vulnerability).filter(
            text("sources::jsonb @> '[\"nvd\"]'::jsonb")
        ).order_by(Vulnerability.published_at.desc()).first()
        
        # Count by severity
        severity_counts = db.query(
            Vulnerability.severity,
            func.count(Vulnerability.id)
        ).filter(
            text("sources::jsonb @> '[\"nvd\"]'::jsonb")
        ).group_by(Vulnerability.severity).all()
        
        severity_breakdown = {sev: count for sev, count in severity_counts}
        
        return {
            "source": "nvd",
            "status": "active" if nvd_count > 0 else "empty",
            "total_cves": nvd_count,
            "latest_cve": {
                "cve_id": latest_cve.cve_id if latest_cve else None,
                "published_at": latest_cve.published_at if latest_cve else None
            } if latest_cve else None,
            "severity_breakdown": severity_breakdown,
            "api_url": "https://services.nvd.nist.gov/rest/json/cves/2.0"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/cisa-kev/fetch", dependencies=[Depends(require_admin)])
async def trigger_cisa_kev_fetch():
    """
    Fetch CISA Known Exploited Vulnerabilities catalog.
    
    **Requires:** ADMIN role
    
    This updates the exploited_in_the_wild flag for CVEs that are actively exploited.
    
    Returns:
        Status message with task information.
    """
    try:
        import cloudscraper
        from backend.database import get_db
        from backend.models import Vulnerability
        
        # Use cloudscraper to bypass Cloudflare protection
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Fetch CISA KEV catalog
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        
        try:
            response = scraper.get(url, timeout=60)
            response.raise_for_status()
            kev_data = response.json()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to fetch CISA KEV data: {str(e)}"
            )
        
        vulnerabilities = kev_data.get("vulnerabilities", [])
        
        # Update database
        db = next(get_db())
        updated_count = 0
        
        try:
            for vuln in vulnerabilities:
                cve_id = vuln.get("cveID")
                if not cve_id:
                    continue
                
                # Find CVE in database
                existing = db.query(Vulnerability).filter(
                    Vulnerability.cve_id == cve_id
                ).first()
                
                if existing:
                    existing.exploited_in_the_wild = True
                    
                    # Add CISA source if not present
                    sources = existing.sources or []
                    if "cisa_kev" not in sources:
                        sources.append("cisa_kev")
                        existing.sources = sources
                    
                    # Recalculate priority (exploitation increases priority)
                    from backend.services.nvd_complete_service import NVDCompleteService
                    service = NVDCompleteService()
                    existing.priority_score = service._calculate_priority(
                        existing.cvss_score,
                        existing.severity,
                        existing.published_at.isoformat() if existing.published_at else None,
                        exploited=True
                    )
                    
                    updated_count += 1
            
            db.commit()
            
            return {
                "status": "success",
                "message": f"Updated {updated_count} CVEs with CISA KEV data",
                "source": "cisa_kev",
                "total_kev_entries": len(vulnerabilities),
                "updated_in_db": updated_count
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cisa-kev/status")
async def get_cisa_kev_status():
    """
    Get status of CISA KEV integration.
    
    Returns information about exploited vulnerabilities.
    """
    from backend.database import get_db
    from backend.models import Vulnerability
    from sqlalchemy import text
    
    db = next(get_db())
    try:
        # Count exploited vulnerabilities
        exploited_count = db.query(Vulnerability).filter(
            Vulnerability.exploited_in_the_wild == True
        ).count()
        
        # Count with CISA source
        cisa_count = db.query(Vulnerability).filter(
            text("sources::jsonb @> '[\"cisa_kev\"]'::jsonb")
        ).count()
        
        return {
            "source": "cisa_kev",
            "status": "active" if cisa_count > 0 else "empty",
            "exploited_vulnerabilities": exploited_count,
            "cves_from_cisa": cisa_count,
            "catalog_url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
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
            "description": "Official CVE database from NIST",
            "endpoints": {
                "fetch_all": "/api/v1/data-sources/nvd/fetch-all",
                "fetch_recent": "/api/v1/data-sources/nvd/fetch-recent",
                "status": "/api/v1/data-sources/nvd/status"
            }
        },
        {
            "id": "cisa_kev",
            "name": "CISA Known Exploited Vulnerabilities",
            "type": "primary",
            "status": "active",
            "update_frequency": "Daily",
            "description": "Known exploited vulnerabilities catalog",
            "endpoints": {
                "fetch": "/api/v1/data-sources/cisa-kev/fetch",
                "status": "/api/v1/data-sources/cisa-kev/status"
            }
        },
        {
            "id": "bsi_cert",
            "name": "BSI CERT-Bund",
            "type": "enrichment",
            "status": "active",
            "update_frequency": "Daily at 08:00 UTC",
            "description": "German security advisories and recommendations",
            "endpoints": {
                "fetch": "/api/v1/data-sources/bsi-cert/fetch",
                "status": "/api/v1/data-sources/bsi-cert/status"
            }
        }
    ]
    
    return {
        "sources": sources,
        "total": len(sources)
    }
