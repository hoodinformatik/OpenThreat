
from __future__ import annotations
from typing import Dict
from .models import Vulnerability

SEVERITY_MAP = {
    None: "UNKNOWN",
    "NONE": "LOW",
    "LOW": "LOW",
    "MEDIUM": "MEDIUM",
    "HIGH": "HIGH",
    "CRITICAL": "CRITICAL",
}

def map_nvd_record(rec: Dict) -> Vulnerability | None:
    cve = rec.get("cve_id")
    if not cve:
        return None
    products = []
    vendors = rec.get("vendors") or []
    prods = rec.get("products") or []
    if vendors or prods:
        for v in vendors or ["unknown"]:
            for p in prods or ["unknown"]:
                products.append(f"{v}:{p}")
    return Vulnerability(
        cve_id=cve,
        title=cve,
        description=None,
        cvss_score=rec.get("cvss"),
        severity=SEVERITY_MAP.get((rec.get("severity") or "").upper(), "UNKNOWN"),
        published_at=rec.get("published"),
        modified_at=rec.get("last_modified"),
        affected_products=products,
        exploited_in_the_wild=False,
        source_tags=["NVD"],
    )
