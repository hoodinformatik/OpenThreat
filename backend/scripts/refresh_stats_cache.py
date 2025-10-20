#!/usr/bin/env python3
"""
Script to refresh the vulnerability stats cache.
Can be run as a cronjob or manually.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal


def refresh_stats_cache():
    """Refresh the vulnerability stats cache."""
    db = SessionLocal()
    try:
        print("Refreshing vulnerability stats cache...")
        db.execute("SELECT refresh_vulnerability_stats_cache()")
        db.commit()
        print("✓ Stats cache refreshed successfully")
        return True
    except Exception as e:
        print(f"✗ Error refreshing stats cache: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = refresh_stats_cache()
    sys.exit(0 if success else 1)
