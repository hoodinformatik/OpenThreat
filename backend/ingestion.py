"""
Data ingestion pipeline to load CVE data from NDJSON files into the database.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import IngestionRun, Vulnerability


def calculate_priority_score(vuln_data: Dict[str, Any]) -> float:
    """
    Calculate priority score based on multiple factors:
    - Exploited in the wild: +0.5
    - CVSS score: 0.0-0.4 (normalized from 0-10)
    - Recency: 0.0-0.1 (newer = higher)

    Returns a score between 0.0 and 1.0
    """
    score = 0.0

    # Exploitation status (50% weight)
    if vuln_data.get("exploited_in_the_wild"):
        score += 0.5

    # CVSS score (40% weight)
    cvss = vuln_data.get("cvss_score")
    if cvss:
        try:
            cvss_float = float(cvss)
            score += (cvss_float / 10.0) * 0.4
        except (ValueError, TypeError):
            pass

    # Recency (10% weight) - published in last 30 days gets full points
    published = vuln_data.get("published") or vuln_data.get("published_at")
    if published:
        try:
            if isinstance(published, str):
                pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            else:
                pub_date = published

            days_old = (datetime.now(timezone.utc) - pub_date).days
            if days_old < 30:
                score += 0.1 * (1 - (days_old / 30))
        except Exception:
            pass

    return min(score, 1.0)


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime string to datetime object."""
    if not dt_str:
        return None

    try:
        if isinstance(dt_str, datetime):
            return dt_str

        # Handle ISO format with Z
        dt_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)

        # Ensure timezone aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except Exception:
        return None


def parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """Parse date string to date object."""
    if not date_str:
        return None

    try:
        if len(date_str) == 10:  # YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        pass

    return None


def normalize_severity(severity: Optional[str]) -> Optional[str]:
    """Normalize severity string to standard values."""
    if not severity:
        return "UNKNOWN"

    severity_upper = severity.upper()
    valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]

    if severity_upper in valid_severities:
        return severity_upper

    return "UNKNOWN"


def ingest_vulnerability(db: Session, vuln_data: Dict[str, Any]) -> tuple[bool, bool]:
    """
    Ingest a single vulnerability record.

    Returns:
        (inserted, updated) - tuple of booleans
    """
    cve_id = vuln_data.get("cve_id")
    if not cve_id:
        return False, False

    # Check if vulnerability already exists
    existing = db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()

    # Calculate priority score
    priority_score = calculate_priority_score(vuln_data)

    # Prepare data
    vuln_dict = {
        "cve_id": cve_id,
        "title": vuln_data.get("title") or vuln_data.get("vulnerabilityName") or cve_id,
        "description": vuln_data.get("description")
        or vuln_data.get("shortDescription"),
        "cvss_score": vuln_data.get("cvss_score") or vuln_data.get("cvss"),
        "cvss_vector": vuln_data.get("cvss_vector"),
        "severity": normalize_severity(vuln_data.get("severity")),
        "published_at": parse_datetime(
            vuln_data.get("published")
            or vuln_data.get("published_at")
            or vuln_data.get("dateAdded")
        ),
        "modified_at": parse_datetime(
            vuln_data.get("last_modified") or vuln_data.get("modified_at")
        ),
        "exploited_in_the_wild": vuln_data.get("exploited_in_the_wild", False),
        "cisa_due_date": parse_date(
            vuln_data.get("cisa_due_date") or vuln_data.get("dueDate")
        ),
        "cwe_ids": vuln_data.get("cwe_ids") or vuln_data.get("cwes") or [],
        "affected_products": vuln_data.get("affected_products", []),
        "vendors": vuln_data.get("vendors", []),
        "products": vuln_data.get("products", []),
        "references": vuln_data.get("references", []),
        "sources": (
            vuln_data.get("sources", [vuln_data.get("source")])
            if vuln_data.get("source")
            else []
        ),
        "source_tags": vuln_data.get("source_tags", []),
        "priority_score": priority_score,
    }

    if existing:
        # Update existing record
        for key, value in vuln_dict.items():
            if key != "cve_id":  # Don't update primary identifier
                setattr(existing, key, value)

        existing.updated_at = datetime.now(timezone.utc)
        return False, True
    else:
        # Insert new record
        new_vuln = Vulnerability(**vuln_dict)
        db.add(new_vuln)
        return True, False


