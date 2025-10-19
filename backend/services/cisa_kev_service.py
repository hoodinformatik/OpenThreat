"""
CISA Known Exploited Vulnerabilities (KEV) Service.

Fetches and processes the CISA KEV catalog to mark vulnerabilities
as exploited in the wild using the NVD API.
"""

import logging
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models import Vulnerability
from backend.services.nvd_complete_service import NVDCompleteService

logger = logging.getLogger(__name__)


class CISAKEVService:
    """Service for fetching and processing CISA KEV data via NVD API."""
    
    NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(self):
        self.nvd_service = NVDCompleteService()
    
    def fetch_kev_cves(self) -> List[Dict]:
        """
        Fetch all CVEs marked as KEV from NVD API.
        
        Returns:
            List of CVE records with KEV status
        """
        all_cves = []
        start_index = 0
        results_per_page = 2000  # Maximum allowed by NVD API
        
        headers = {
            'User-Agent': 'OpenThreat/1.0 (Vulnerability Management System)',
            'Accept': 'application/json',
        }
        
        logger.info("Fetching KEV CVEs from NVD API...")
        
        while True:
            try:
                # Use hasKev parameter to get only KEV CVEs
                url = f"{self.NVD_API_BASE}?hasKev&resultsPerPage={results_per_page}&startIndex={start_index}"
                
                logger.info(f"Requesting CVEs from index {start_index}...")
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                vulnerabilities = data.get("vulnerabilities", [])
                total_results = data.get("totalResults", 0)
                
                if not vulnerabilities:
                    break
                
                all_cves.extend(vulnerabilities)
                logger.info(f"Fetched {len(vulnerabilities)} CVEs (total: {len(all_cves)}/{total_results})")
                
                # Check if we've fetched all results
                if len(all_cves) >= total_results:
                    break
                
                start_index += results_per_page
                
                # Rate limiting: NVD allows 5 requests per 30 seconds without API key
                # Sleep for 6 seconds between requests to be safe
                time.sleep(6)
                
            except Exception as e:
                logger.error(f"Failed to fetch KEV CVEs from NVD: {e}")
                break
        
        logger.info(f"Successfully fetched {len(all_cves)} KEV CVEs from NVD")
        return all_cves
    
    def update_exploited_vulnerabilities(self, db: Session) -> Dict:
        """
        Update database with CISA KEV data from NVD API.
        
        Args:
            db: Database session
            
        Returns:
            Dict with update statistics
        """
        kev_cves = self.fetch_kev_cves()
        
        if not kev_cves:
            return {
                "status": "error",
                "message": "Failed to fetch CISA KEV data from NVD",
                "updated": 0,
                "not_found": 0
            }
        
        logger.info(f"Processing {len(kev_cves)} KEV entries from NVD")
        
        updated_count = 0
        not_found_count = 0
        
        for vuln_wrapper in kev_cves:
            cve_data = vuln_wrapper.get("cve", {})
            cve_id = cve_data.get("id")
            
            if not cve_id:
                continue
            
            # Find CVE in database
            existing = db.query(Vulnerability).filter(
                Vulnerability.cve_id == cve_id
            ).first()
            
            if existing:
                # Mark as exploited
                existing.exploited_in_the_wild = True
                
                # Add CISA source if not present
                sources = existing.sources or []
                if "cisa_kev" not in sources:
                    sources.append("cisa_kev")
                    existing.sources = sources
                
                # Recalculate priority (exploitation increases priority)
                existing.priority_score = self.nvd_service._calculate_priority(
                    existing.cvss_score,
                    existing.severity,
                    existing.published_at.isoformat() if existing.published_at else None,
                    exploited=True
                )
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} CVEs...")
                    db.commit()  # Commit in batches
            else:
                not_found_count += 1
        
        # Final commit
        db.commit()
        
        logger.info(
            f"CISA KEV update complete: {updated_count} updated, "
            f"{not_found_count} not found in database"
        )
        
        return {
            "status": "success",
            "total_kev_entries": len(kev_cves),
            "updated": updated_count,
            "not_found": not_found_count,
            "timestamp": datetime.utcnow().isoformat()
        }


def get_cisa_kev_service() -> CISAKEVService:
    """Get CISA KEV service instance."""
    return CISAKEVService()
