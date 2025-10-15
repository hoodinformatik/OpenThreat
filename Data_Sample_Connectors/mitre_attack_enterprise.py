
"""Sample connector: MITRE ATT&CK (Enterprise) techniques & tactics.

For sampling we pull the MITRE CTI JSON from GitHub raw and extract basic fields.
This file is large; consider caching locally if needed.
"""
from __future__ import annotations

from typing import Dict, Any, Iterable
from pathlib import Path

from common import http_session, write_ndjson, timestamped_path


MITRE_ENTERPRISE_JSON = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"


def fetch() -> Dict[str, Any]:
    s = http_session()
    r = s.get(MITRE_ENTERPRISE_JSON, timeout=120)
    r.raise_for_status()
    return r.json()


def normalize(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for obj in payload.get("objects", []):
        t = obj.get("type")
        if t in ("attack-pattern", "x-mitre-tactic"):
            yield {
                "source": "mitre_attack",
                "stix_type": t,
                "id": obj.get("id"),
                "name": obj.get("name"),
                "external_id": _external_id(obj),
                "description": obj.get("description"),
                "revoked": obj.get("revoked", False),
                "deprecated": obj.get("x_mitre_deprecated", False),
            }


def _external_id(obj: Dict[str, Any]) -> str | None:
    for ref in obj.get("external_references", []) or []:
        if ref.get("source_name") in ("mitre-attack", "mitre-attack"):
            return ref.get("external_id")
    return None


def run(out_dir: Path) -> Path:
    data = fetch()
    items = list(normalize(data))
    out_path = timestamped_path(out_dir, "mitre_attack_enterprise")
    write_ndjson(items, out_path)
    return out_path


if __name__ == "__main__":
    dest = run(Path(__file__).parent / "out")
    print(dest)
