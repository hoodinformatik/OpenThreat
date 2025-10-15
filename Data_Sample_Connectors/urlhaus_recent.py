
"""Sample connector: abuse.ch URLhaus recent URLs.

Endpoints:
- https://urlhaus.abuse.ch/downloads/csv/  (large)
- https://urlhaus.abuse.ch/api/  (JSON API)

We use the JSON API: payload 'recenturls'.
"""
from __future__ import annotations

from typing import Dict, Any, Iterable
from pathlib import Path

from common import http_session, write_ndjson, timestamped_path


URLHAUS_API = "https://urlhaus.abuse.ch/api/"


def fetch() -> Dict[str, Any]:
    s = http_session()
    r = s.post(URLHAUS_API, json={"query": "recenturls"}, timeout=60)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        print("Skipping URLHAUS")



def normalize(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for e in payload.get("urls", []):
        yield {
            "source": "urlhaus",
            "indicator": e.get("url"),
            "type": "url",
            "host": e.get("host"),
            "status": e.get("url_status"),
            "first_seen": e.get("date_added"),
            "threat": e.get("threat"),
            "tags": e.get("tags") or [],
            "reporter": e.get("reporter"),
        }


def run(out_dir: Path) -> Path:
    data = fetch()
    items = list(normalize(data))
    out_path = timestamped_path(out_dir, "urlhaus_recent")
    write_ndjson(items, out_path)
    return out_path


if __name__ == "__main__":
    dest = run(Path(__file__).parent / "out")
    print(dest)