def ingest_from_ndjson(db: Session, file_path: Path, source: str) -> Dict[str, int]:
    """
    Ingest vulnerabilities from an NDJSON file.

    Returns:
        Dictionary with statistics: {fetched, inserted, updated, failed}
    """
    stats = {
        "fetched": 0,
        "inserted": 0,
        "updated": 0,
        "failed": 0,
    }

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                vuln_data = json.loads(line)
                stats["fetched"] += 1

                inserted, updated = ingest_vulnerability(db, vuln_data)

                if inserted:
                    stats["inserted"] += 1
                elif updated:
                    stats["updated"] += 1

                # Commit every 100 records
                if stats["fetched"] % 100 == 0:
                    db.commit()

            except Exception as e:
                stats["failed"] += 1
                print(f"Error on line {line_num}: {e}")

    # Final commit
    db.commit()

    return stats


def run_ingestion(
    file_path: Path, source: str, db: Optional[Session] = None
) -> IngestionRun:
    """
    Run a complete ingestion process with tracking.

    Args:
        file_path: Path to NDJSON file
        source: Source identifier (e.g., "deduplicated_cves")
        db: Optional database session (creates new one if not provided)

    Returns:
        IngestionRun record with statistics
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    # Create ingestion run record
    run = IngestionRun(
        source=source,
        status="running",
        started_at=datetime.now(timezone.utc),
        records_fetched=0,
        records_inserted=0,
        records_updated=0,
        records_failed=0,
    )
    db.add(run)
    db.commit()

    try:
        # Run ingestion
        stats = ingest_from_ndjson(db, file_path, source)

        # Update run record
        run.status = "success"
        run.completed_at = datetime.now(timezone.utc)
        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
        run.records_fetched = stats["fetched"]
        run.records_inserted = stats["inserted"]
        run.records_updated = stats["updated"]
        run.records_failed = stats["failed"]

        db.commit()

        print(f"Ingestion complete: {stats}")

    except Exception as e:
        # Mark run as failed
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
        run.error_message = str(e)

        db.commit()

        print(f"Ingestion failed: {e}")
        raise

    finally:
        if close_db:
            db.close()

    return run


def get_ingestion_stats(db: Session) -> Dict[str, Any]:
    """Get overall ingestion statistics."""
    total_vulns = db.query(func.count(Vulnerability.id)).scalar()
    exploited_vulns = (
        db.query(func.count(Vulnerability.id))
        .filter(Vulnerability.exploited_in_the_wild == True)
        .scalar()
    )

    recent_runs = (
        db.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(10).all()
    )

    return {
        "total_vulnerabilities": total_vulns,
        "exploited_vulnerabilities": exploited_vulns,
        "recent_runs": [
            {
                "id": run.id,
                "source": run.source,
                "status": run.status,
                "started_at": run.started_at.isoformat(),
                "records_inserted": run.records_inserted,
                "records_updated": run.records_updated,
            }
            for run in recent_runs
        ],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m backend.ingestion <ndjson_file> [source_name]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    source = sys.argv[2] if len(sys.argv) > 2 else "manual"

    print(f"Starting ingestion from {file_path}...")

    # Create a session to keep the run object attached
    db = SessionLocal()
    try:
        run = run_ingestion(file_path, source, db)

        # Refresh to get latest data
        db.refresh(run)

        print(f"\nIngestion Run #{run.id}")
        print(f"Status: {run.status}")
        print(f"Fetched: {run.records_fetched}")
        print(f"Inserted: {run.records_inserted}")
        print(f"Updated: {run.records_updated}")
        print(f"Failed: {run.records_failed}")
        print(f"Duration: {run.duration_seconds:.2f}s")
    finally:
        db.close()
