"""
Stats Cache Service.

Provides utilities to refresh the vulnerability statistics cache.
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def refresh_stats_cache(db: Session) -> bool:
    """
    Refresh the vulnerability statistics cache.

    This should be called after:
    - New vulnerabilities are added
    - Vulnerabilities are updated
    - Exploitation status changes

    Args:
        db: Database session

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Refreshing vulnerability stats cache...")
        db.execute(text("SELECT refresh_vulnerability_stats_cache()"))
        db.commit()
        logger.info("✓ Stats cache refreshed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to refresh stats cache: {e}")
        db.rollback()
        return False
