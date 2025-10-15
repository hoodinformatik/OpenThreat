
from __future__ import annotations

import json
from glob import glob
from pathlib import Path
from typing import Iterable, Dict, Any

from mappers.models import Vulnerability, Technique
from mappers.cisa_mapper import map_cisa_record
from mappers.nvd_mapper import map_nvd_record
from mappers.mitre_mapper import map_mitre_record


def read_ndjson(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def latest_file(pattern: str) -> Path | None:
    files = sorted(glob(pattern))
    return Path(files[-1]) if files else None


def normalize_all(samples_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Vulnerabilities: CISA + NVD
    vulns: list[Vulnerability] = []

    cisa_path = latest_file(str(samples_dir / "cisa_kev-*.ndjson"))
    if cisa_path:
        for rec in read_ndjson(cisa_path):
            v = map_cisa_record(rec)
            if v:
                vulns.append(v)

    nvd_path = latest_file(str(samples_dir / "nvd_recent-*.ndjson"))
    if nvd_path:
        for rec in read_ndjson(nvd_path):
            v = map_nvd_record(rec)
            if v:
                vulns.append(v)

    # Deduplicate by cve_id (prefer CISA over NVD for exploited flag)
    merged: dict[str, Vulnerability] = {}
    for v in vulns:
        key = v.cve_id
        if key in merged:
            # merge fields conservatively
            base = merged[key]
            base.exploited_in_the_wild = base.exploited_in_the_wild or v.exploited_in_the_wild
            base.cvss_score = base.cvss_score or v.cvss_score
            base.severity = base.severity if base.severity != "UNKNOWN" else v.severity
            # merge affected products
            ap = { *base.affected_products, *v.affected_products }
            base.affected_products = sorted(ap)
            # keep earliest published_at, latest modified_at
            base.published_at = min([d for d in [base.published_at, v.published_at] if d], default=base.published_at)
            base.modified_at = max([d for d in [base.modified_at, v.modified_at] if d], default=base.modified_at)
            merged[key] = base
        else:
            merged[key] = v

    vulns_out = out_dir / "vulnerabilities.ndjson"
    with vulns_out.open("w", encoding="utf-8") as f:
        for v in merged.values():
            f.write(v.model_dump_json() + "\n")

    # Techniques (MITRE)
    mitre_path = latest_file(str(samples_dir / "mitre_attack_enterprise-*.ndjson"))
    tech_out = out_dir / "techniques.ndjson"
    if mitre_path:
        with tech_out.open("w", encoding="utf-8") as f:
            for rec in read_ndjson(mitre_path):
                t = map_mitre_record(rec)
                if t:
                    f.write(t.model_dump_json() + "\n")


if __name__ == "__main__":
    samples = Path("Data_Sample_Connectors/out")  # adjust for your repo
    out = Path(__file__).parent / "out"
    normalize_all(samples, out)
    print("Wrote normalized outputs to", out)
