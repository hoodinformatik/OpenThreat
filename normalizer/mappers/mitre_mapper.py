
from __future__ import annotations
from typing import Dict, Iterable
from .models import Technique

def map_mitre_record(rec: Dict) -> Technique | None:
    if rec.get("stix_type") not in ("attack-pattern", "x-mitre-tactic"):
        return None
    return Technique(
        id=rec.get("id"),
        name=rec.get("name") or rec.get("external_id") or rec.get("id"),
        external_id=rec.get("external_id"),
        description=rec.get("description"),
        revoked=bool(rec.get("revoked")),
        deprecated=bool(rec.get("deprecated")),
        source_tags=["MITRE"],
    )
