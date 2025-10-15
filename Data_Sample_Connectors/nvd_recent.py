
"""Sample connector: NVD recent vulnerabilities (modified in last 7 days).

Notes:
- Without an API key this is rate-limited; you can set env NVD_API_KEY or pass ?apiKey=... to be polite.
- Output: NDJSON with a compact subset (CVE, CVSS, severity, published/lastModified, vendors/products if available).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Iterable, List
from pathlib import Path

from common import http_session, write_ndjson, timestamped_path


BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch() -> Dict[str, Any]:
    s = http_session()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    params = {
        "lastModStartDate": iso(start),
        "lastModEndDate": iso(now),
        "startIndex": 0,
        "resultsPerPage": 2000,
    }
    api_key = os.getenv("NVD_API_KEY")
    if api_key:
        params["apiKey"] = api_key
    r = s.get(BASE, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def normalize(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for item in payload.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id")
        published = cve.get("published")
        last_modified = cve.get("lastModified")
        # CVSS (prefer v3.x baseScore)
        metrics = cve.get("metrics", {})
        cvss = None
        severity = None
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            arr = metrics.get(key) or []
            if arr:
                m = arr[0]
                cvss = m.get("cvssData", {}).get("baseScore") or m.get("baseScore")
                severity = m.get("cvssData", {}).get("baseSeverity") or m.get("baseSeverity")
                break
        
        vendors = set()
        products = set()
        for conf in (cve.get("configurations") or []):
            for node in conf.get("nodes", []):
                for cpe in node.get("cpeMatch", []):
                    uri = cpe.get("criteria") or cpe.get("cpe23Uri") or ""
                    parts = uri.split(":")
                    if len(parts) >= 5:
                        vendors.add(parts[3])
                        products.add(parts[4])
        yield {
            "source": "nvd",
            "cve_id": cve_id,
            "published": published,
            "last_modified": last_modified,
            "cvss": cvss,
            "severity": severity,
            "vendors": sorted(vendors),
            "products": sorted(products),
            "exploited_in_the_wild": False,
        }


def run(out_dir: Path) -> Path:
    data = fetch()
    items = list(normalize(data))
    out_path = timestamped_path(out_dir, "nvd_recent")
    write_ndjson(items, out_path)
    return out_path


if __name__ == "__main__":
    dest = run(Path(__file__).parent / "out")
    print(dest)
