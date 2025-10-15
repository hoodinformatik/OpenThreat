"""
NVD CVE Connector - Fetches CVE data from NVD API 2.0.

This connector fetches CVEs with more comprehensive data than nvd_recent.py.
It can fetch by date range, specific CVE IDs, or keyword search.

Usage:
    python nvd_cve.py                    # Last 7 days
    python nvd_cve.py --days 30          # Last 30 days
    python nvd_cve.py --cve CVE-2024-1234  # Specific CVE

Environment:
    NVD_API_KEY - Optional API key for higher rate limits (recommended)
"""
from __future__ import annotations

import os
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Iterable, List, Optional
from pathlib import Path

from common import http_session, write_ndjson, timestamped_path


BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def iso(dt: datetime) -> str:
    """Convert datetime to ISO format for NVD API."""
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_cves(
    days: int = 7,
    cve_id: Optional[str] = None,
    keyword: Optional[str] = None,
    results_per_page: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Fetch CVEs from NVD API with pagination support.
    
    Args:
        days: Number of days to look back (default: 7)
        cve_id: Specific CVE ID to fetch
        keyword: Keyword search term
        results_per_page: Results per page (max 2000)
    
    Returns:
        List of CVE items
    """
    s = http_session()
    api_key = os.getenv("NVD_API_KEY")
    
    all_items = []
    start_index = 0
    
    while True:
        params: Dict[str, Any] = {
            "startIndex": start_index,
            "resultsPerPage": results_per_page,
        }
        
        if api_key:
            params["apiKey"] = api_key
        
        if cve_id:
            params["cveId"] = cve_id
        elif keyword:
            params["keywordSearch"] = keyword
        else:
            # Date range search
            now = datetime.now(timezone.utc)
            start = now - timedelta(days=days)
            params["lastModStartDate"] = iso(start)
            params["lastModEndDate"] = iso(now)
        
        print(f"Fetching CVEs (startIndex={start_index})...")
        r = s.get(BASE, params=params, timeout=60)
        r.raise_for_status()
        
        data = r.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        if not vulnerabilities:
            break
        
        all_items.extend(vulnerabilities)
        
        # Check if there are more results
        total_results = data.get("totalResults", 0)
        if start_index + len(vulnerabilities) >= total_results:
            break
        
        start_index += results_per_page
        
        # If we have a specific CVE, we're done
        if cve_id:
            break
    
    print(f"Fetched {len(all_items)} CVEs")
    return all_items


def extract_references(cve: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract reference URLs and types from CVE data."""
    refs = []
    for ref in cve.get("references", []):
        url = ref.get("url")
        if not url:
            continue
        
        # Determine reference type
        tags = ref.get("tags", [])
        ref_type = "other"
        
        if "Patch" in tags:
            ref_type = "patch"
        elif "Vendor Advisory" in tags or "Third Party Advisory" in tags:
            ref_type = "advisory"
        elif "Exploit" in tags:
            ref_type = "exploit"
        elif any(t in tags for t in ["Release Notes", "Product"]):
            ref_type = "vendor"
        
        refs.append({
            "url": url,
            "type": ref_type,
            "tags": tags,
        })
    
    return refs


def extract_cwe_ids(cve: Dict[str, Any]) -> List[str]:
    """Extract CWE IDs from CVE data."""
    cwe_ids = []
    for weakness in cve.get("weaknesses", []):
        for desc in weakness.get("description", []):
            value = desc.get("value", "")
            if value.startswith("CWE-"):
                cwe_ids.append(value)
    return list(set(cwe_ids))  # Deduplicate


def normalize(vulnerabilities: List[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    """
    Normalize NVD CVE data to our internal format.
    
    Yields:
        Normalized CVE records
    """
    for item in vulnerabilities:
        cve = item.get("cve", {})
        cve_id = cve.get("id")
        
        if not cve_id:
            continue
        
        # Timestamps
        published = cve.get("published")
        last_modified = cve.get("lastModified")
        
        # Description (prefer English)
        description = None
        for desc in cve.get("descriptions", []):
            if desc.get("lang") == "en":
                description = desc.get("value")
                break
        
        # CVSS scores (prefer v3.1 > v3.0 > v2.0)
        metrics = cve.get("metrics", {})
        cvss_score = None
        cvss_vector = None
        severity = None
        
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            arr = metrics.get(key, [])
            if arr:
                m = arr[0]
                cvss_data = m.get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
                severity = cvss_data.get("baseSeverity")
                break
        
        # Extract vendors and products from CPE
        vendors = set()
        products = set()
        affected_products = []
        
        for conf in cve.get("configurations", []):
            for node in conf.get("nodes", []):
                for cpe in node.get("cpeMatch", []):
                    uri = cpe.get("criteria") or cpe.get("cpe23Uri") or ""
                    parts = uri.split(":")
                    if len(parts) >= 5:
                        vendor = parts[3]
                        product = parts[4]
                        version = parts[5] if len(parts) > 5 else ""
                        
                        vendors.add(vendor)
                        products.add(product)
                        
                        # Build affected product string
                        if version and version != "*":
                            affected_products.append(f"{vendor}:{product}:{version}")
                        else:
                            affected_products.append(f"{vendor}:{product}")
        
        # References
        references = extract_references(cve)
        
        # CWE IDs
        cwe_ids = extract_cwe_ids(cve)
        
        yield {
            "source": "nvd_cve",
            "cve_id": cve_id,
            "description": description,
            "published": published,
            "last_modified": last_modified,
            "cvss_score": cvss_score,
            "cvss_vector": cvss_vector,
            "severity": severity,
            "vendors": sorted(vendors),
            "products": sorted(products),
            "affected_products": affected_products,
            "cwe_ids": cwe_ids,
            "references": references,
            "exploited_in_the_wild": False,  # NVD doesn't track this directly
        }


def run(
    out_dir: Path,
    days: int = 7,
    cve_id: Optional[str] = None,
    keyword: Optional[str] = None,
) -> Path:
    """
    Run the NVD CVE connector.
    
    Args:
        out_dir: Output directory
        days: Number of days to look back
        cve_id: Specific CVE ID to fetch
        keyword: Keyword search term
    
    Returns:
        Path to output file
    """
    vulnerabilities = fetch_cves(days=days, cve_id=cve_id, keyword=keyword)
    items = list(normalize(vulnerabilities))
    
    out_path = timestamped_path(out_dir, "nvd_cve")
    count = write_ndjson(items, out_path)
    print(f"Wrote {count} CVEs to {out_path}")
    
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch CVEs from NVD API")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--cve", type=str, help="Specific CVE ID to fetch")
    parser.add_argument("--keyword", type=str, help="Keyword search term")
    
    args = parser.parse_args()
    
    dest = run(
        Path(__file__).parent / "out",
        days=args.days,
        cve_id=args.cve,
        keyword=args.keyword,
    )
    print(f"Output: {dest}")
