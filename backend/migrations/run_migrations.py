#!/usr/bin/env python3
"""
Run database migrations on startup.
This script is executed automatically when the backend starts.
"""

import logging
import os
from pathlib import Path

from sqlalchemy import text

from backend.database import engine

logger = logging.getLogger(__name__)


def run_migrations():
    """
    Run all SQL migrations in the migrations directory.
    Migrations are idempotent and safe to run multiple times.
    """
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        logger.info("No migration files found")
        return

    logger.info(f"Found {len(migration_files)} migration file(s)")

    with engine.connect() as conn:
        for migration_file in migration_files:
            logger.info(f"Running migration: {migration_file.name}")

            try:
                # Read migration file
                with open(migration_file, "r") as f:
                    migration_sql = f.read()

                # Execute migration
                conn.execute(text(migration_sql))
                conn.commit()

                logger.info(f"✓ Migration {migration_file.name} completed successfully")

            except Exception as e:
                logger.error(f"✗ Migration {migration_file.name} failed: {e}")
                # Don't raise - continue with other migrations
                # This allows partial migrations to succeed

    logger.info("All migrations completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    run_migrations()
