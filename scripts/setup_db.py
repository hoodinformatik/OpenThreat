"""
Database setup script for OpenThreat.

This script:
1. Creates initial Alembic migration
2. Applies migrations to database
3. Optionally loads sample data
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd: list[str], cwd: Path = PROJECT_ROOT):
    """Run a command and print output."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=cwd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    
    print(f"\n✅ Command completed successfully\n")


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         OpenThreat Database Setup                        ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # Check if Docker is running
    print("Step 1: Checking Docker...")
    try:
        subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            check=True
        )
        print("✅ Docker is running")
    except Exception as e:
        print("❌ Docker is not running. Please start Docker first.")
        print("   Run: docker-compose up -d")
        sys.exit(1)
    
    # Start database containers
    print("\nStep 2: Starting database containers...")
    run_command(["docker-compose", "up", "-d", "postgres", "redis"])
    
    # Wait for database to be ready
    print("\nStep 3: Waiting for database to be ready...")
    import time
    time.sleep(5)
    
    # Create initial migration
    print("\nStep 4: Creating initial Alembic migration...")
    try:
        run_command([
            sys.executable, "-m", "alembic",
            "revision", "--autogenerate",
            "-m", "Initial schema"
        ])
    except Exception as e:
        print("⚠️  Migration might already exist, continuing...")
    
    # Apply migrations
    print("\nStep 5: Applying migrations...")
    run_command([
        sys.executable, "-m", "alembic",
        "upgrade", "head"
    ])
    
    # Optional: Load sample data
    print("\nStep 6: Load sample data? (y/n)")
    response = input("> ").strip().lower()
    
    if response == 'y':
        dedup_file = PROJECT_ROOT / "Data_Sample_Connectors" / "out" / "deduplicated_cves.ndjson"
        
        if dedup_file.exists():
            print(f"\nLoading data from {dedup_file}...")
            run_command([
                sys.executable, "-m", "backend.ingestion",
                str(dedup_file),
                "initial_load"
            ])
        else:
            print(f"⚠️  File not found: {dedup_file}")
            print("   Run the connectors first: python Data_Sample_Connectors/run_all.py")
    
    print("""
╔══════════════════════════════════════════════════════════╗
║         ✅ Database Setup Complete!                      ║
╚══════════════════════════════════════════════════════════╝

Next steps:
1. Check database: docker-compose logs postgres
2. Connect to DB: docker exec -it openthreat-db psql -U openthreat -d openthreat
3. View data: SELECT COUNT(*) FROM vulnerabilities;

To start the API server:
    python -m uvicorn backend.main:app --reload
""")


if __name__ == "__main__":
    main()
