#!/usr/bin/env python3
"""
Check if KEV data is initialized in the database.
Returns exit code 0 if initialized, 1 if not.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from backend.database import SessionLocal
    from backend.models import Vulnerability
    
    db = SessionLocal()
    try:
        count = db.query(Vulnerability).filter(
            Vulnerability.exploited_in_the_wild == True
        ).count()
        
        if count > 0:
            print(f"{count}")  # Print count for logging
            sys.exit(0)  # KEV data exists
        else:
            print("0")
            sys.exit(1)  # No KEV data
            
    finally:
        db.close()
        
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)  # Error = assume not initialized
