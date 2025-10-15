from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Dict, Iterable, List, Optional
from datetime import date

from .models import Vulnerability, Reference


URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def extract_urls(text: Optional[str]) -> List[str]:
    """Extract http/https URLs from a free-text field (like CISA 'notes')."""
    if not text:
        return []
    return [m.group(0).strip().rstrip('.,);]') for m in URL_RE.finditer(text)]


def safe_references(refs_raw: Iterable[str]) -> List[Reference]:
    """Return only valid HTTP(S) URLs as Reference objects, skip everything else."""
    out: List[Reference] = []
    for u in refs_raw or []:
        if not u:
            continue
        u = u.strip()
        parsed = urlparse(u)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            try:
                out.append(Reference(url=u))  # type defaults to 'other'
            except Exception:
                # If Pydantic still dislikes it, skip silently
                continue
    return out


def map_cisa_record(rec: Dict) -> Vulnerability | None:
    """Map either a raw CISA KEV item or our sample NDJSON shape to Vulnerability.

    Supported inputs:
    - Raw CISA dict (keys like 'cveID', 'vulnerabilityName', 'notes', ...)
    - Sample NDJSON dict from Data_Sample_Connectors/cisa_kev.py (keys like 'cve_id', 'references', ...)
    """
    # Case 1: raw CISA feed item
    if rec.get("cveID") and not rec.get("cve_id"):
        notes = rec.get("notes") or ""
        # URLs are often mixed with text and separated by ';' – extract via regex
        urls = extract_urls(notes)
        refs = safe_references(urls)

        vendor = (rec.get("vendorProject") or "").strip()
        product = (rec.get("product") or "").strip()
        affected: List[str] = []
        if vendor or product:
            affected.append(":".join([x for x in (vendor, product) if x]))

        try:
            due = date.fromisoformat(rec["dueDate"]) if rec.get("dueDate") else None
        except Exception:
            due = None

        return Vulnerability(
            cve_id=rec["cveID"],
            title=rec.get("vulnerabilityName") or rec["cveID"],
            description=rec.get("shortDescription"),
            published_at=rec.get("dateAdded"),
            cisa_due_date=due,
            exploited_in_the_wild=True,
            cwe_ids=rec.get("cwes") or [],
            affected_products=affected,
            references=refs,
            source_tags=["CISA"],
        )

    # Case 2: our sample NDJSON shape
    cve = rec.get("cve_id")
    if not cve:
        return None

    refs = safe_references(rec.get("references", []))

    vendor = rec.get("vendor")
    product = rec.get("product")
    affected: List[str] = []
    if vendor or product:
        affected.append(":".join([x for x in (vendor or "", product or "") if x]))

    try:
        due2 = date.fromisoformat(rec["due_date"]) if rec.get("due_date") else None
    except Exception:
        due2 = None

    return Vulnerability(
        cve_id=cve,
        title=rec.get("title") or cve,
        description=rec.get("description"),
        published_at=rec.get("date_added"),
        cisa_due_date=due2,
        exploited_in_the_wild=True,
        cwe_ids=rec.get("cwes") or [],
        affected_products=affected,
        references=refs,
        source_tags=["CISA"],
    )
