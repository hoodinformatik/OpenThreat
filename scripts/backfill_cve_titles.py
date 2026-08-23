"""
One-time backfill for CVEs stuck with a fabricated "Unknown Software" title.

Root cause: NVD hadn't finished CPE analysis for these CVEs at ingestion time
(empty `configurations`), so vendor/product were empty and the old title
logic literally wrote "Unknown Software" into simple_title. That logic is now
fixed (see backend/llm_service.py and
backend/services/nvd_complete_service.py), but existing rows in production
still carry the old bad title. This script re-enriches and re-titles them.

For each affected CVE:
  1. If it still has no vendor/product, try the CVE.org fallback lookup
     (same one now used during ingestion) to fill it in.
  2. Re-run title/description generation with the (possibly now-populated)
     vendor/product data.

Usage:
    python scripts/backfill_cve_titles.py --dry-run     # preview only
    python scripts/backfill_cve_titles.py                # apply
    python scripts/backfill_cve_titles.py --limit 50     # process a batch
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from sqlalchemy import or_

from backend.database import SessionLocal
from backend.models import Vulnerability
from backend.llm_service import get_llm_service
from backend.services.nvd_complete_service import NVDCompleteService


def find_broken_vulnerabilities(session, limit=None):
    query = session.query(Vulnerability).filter(
        or_(
            Vulnerability.simple_title.ilike("%unknown software%"),
            Vulnerability.simple_title.ilike("%in unknown%"),
        )
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def backfill(dry_run: bool = False, limit: int = None):
    session = SessionLocal()
    llm = get_llm_service(enabled=True)
    nvd = NVDCompleteService()

    try:
        broken = find_broken_vulnerabilities(session, limit=limit)

        if not broken:
            print("No CVEs with an \"Unknown Software\" title found. Nothing to do.")
            return

        print(f"Found {len(broken)} CVEs with a broken title.")
        print(f"Mode: {'DRY RUN (no changes will be saved)' if dry_run else 'APPLY'}")
        print()

        updated = 0
        still_unknown = 0
        errors = 0

        for vuln in broken:
            try:
                print(f"{vuln.cve_id}: was \"{vuln.simple_title}\"")

                vendors = vuln.vendors or []
                products = vuln.products or []

                # Try to recover real vendor/product data if we still don't have any.
                if not vendors and not products:
                    fallback = nvd._fetch_vendor_product_fallback(vuln.cve_id)
                    if fallback:
                        vendors = list(fallback.keys())
                        for prods in fallback.values():
                            products.extend(prods)

                summary = llm.generate_cve_summary(
                    cve_id=vuln.cve_id,
                    original_title=vuln.title,
                    description=vuln.description or "",
                    cvss_score=vuln.cvss_score,
                    severity=vuln.severity,
                    vendors=vendors,
                    products=products,
                    published_at=vuln.published_at,
                )

                new_title = summary["simple_title"]
                print(f"  -> \"{new_title}\"")

                if "unknown software" in new_title.lower():
                    still_unknown += 1

                if not dry_run:
                    vuln.vendors = vendors
                    vuln.products = products
                    vuln.simple_title = new_title
                    vuln.simple_description = summary["simple_description"]
                    vuln.llm_processed = True
                    vuln.llm_processed_at = datetime.now(timezone.utc)
                    vuln.updated_at = datetime.now(timezone.utc)
                    session.commit()

                updated += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                errors += 1
                session.rollback()

        print()
        print(f"Processed: {updated}")
        if still_unknown:
            print(f"Still generic after backfill (no vendor/product available anywhere): {still_unknown}")
        if errors:
            print(f"Errors: {errors}")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill CVEs with an 'Unknown Software' title")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    parser.add_argument("--limit", type=int, help="Only process up to N broken CVEs")
    args = parser.parse_args()

    backfill(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
