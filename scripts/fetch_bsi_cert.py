#!/usr/bin/env python3
"""
Fetch and enrich vulnerabilities with BSI CERT-Bund data

Usage:
    # Fetch and enrich existing CVEs
    python scripts/fetch_bsi_cert.py
    
    # Just show what would be enriched (dry-run)
    python scripts/fetch_bsi_cert.py --dry-run
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.bsi_cert_service import get_bsi_cert_service
from backend.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Fetch BSI CERT-Bund advisories and enrich CVEs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be enriched without making changes'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of advisories to fetch'
    )
    
    args = parser.parse_args()
    
    try:
        # Get BSI CERT service
        bsi_service = get_bsi_cert_service()
        
        # Fetch advisories
        logger.info("Fetching BSI CERT-Bund advisories...")
        advisories = bsi_service.fetch_advisories(limit=args.limit)
        
        if not advisories:
            logger.warning("No advisories fetched")
            return
        
        logger.info(f"Fetched {len(advisories)} advisories")
        
        # Show summary
        total_cves = sum(len(adv.get("cve_ids", [])) for adv in advisories)
        logger.info(f"Found {total_cves} CVE references in advisories")
        
        # Show examples
        print("\n" + "="*60)
        print("BSI CERT-BUND ADVISORIES")
        print("="*60)
        
        for i, advisory in enumerate(advisories[:5], 1):
            print(f"\n{i}. {advisory['title']}")
            print(f"   Link: {advisory['link']}")
            print(f"   CVEs: {', '.join(advisory['cve_ids']) if advisory['cve_ids'] else 'None'}")
            print(f"   Published: {advisory['published_at']}")
        
        if len(advisories) > 5:
            print(f"\n... and {len(advisories) - 5} more advisories")
        
        print("\n" + "="*60)
        
        if args.dry_run:
            logger.info("Dry-run mode - no changes made")
            return
        
        # Enrich vulnerabilities
        logger.info("Enriching vulnerabilities with BSI CERT-Bund data...")
        db = next(get_db())
        
        try:
            enriched = bsi_service.enrich_vulnerabilities(db)
            logger.info(f"✅ Successfully enriched {enriched} vulnerabilities")
            
            if enriched > 0:
                logger.info("BSI CERT-Bund references and German descriptions added")
            
        finally:
            db.close()
        
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
