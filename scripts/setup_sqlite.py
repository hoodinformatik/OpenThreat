"""
Setup script for OpenThreat using SQLite (no Docker required).

This is a simplified setup for development without Docker.
For production, use PostgreSQL with Docker.
"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Set SQLite database URL
os.environ["DATABASE_URL"] = f"sqlite:///{PROJECT_ROOT}/openthreat.db"

print("""
╔══════════════════════════════════════════════════════════╗
║    OpenThreat Setup (SQLite - No Docker Required)       ║
╚══════════════════════════════════════════════════════════╝

⚠️  Note: This uses SQLite for development.
   For production, use PostgreSQL with Docker.
""")

# Import after setting environment variable
from backend.database import Base, engine, SessionLocal
from backend.ingestion import run_ingestion

print("\nStep 1: Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
except Exception as e:
    print(f"❌ Error creating tables: {e}")
    sys.exit(1)

print("\nStep 2: Load sample data? (y/n)")
response = input("> ").strip().lower()

if response == 'y':
    dedup_file = PROJECT_ROOT / "Data_Sample_Connectors" / "out" / "deduplicated_cves.ndjson"
    
    if dedup_file.exists():
        print(f"\nLoading data from {dedup_file}...")
        try:
            run = run_ingestion(dedup_file, "initial_load")
            print(f"\n✅ Data loaded successfully!")
            print(f"   Inserted: {run.records_inserted}")
            print(f"   Updated: {run.records_updated}")
            print(f"   Failed: {run.records_failed}")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
    else:
        print(f"⚠️  File not found: {dedup_file}")
        print("   Run the connectors first: python Data_Sample_Connectors/run_all.py")

print(f"""
╔══════════════════════════════════════════════════════════╗
║         ✅ Setup Complete!                               ║
╚══════════════════════════════════════════════════════════╝

Database location: {PROJECT_ROOT}/openthreat.db

To query the database:
    python scripts/query_db.py

To start the API server (when ready):
    $env:DATABASE_URL="sqlite:///{PROJECT_ROOT}/openthreat.db"
    python -m uvicorn backend.main:app --reload
""")
