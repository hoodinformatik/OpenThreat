#!/usr/bin/env python3
"""
Apply CVE voting migration directly to the database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database import engine

def apply_migration():
    """Apply the CVE voting migration."""

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='vulnerabilities'
                AND column_name IN ('upvotes', 'downvotes')
            """))
            existing_columns = [row[0] for row in result]

            # Add upvotes and downvotes columns if they don't exist
            if 'upvotes' not in existing_columns:
                print("Adding upvotes column to vulnerabilities table...")
                conn.execute(text("""
                    ALTER TABLE vulnerabilities
                    ADD COLUMN upvotes INTEGER NOT NULL DEFAULT 0
                """))
            else:
                print("upvotes column already exists")

            if 'downvotes' not in existing_columns:
                print("Adding downvotes column to vulnerabilities table...")
                conn.execute(text("""
                    ALTER TABLE vulnerabilities
                    ADD COLUMN downvotes INTEGER NOT NULL DEFAULT 0
                """))
            else:
                print("downvotes column already exists")

            # Check if cve_votes table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'cve_votes'
                )
            """))
            table_exists = result.scalar()

            if not table_exists:
                print("Creating cve_votes table...")
                conn.execute(text("""
                    CREATE TABLE cve_votes (
                        id SERIAL PRIMARY KEY,
                        cve_id VARCHAR(50) NOT NULL,
                        user_id INTEGER NOT NULL,
                        vote_type INTEGER NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        FOREIGN KEY (cve_id) REFERENCES vulnerabilities(cve_id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))

                print("Creating indexes on cve_votes table...")
                conn.execute(text("""
                    CREATE UNIQUE INDEX idx_cve_votes_unique
                    ON cve_votes(cve_id, user_id)
                """))
                conn.execute(text("""
                    CREATE INDEX idx_cve_votes_user
                    ON cve_votes(user_id)
                """))
                conn.execute(text("""
                    CREATE INDEX idx_cve_votes_cve_created
                    ON cve_votes(cve_id, created_at)
                """))
                conn.execute(text("""
                    CREATE INDEX ix_cve_votes_id
                    ON cve_votes(id)
                """))
                conn.execute(text("""
                    CREATE INDEX ix_cve_votes_cve_id
                    ON cve_votes(cve_id)
                """))
                conn.execute(text("""
                    CREATE INDEX ix_cve_votes_user_id
                    ON cve_votes(user_id)
                """))
            else:
                print("cve_votes table already exists")

            # Update alembic version if the table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
            """))
            alembic_exists = result.scalar()

            if alembic_exists:
                print("Updating alembic version...")
                conn.execute(text("""
                    UPDATE alembic_version
                    SET version_num = '008_add_cve_voting'
                """))

            # Commit transaction
            trans.commit()
            print("\n✅ Migration applied successfully!")

        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error applying migration: {e}")
            raise

if __name__ == "__main__":
    apply_migration()
