#!/usr/bin/env python3
"""
Fetch and import CISA Known Exploited Vulnerabilities catalog.
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database import SessionLocal
from backend.services.cisa_kev_service import get_cisa_kev_service

def fetch_cisa_kev():
    """Fetch CISA KEV catalog and update database."""
    print(f"[{datetime.utcnow()}] Starting CISA KEV fetch...")
    
    db = SessionLocal()
    try:
        kev_service = get_cisa_kev_service()
        result = kev_service.update_exploited_vulnerabilities(db)
        
        if result["status"] == "success":
            print(f"\n✓ CISA KEV import completed:")
            print(f"  - Total KEV entries: {result['total_kev_entries']}")
            print(f"  - Updated in DB: {result['updated']}")
            print(f"  - Not found in DB: {result['not_found']}")
            return True
        else:
            print(f"\n✗ CISA KEV import failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fetch_cisa_kev()
    sys.exit(0 if success else 1)
