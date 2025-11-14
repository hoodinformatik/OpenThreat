"""
NVD Complete Service - Fetch all CVEs from NVD API 2.0

This service handles:
1. Initial bulk download of all CVEs (1999-present)
2. Incremental updates for recent changes
3. Rate limiting and retry logic
4. Progress tracking and resume capability
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Vulnerability
from backend.services.stats_cache_service import refresh_stats_cache

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class NVDCompleteService:
    """Service for fetching complete CVE data from NVD API 2.0"""

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    RESULTS_PER_PAGE = 2000  # NVD API max
    RATE_LIMIT_DELAY = 6  # seconds (10 requests per minute for no API key)

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NVD service.

        Args:
            api_key: Optional NVD API key for higher rate limits (50 req/min)
        """
        self.api_key = api_key or os.getenv("NVD_API_KEY")
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({"apiKey": self.api_key})
            self.rate_limit_delay = 0.6  # 50 requests per minute
            logger.info("NVD API key configured - using enhanced rate limit")
        else:
            self.rate_limit_delay = self.RATE_LIMIT_DELAY
            logger.warning("No NVD API key - using public rate limit (slower)")

    def fetch_all_cves(
        self,
        start_year: int = 1999,
        end_year: Optional[int] = None,
        checkpoint_file: str = "nvd_checkpoint.txt",
    ) -> int:
        """
        Fetch all CVEs from NVD and store in database.

        Note: NVD API 2.0 doesn't support filtering by publication date for bulk downloads.
        We fetch all CVEs without date filtering.

        Args:
            start_year: Ignored (kept for compatibility)
            end_year: Ignored (kept for compatibility)
            checkpoint_file: File to track progress for resume capability

        Returns:
            Total number of CVEs processed
        """
        logger.info(f"Starting NVD complete fetch (all CVEs)")
        logger.info(f"Note: Fetching entire NVD database without date filtering")

        # Check for checkpoint
        start_index = self._load_checkpoint(checkpoint_file)

        # Fetch all CVEs without date filtering
        total_processed = self._fetch_cves_by_date_range(
            start_index=start_index, checkpoint_file=checkpoint_file
        )

        # Clean up checkpoint file
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)

        logger.info(f"NVD complete fetch finished: {total_processed} total CVEs")
        return total_processed

    def fetch_recent_cves(self, days: int = 7) -> int:
        """
        Fetch CVEs modified in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Number of CVEs processed
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching CVEs modified in last {days} days")

        count = self._fetch_cves_by_date_range(
            mod_start_date=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            mod_end_date=end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        logger.info(f"Recent CVEs fetch complete: {count} CVEs processed")
        return count

    def _fetch_cves_by_date_range(
        self,
        pub_start_date: Optional[str] = None,
        pub_end_date: Optional[str] = None,
        mod_start_date: Optional[str] = None,
        mod_end_date: Optional[str] = None,
        start_index: int = 0,
        checkpoint_file: Optional[str] = None,
    ) -> int:
        """
        Fetch CVEs within a date range with pagination.

        Args:
            pub_start_date: Publication start date (ISO format with Z)
            pub_end_date: Publication end date (ISO format with Z)
            mod_start_date: Modification start date (ISO format with Z)
            mod_end_date: Modification end date (ISO format with Z)
            start_index: Starting index for pagination (for resume)
            checkpoint_file: File to save progress

        Returns:
            Number of CVEs processed
        """
        params = {"resultsPerPage": self.RESULTS_PER_PAGE, "startIndex": start_index}

        # NVD API 2.0 expects dates in ISO 8601 format with Z suffix
        if pub_start_date:
            # Convert to proper format if needed
            if not pub_start_date.endswith("Z"):
                pub_start_date = pub_start_date.replace(".000", "Z")
            params["pubStartDate"] = pub_start_date
        if pub_end_date:
            if not pub_end_date.endswith("Z"):
                pub_end_date = pub_end_date.replace(".000", "Z")
            params["pubEndDate"] = pub_end_date
        if mod_start_date:
            if not mod_start_date.endswith("Z"):
                mod_start_date = mod_start_date.replace(".000", "Z")
            params["lastModStartDate"] = mod_start_date
        if mod_end_date:
            if not mod_end_date.endswith("Z"):
                mod_end_date = mod_end_date.replace(".000", "Z")
            params["lastModEndDate"] = mod_end_date

        total_processed = 0

        while True:
            try:
                # Rate limiting
                time.sleep(self.rate_limit_delay)

                # Fetch page
                logger.info(f"Fetching CVEs: startIndex={params['startIndex']}")
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                # Extract CVEs
                vulnerabilities = data.get("vulnerabilities", [])
                total_results = data.get("totalResults", 0)

                if not vulnerabilities:
                    logger.info("No more CVEs to fetch")
                    break

                # Process CVEs
                db = next(get_db())
                try:
                    for vuln_data in vulnerabilities:
                        self._process_cve(db, vuln_data)
                        total_processed += 1

                    db.commit()
                    logger.info(
                        f"Processed {len(vulnerabilities)} CVEs (Total: {total_processed}/{total_results})"
                    )

                    # Refresh stats cache after each batch
                    refresh_stats_cache(db)

                    # Save checkpoint
                    if checkpoint_file:
                        self._save_checkpoint(
                            checkpoint_file, params["startIndex"] + len(vulnerabilities)
                        )

                except Exception as e:
                    db.rollback()
                    logger.error(f"Database error: {e}")
                    raise
                finally:
                    db.close()

                # Check if we've fetched all results
                if params["startIndex"] + len(vulnerabilities) >= total_results:
                    logger.info("All CVEs fetched for this range")
                    break

                # Move to next page
                params["startIndex"] += self.RESULTS_PER_PAGE

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                logger.info("Retrying in 30 seconds...")
                time.sleep(30)
                continue

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

        return total_processed

    def _process_cve(self, db: Session, vuln_data: Dict[str, Any]) -> None:
        """
        Process a single CVE and store in database.

        Args:
            db: Database session
            vuln_data: CVE data from NVD API
        """
        cve = vuln_data.get("cve", {})
        cve_id = cve.get("id")

        if not cve_id:
            logger.warning("CVE without ID, skipping")
            return

        # Skip non-CVE entries (e.g., GHSA)
        if not cve_id.startswith("CVE-"):
            logger.debug(f"Skipping non-CVE entry: {cve_id}")
            return

        # Extract basic info
        published = cve.get("published")
        modified = cve.get("lastModified")

        # Extract descriptions
        descriptions = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            descriptions[0]["value"] if descriptions else None,
        )

        # Extract CVSS metrics
        metrics = cve.get("metrics", {})
        cvss_score = None
        cvss_vector = None
        severity = "UNKNOWN"

        # Try CVSS v3.1 first, then v3.0, then v2.0
        for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if version in metrics and metrics[version]:
                cvss_data = metrics[version][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
                severity = cvss_data.get("baseSeverity", "UNKNOWN").upper()
                break

        # Extract CWE IDs
        weaknesses = cve.get("weaknesses", [])
        cwe_ids = []
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                if desc.get("lang") == "en":
                    cwe_id = desc.get("value")
                    if cwe_id and cwe_id.startswith("CWE-"):
                        cwe_ids.append(cwe_id)

        # Extract references
        references = cve.get("references", [])
        reference_list = []
        for ref in references[:20]:  # Limit to 20 references
            url = ref.get("url")
            if url:
                reference_list.append(
                    {"url": url, "source": "nvd", "tags": ref.get("tags", [])}
                )

        # Extract affected products (CPE)
        configurations = cve.get("configurations", [])
        cpe_list = []
        affected_products = []

        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    if cpe_match.get("vulnerable"):
                        cpe_uri = cpe_match.get("criteria")
                        if cpe_uri:
                            cpe_list.append(cpe_uri)
                            affected_products.append(cpe_uri)

        # Parse vendors and products from CPE
        vendors_products = self._parse_cpe(cpe_list)
        vendor_list = list(vendors_products.keys())
        product_list = []
        for products in vendors_products.values():
            product_list.extend(products)

        # Check if CVE exists
        existing = (
            db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
        )

        if existing:
            # Update existing - merge sources
            existing.description = description or existing.description
            existing.cvss_score = cvss_score or existing.cvss_score
            existing.cvss_vector = cvss_vector or existing.cvss_vector
            existing.severity = severity if severity != "UNKNOWN" else existing.severity
            existing.published_at = published or existing.published_at
            existing.modified_at = modified or existing.modified_at

            # Merge CWE IDs
            existing_cwes = existing.cwe_ids or []
            merged_cwes = list(set(existing_cwes + cwe_ids))
            existing.cwe_ids = merged_cwes

            # Merge references
            existing_refs = existing.references or []
            # Handle both dict and string formats
            existing_urls = set()
            for r in existing_refs:
                if isinstance(r, dict):
                    existing_urls.add(r.get("url"))
                elif isinstance(r, str):
                    existing_urls.add(r)

            for ref in reference_list:
                if ref["url"] not in existing_urls:
                    existing_refs.append(ref)
            existing.references = existing_refs

            # Merge vendors and products
            existing.vendors = list(set((existing.vendors or []) + vendor_list))
            existing.products = list(set((existing.products or []) + product_list))
            existing.affected_products = list(
                set((existing.affected_products or []) + affected_products)
            )

            # Merge sources
            existing_sources = existing.sources or []
            if "nvd" not in existing_sources:
                existing_sources.append("nvd")
            existing.sources = existing_sources

            # Recalculate priority
            pub_date_str = None
            if existing.published_at:
                if isinstance(existing.published_at, str):
                    pub_date_str = existing.published_at
                else:
                    pub_date_str = existing.published_at.isoformat()

            existing.priority_score = self._calculate_priority(
                existing.cvss_score,
                existing.severity,
                pub_date_str,
                existing.exploited_in_the_wild,
            )

            existing.updated_at = datetime.utcnow()
            logger.debug(f"Updated existing CVE: {cve_id}")

        else:
            # Create new
            vulnerability = Vulnerability(
                cve_id=cve_id,
                title=f"Vulnerability in {cve_id}",
                description=description,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                severity=severity,
                published_at=published,
                modified_at=modified,
                exploited_in_the_wild=False,  # Will be updated by CISA KEV
                cwe_ids=cwe_ids,
                references=reference_list,
                vendors=vendor_list,
                products=product_list,
                affected_products=affected_products,
                sources=["nvd"],
                priority_score=self._calculate_priority(
                    cvss_score, severity, published
                ),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(vulnerability)
            logger.debug(f"Created new CVE: {cve_id}")

    def _parse_cpe(self, cpe_list: List[str]) -> Dict[str, set]:
        """
        Parse CPE URIs to extract vendor and product names.

        CPE format: cpe:2.3:a:vendor:product:version:...

        Args:
            cpe_list: List of CPE URIs

        Returns:
            Dict mapping vendor names to sets of product names
        """
        vendors_products = {}

        for cpe in cpe_list:
            parts = cpe.split(":")
            if len(parts) >= 5:
                vendor = parts[3].replace("_", " ").title()
                product = parts[4].replace("_", " ").title()

                if vendor not in vendors_products:
                    vendors_products[vendor] = set()
                vendors_products[vendor].add(product)

        return vendors_products

    def _calculate_priority(
        self,
        cvss_score: Optional[float],
        severity: str,
        published_at: Optional[str],
        exploited: bool = False,
    ) -> float:
        """
        Calculate priority score (0.0-1.0).

        Args:
            cvss_score: CVSS base score
            severity: Severity level
            published_at: Publication date

        Returns:
            Priority score
        """
        # CVSS weight (40%)
        cvss_weight = 0.0
        if cvss_score:
            cvss_weight = cvss_score / 10.0
        elif severity == "CRITICAL":
            cvss_weight = 1.0
        elif severity == "HIGH":
            cvss_weight = 0.7
        elif severity == "MEDIUM":
            cvss_weight = 0.4
        elif severity == "LOW":
            cvss_weight = 0.2

        # Recency weight (20%)
        recency_weight = 0.0
        if published_at:
            try:
                pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                days_old = (datetime.now(pub_date.tzinfo) - pub_date).days

                if days_old <= 7:
                    recency_weight = 1.0
                elif days_old <= 30:
                    recency_weight = 0.5
            except:
                pass

        # Exploitation weight (40%)
        exploit_weight = 1.0 if exploited else 0.0

        priority = (cvss_weight * 0.4) + (recency_weight * 0.2) + (exploit_weight * 0.4)
        return round(priority, 3)

    def _save_checkpoint(self, checkpoint_file: str, index: int) -> None:
        """Save progress checkpoint."""
        with open(checkpoint_file, "w") as f:
            f.write(str(index))

    def _load_checkpoint(self, checkpoint_file: str) -> int:
        """Load progress checkpoint."""
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, "r") as f:
                return int(f.read().strip())
        return 0


# Singleton instance
_nvd_service = None


def get_nvd_service(api_key: Optional[str] = None) -> NVDCompleteService:
    """Get or create NVD service instance."""
    global _nvd_service
    if _nvd_service is None:
        _nvd_service = NVDCompleteService(api_key=api_key)
    return _nvd_service
