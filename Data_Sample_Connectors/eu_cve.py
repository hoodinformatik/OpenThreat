"""
European CVE Connector - Fetches CVE data from CVE Search (CIRCL).

This connector uses the CVE Search API (cve.circl.lu) which aggregates CVE data
and provides additional European context. It helps identify CVEs that may be
duplicates of NVD data but provides alternative metadata.

Usage:
    python eu_cve.py                    # Recent CVEs (last 30)
    python eu_cve.py --limit 100        # Last 100 CVEs
    python eu_cve.py --cve CVE-2024-1234  # Specific CVE

API Documentation: https://cve.circl.lu/api/
"""
from __future__ import annotations

import argparse
from typing import Dict, Any, Iterable, List, Optional
from pathlib import Path
import time

from common import http_session, write_ndjson, timestamped_path


BASE = "https://cve.circl.lu/api"


def fetch_recent_cves(limit: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch recent CVEs from CVE Search API.
    
    Args:
        limit: Number of recent CVEs to fetch (default: 30)
    
    Returns:
        List of CVE records
    """
    s = http_session()
    url = f"{BASE}/last/{limit}"
    
    print(f"Fetching last {limit} CVEs from CVE Search...")
    r = s.get(url, timeout=30)
    r.raise_for_status()
    
    data = r.json()
    print(f"Fetched {len(data)} CVEs")
    return data


def fetch_cve_by_id(cve_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific CVE by ID.
    
    Args:
        cve_id: CVE identifier (e.g., CVE-2024-1234)
    
    Returns:
        CVE record or None if not found
    """
    s = http_session()
    url = f"{BASE}/cve/{cve_id}"
    
    print(f"Fetching {cve_id} from CVE Search...")
    r = s.get(url, timeout=30)
    
    if r.status_code == 404:
        print(f"CVE {cve_id} not found")
        return None
    
    r.raise_for_status()
    return r.json()


def fetch_by_vendor(vendor: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch CVEs by vendor name.
    
    Args:
        vendor: Vendor name
        limit: Maximum number of results
    
    Returns:
        List of CVE records
    """
    s = http_session()
    url = f"{BASE}/search/{vendor}"
    
    print(f"Searching CVEs for vendor: {vendor}...")
    r = s.get(url, timeout=30)
    r.raise_for_status()
    
    data = r.json()
    results = data.get("results", [])[:limit]
    print(f"Found {len(results)} CVEs for {vendor}")
    return results


def normalize(cves: List[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    """
    Normalize CVE Search data to our internal format.
    
    The CVE Search API provides data in a slightly different format than NVD.
    This function normalizes it to match our schema.
    
    Yields:
        Normalized CVE records
    """
    for cve in cves:
        cve_id = cve.get("id")
        
        if not cve_id:
            continue
        
        # Summary/Description
        summary = cve.get("summary", "")
        
        # Timestamps
        published = cve.get("Published")
        modified = cve.get("Modified") or cve.get("last-modified")
        
        # CVSS scores
        cvss_score = cve.get("cvss")
        cvss_vector = cve.get("cvss-vector")
        
        # Determine severity from CVSS score
        severity = None
        if cvss_score:
            try:
                score = float(cvss_score)
                if score >= 9.0:
                    severity = "CRITICAL"
                elif score >= 7.0:
                    severity = "HIGH"
                elif score >= 4.0:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
            except (ValueError, TypeError):
                pass
        
        # CWE
        cwe = cve.get("cwe")
        cwe_ids = []
        if cwe:
            if isinstance(cwe, str):
                if cwe.startswith("CWE-"):
                    cwe_ids = [cwe]
            elif isinstance(cwe, list):
                cwe_ids = [c for c in cwe if isinstance(c, str) and c.startswith("CWE-")]
        
        # Vendors and products
        vulnerable_config = cve.get("vulnerable_configuration", [])
        vulnerable_product = cve.get("vulnerable_product", [])
        
        vendors = set()
        products = set()
        affected_products = []
        
        # Parse CPE URIs
        for cpe_uri in vulnerable_config + vulnerable_product:
            if not cpe_uri:
                continue
            
            # CPE format: cpe:2.3:a:vendor:product:version:...
            # or cpe:/a:vendor:product:version
            parts = cpe_uri.replace("cpe:/", "cpe:2.3:").split(":")
            
            if len(parts) >= 5:
                vendor = parts[3]
                product = parts[4]
                version = parts[5] if len(parts) > 5 else ""
                
                if vendor and vendor != "*":
                    vendors.add(vendor)
                if product and product != "*":
                    products.add(product)
                
                # Build affected product string
                if version and version != "*":
                    affected_products.append(f"{vendor}:{product}:{version}")
                elif vendor and product:
                    affected_products.append(f"{vendor}:{product}")
        
        # References
        references = []
        refs_data = cve.get("references", [])
        if isinstance(refs_data, list):
            for ref_url in refs_data:
                if isinstance(ref_url, str):
                    references.append({
                        "url": ref_url,
                        "type": "other",
                    })
        
        # CAPEC (Common Attack Pattern Enumeration and Classification)
        capec = cve.get("capec", [])
        
        # Check if exploited
        # CVE Search doesn't directly track this, but we can infer from references
        exploited = False
        exploit_refs = [r for r in references if "exploit" in r.get("url", "").lower()]
        if exploit_refs:
            exploited = True
        
        yield {
            "source": "eu_cve_search",
            "cve_id": cve_id,
            "description": summary,
            "published": published,
            "last_modified": modified,
            "cvss_score": cvss_score,
            "cvss_vector": cvss_vector,
            "severity": severity,
            "vendors": sorted(vendors),
            "products": sorted(products),
            "affected_products": list(set(affected_products)),  # Deduplicate
            "cwe_ids": cwe_ids,
            "references": references,
            "capec": capec,
            "exploited_in_the_wild": exploited,
        }


def run(
    out_dir: Path,
    limit: int = 30,
    cve_id: Optional[str] = None,
    vendor: Optional[str] = None,
) -> Path:
    """
    Run the European CVE connector.
    
    Args:
        out_dir: Output directory
        limit: Number of recent CVEs to fetch
        cve_id: Specific CVE ID to fetch
        vendor: Vendor name to search for
    
    Returns:
        Path to output file
    """
    if cve_id:
        cve = fetch_cve_by_id(cve_id)
        cves = [cve] if cve else []
    elif vendor:
        cves = fetch_by_vendor(vendor, limit=limit)
    else:
        cves = fetch_recent_cves(limit=limit)
    
    items = list(normalize(cves))
    
    out_path = timestamped_path(out_dir, "eu_cve")
    count = write_ndjson(items, out_path)
    print(f"Wrote {count} CVEs to {out_path}")
    
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch CVEs from CVE Search (CIRCL)")
    parser.add_argument("--limit", type=int, default=30, help="Number of recent CVEs to fetch (default: 30)")
    parser.add_argument("--cve", type=str, help="Specific CVE ID to fetch")
    parser.add_argument("--vendor", type=str, help="Vendor name to search for")
    
    args = parser.parse_args()
    
    dest = run(
        Path(__file__).parent / "out",
        limit=args.limit,
        cve_id=args.cve,
        vendor=args.vendor,
    )
    print(f"Output: {dest}")
