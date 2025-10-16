#!/usr/bin/env python3
"""
Start LLM Processing for Vulnerabilities

Usage:
    # Process all unprocessed CVEs (background)
    python scripts/start_llm_processing.py
    
    # Process specific batch size
    python scripts/start_llm_processing.py --batch-size 50
    
    # Process only high priority
    python scripts/start_llm_processing.py --priority high
    
    # Process single CVE
    python scripts/start_llm_processing.py --cve CVE-2024-1234
    
    # Get stats
    python scripts/start_llm_processing.py --stats
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.tasks.llm_tasks import process_cve_with_llm, process_llm_queue, get_llm_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Start LLM processing for vulnerabilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--cve',
        type=str,
        help='Process a single CVE by ID'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of CVEs to process in batch (default: 10)'
    )
    
    parser.add_argument(
        '--priority',
        type=str,
        choices=['high', 'medium', 'low', 'all'],
        default='all',
        help='Priority level to process (default: all)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show LLM processing statistics'
    )
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            # Show statistics
            logger.info("Fetching LLM processing statistics...")
            result = get_llm_stats()
            
            print("\n" + "="*60)
            print("LLM PROCESSING STATISTICS")
            print("="*60)
            print(f"Total CVEs:              {result['total_cves']:,}")
            print(f"Processed:               {result['processed']:,}")
            print(f"Pending:                 {result['pending']:,}")
            print(f"High Priority Pending:   {result['high_priority_pending']:,}")
            print(f"Completion:              {result['completion_percentage']}%")
            print("="*60 + "\n")
            
        elif args.cve:
            # Process single CVE
            logger.info(f"Queuing CVE {args.cve} for LLM processing...")
            task = process_cve_with_llm.delay(args.cve)
            logger.info(f"Task queued with ID: {task.id}")
            logger.info("Waiting for result...")
            
            result = task.get(timeout=300)  # 5 minute timeout
            
            if result['status'] == 'success':
                logger.info(f"[SUCCESS] Processed {args.cve}")
                if result.get('simple_title'):
                    logger.info(f"  Title: {result['simple_title']}")
                if result.get('simple_description'):
                    logger.info(f"  Description: {result['simple_description'][:100]}...")
            else:
                logger.warning(f"[{result['status'].upper()}] {result.get('message', 'Unknown status')}")
                
        else:
            # Process batch
            if args.priority == 'all':
                priorities = ['high', 'medium', 'low']
            else:
                priorities = [args.priority]
            
            total_queued = 0
            for priority in priorities:
                logger.info(f"Queuing {args.batch_size} CVEs with priority: {priority}")
                task = process_llm_queue.delay(batch_size=args.batch_size, priority=priority)
                logger.info(f"Task queued with ID: {task.id}")
                
                # Wait for result
                result = task.get(timeout=60)
                
                if result['status'] == 'success':
                    queued = result.get('processed', 0)
                    total_queued += queued
                    logger.info(f"[SUCCESS] Queued {queued} CVEs for processing")
                else:
                    logger.warning(f"[{result['status'].upper()}] {result.get('message', 'Unknown error')}")
            
            logger.info(f"\nTotal CVEs queued for processing: {total_queued}")
            logger.info("Processing will continue in background via Celery workers")
            
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
