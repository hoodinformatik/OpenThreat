#!/usr/bin/env python3
"""
Clear the statistics cache in Redis to force recalculation.
"""
import redis
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database import REDIS_URL

def clear_stats_cache():
    """Clear the stats cache from Redis."""
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Delete the stats cache key
        result = redis_client.delete("dashboard:stats")
        
        if result:
            print("✓ Stats cache cleared successfully")
        else:
            print("ℹ Stats cache was already empty")
            
        return True
        
    except Exception as e:
        print(f"✗ Error clearing stats cache: {e}")
        return False

if __name__ == "__main__":
    success = clear_stats_cache()
    sys.exit(0 if success else 1)
