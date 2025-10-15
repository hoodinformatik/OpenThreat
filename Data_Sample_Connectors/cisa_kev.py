
"""Sample connector: CISA Known Exploited Vulnerabilities (KEV).

Output: NDJSON; one object per CVE with a small, consistent shape for quick inspection.
"""
from __future__ import annotations

from typing import Dict, Any, Iterable, List
from datetime import datetime
from pathlib import Path

from common import http_session, write_ndjson, timestamped_path


CISA_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def fetch() -> Dict[str, Any]:
    s = http_session()
    r = s.get(CISA_URL, timeout=30)
    r.raise_for_status()
    return r.json()


def normalize(feed: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for v in feed.get("vulnerabilities", []):
        notes = v.get("notes", "") or ""
        refs = [u.strip() for u in notes.split(";") if u.strip()]
        yield {
            "source": "cisa_kev",
            "cve_id": v.get("cveID"),
            "title": v.get("vulnerabilityName"),
            "description": v.get("shortDescription"),
            "vendor": v.get("vendorProject"),
            "product": v.get("product"),
            "date_added": v.get("dateAdded"),
            "due_date": v.get("dueDate"),
            "cwes": v.get("cwes", []) or [],
            "references": refs,
            "exploited_in_the_wild": True,
        }


def run(out_dir: Path) -> Path:
    data = fetch()
    items = list(normalize(data))
    out_path = timestamped_path(out_dir, "cisa_kev")
    write_ndjson(items, out_path)
    return out_path


if __name__ == "__main__":
    dest = run(Path(__file__).parent / "out")
    print(dest)