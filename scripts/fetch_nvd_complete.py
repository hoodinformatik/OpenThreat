#!/usr/bin/env python3
"""
NVD Complete Fetch Script

Usage:
    # Fetch all CVEs from 1999 to present
    python scripts/fetch_nvd_complete.py
    
    # Fetch specific year range
    python scripts/fetch_nvd_complete.py --start-year 2020 --end-year 2024
    
    # Fetch recent changes (last 7 days)
    python scripts/fetch_nvd_complete.py --recent --days 7
    
    # Use API key for faster fetching
    export NVD_API_KEY=your_api_key_here
    python scripts/fetch_nvd_complete.py
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.nvd_complete_service import get_nvd_service
from backend.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nvd_fetch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Fetch CVEs from NVD API 2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=1999,
        help='Starting year (default: 1999)'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        default=None,
        help='Ending year (default: current year)'
    )
    
    parser.add_argument(
        '--recent',
        action='store_true',
        help='Fetch only recent changes instead of full dataset'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back for recent changes (default: 7)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='NVD API key (or set NVD_API_KEY environment variable)'
    )
    
    parser.add_argument(
        '--checkpoint-file',
        type=str,
        default='nvd_checkpoint.txt',
        help='Checkpoint file for resume capability (default: nvd_checkpoint.txt)'
    )
    
    args = parser.parse_args()
    
    # Ensure database tables exist
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    # Get NVD service
    nvd_service = get_nvd_service(api_key=args.api_key)
    
    # Display configuration
    if nvd_service.api_key:
        logger.info("[OK] Using NVD API key - enhanced rate limit (50 req/min)")
    else:
        logger.info("[WARN] No API key - using public rate limit (10 req/min)")
        logger.info("       Get a free API key at: https://nvd.nist.gov/developers/request-an-api-key")
    
    try:
        if args.recent:
            # Fetch recent changes
            logger.info(f"[FETCH] Fetching CVEs modified in last {args.days} days...")
            start_time = datetime.now()
            
            count = nvd_service.fetch_recent_cves(days=args.days)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[DONE] Complete! Processed {count} CVEs in {elapsed:.1f} seconds")
            
        else:
            # Fetch complete dataset
            end_year = args.end_year or datetime.now().year
            logger.info(f"[START] NVD complete fetch: {args.start_year}-{end_year}")
            logger.info(f"        Checkpoint file: {args.checkpoint_file}")
            logger.info(f"        This may take several hours...")
            
            start_time = datetime.now()
            
            count = nvd_service.fetch_all_cves(
                start_year=args.start_year,
                end_year=end_year,
                checkpoint_file=args.checkpoint_file
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            hours = elapsed / 3600
            
            logger.info(f"[DONE] Complete! Processed {count:,} CVEs in {hours:.1f} hours")
            logger.info(f"       Average: {count/(elapsed/60):.1f} CVEs/minute")
    
    except KeyboardInterrupt:
        logger.warning("\n[STOP] Interrupted by user")
        logger.info(f"       Progress saved to {args.checkpoint_file}")
        logger.info(f"       Run the same command again to resume")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"[ERROR] {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
