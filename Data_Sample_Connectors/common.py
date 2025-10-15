
import time
import json
from pathlib import Path
from typing import Iterable, Dict, Any, Optional

import requests
from requests.adapters import HTTPAdapter, Retry


def http_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    s.headers.update({"User-Agent": "ptid-sample-connectors/0.1"})
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s


def write_ndjson(items: Iterable[Dict[str, Any]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1
    return count


def timestamped_path(out_dir: Path, base: str, ext: str = "ndjson") -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return out_dir / f"{base}-{ts}.{ext}"
