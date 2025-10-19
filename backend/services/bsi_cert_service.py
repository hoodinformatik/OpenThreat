"""
BSI CERT-Bund Service - Fetch security advisories from German CERT

This service fetches security advisories from BSI CERT-Bund which provides:
- German security advisories
- CVE references
- Severity ratings
- Affected products
- Recommendations
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy.orm import Session

from backend.models import Vulnerability

logger = logging.getLogger(__name__)


class BSICertService:
    """Service for fetching BSI CERT-Bund security advisories"""

    RSS_URL = "https://wid.cert-bund.de/content/public/securityAdvisory/rss"
    ADVISORY_BASE_URL = "https://wid.cert-bund.de/portal/advisory/"

    def __init__(self):
        """Initialize BSI CERT service."""
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "OpenThreat/0.1.0 (Security Research)"}
        )

    def fetch_advisories(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch security advisories from BSI CERT-Bund RSS feed.

        Args:
            limit: Maximum number of advisories to fetch

        Returns:
            List of advisory dictionaries
        """
        try:
            logger.info("Fetching BSI CERT-Bund advisories...")

            response = self.session.get(self.RSS_URL, timeout=30)
            response.raise_for_status()

            # Parse RSS XML
            root = ET.fromstring(response.content)

            advisories = []
            items = root.findall(".//item")

            if limit:
                items = items[:limit]

            for item in items:
                advisory = self._parse_rss_item(item)
                if advisory:
                    advisories.append(advisory)

            logger.info(f"Fetched {len(advisories)} BSI CERT-Bund advisories")
            return advisories

        except Exception as e:
            logger.error(f"Failed to fetch BSI CERT-Bund advisories: {e}")
            return []

    def _parse_rss_item(self, item: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS item into advisory dictionary.

        Args:
            item: XML element representing RSS item

        Returns:
            Advisory dictionary or None
        """
        try:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")

            # Extract advisory ID from link
            # Link format: https://wid.cert-bund.de/portal/wid/securityadvisory?name=WID-SEC-2025-2308
            advisory_id = None
            if "name=" in link:
                advisory_id = link.split("name=")[-1]

            # Parse publication date
            published_at = None
            if pub_date:
                try:
                    # RSS date format: "Wed, 16 Oct 2024 10:00:00 +0200"
                    published_at = datetime.strptime(
                        pub_date, "%a, %d %b %Y %H:%M:%S %z"
                    )
                except:
                    pass

            # Extract CVE IDs from title and description
            cve_ids = self._extract_cve_ids(title + " " + description)

            # Extract severity from title
            severity = self._extract_severity(title)

            return {
                "advisory_id": advisory_id,
                "title": title,
                "description": description,
                "link": link,
                "published_at": published_at,
                "cve_ids": cve_ids,
                "severity": severity,
                "source": "bsi_cert",
            }

        except Exception as e:
            logger.error(f"Failed to parse RSS item: {e}")
            return None

    def _extract_severity(self, title: str) -> Optional[str]:
        """
        Extract severity from BSI CERT title.

        BSI uses: [kritisch], [hoch], [mittel], [niedrig]

        Args:
            title: Advisory title

        Returns:
            Severity level (CRITICAL, HIGH, MEDIUM, LOW) or None
        """
        title_lower = title.lower()

        if "[kritisch]" in title_lower:
            return "CRITICAL"
        elif "[hoch]" in title_lower:
            return "HIGH"
        elif "[mittel]" in title_lower:
            return "MEDIUM"
        elif "[niedrig]" in title_lower:
            return "LOW"

        return None

    def _extract_cve_ids(self, text: str) -> List[str]:
        """
        Extract CVE IDs from text.

        Args:
            text: Text to search for CVE IDs

        Returns:
            List of CVE IDs
        """
        import re

        pattern = r"CVE-\d{4}-\d{4,7}"
        return list(set(re.findall(pattern, text)))

    def enrich_vulnerabilities(self, db: Session) -> int:
        """
        Enrich existing vulnerabilities with BSI CERT-Bund information.

        Adds German descriptions and BSI references to CVEs.

        Args:
            db: Database session

        Returns:
            Number of vulnerabilities enriched
        """
        advisories = self.fetch_advisories()
        enriched_count = 0

        for advisory in advisories:
            cve_ids = advisory.get("cve_ids", [])

            for cve_id in cve_ids:
                # Find vulnerability in database
                vuln = (
                    db.query(Vulnerability)
                    .filter(Vulnerability.cve_id == cve_id)
                    .first()
                )

                if vuln:
                    # Add BSI reference
                    references = vuln.references or []
                    bsi_ref = {
                        "url": advisory["link"],
                        "source": "bsi_cert",
                        "type": "advisory",
                        "title": advisory["title"],
                    }

                    # Check if reference already exists
                    if not any(r.get("url") == bsi_ref["url"] for r in references):
                        references.append(bsi_ref)
                        vuln.references = references

                    # Add BSI to sources
                    sources = vuln.sources or []
                    if "bsi_cert" not in sources:
                        sources.append("bsi_cert")
                        vuln.sources = sources

                    # Add German description as source tag
                    source_tags = vuln.source_tags or []
                    german_desc = {
                        "source": "bsi_cert",
                        "description_de": advisory["description"],
                    }
                    source_tags.append(german_desc)
                    vuln.source_tags = source_tags

                    vuln.updated_at = datetime.utcnow()
                    enriched_count += 1

        if enriched_count > 0:
            db.commit()
            logger.info(
                f"Enriched {enriched_count} vulnerabilities with BSI CERT-Bund data"
            )

        return enriched_count

    def get_advisory_details(self, advisory_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific advisory.

        Args:
            advisory_id: BSI CERT advisory ID

        Returns:
            Advisory details or None
        """
        try:
            url = f"{self.ADVISORY_BASE_URL}{advisory_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse HTML for detailed information
            # This would require BeautifulSoup for proper parsing
            # For now, return basic info
            return {
                "advisory_id": advisory_id,
                "url": url,
                "content": response.text[:1000],  # First 1000 chars
            }

        except Exception as e:
            logger.error(f"Failed to fetch advisory details: {e}")
            return None


# Singleton instance
_bsi_cert_service = None


def get_bsi_cert_service() -> BSICertService:
    """Get or create BSI CERT service instance."""
    global _bsi_cert_service
    if _bsi_cert_service is None:
        _bsi_cert_service = BSICertService()
    return _bsi_cert_service
