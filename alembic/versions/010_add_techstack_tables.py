"""Add tech stack tables for CVE matching.

Revision ID: 010
Revises: 009
Create Date: 2024-12-06

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "010_add_techstack_tables"
down_revision = "009_add_news_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tech_stacks table
    op.create_table(
        "tech_stacks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Owner - either session_id (anonymous) or user_id (authenticated)
        sa.Column("session_id", sa.String(64), nullable=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        # Packages stored as JSON array
        # Format: [{"name": "react", "version": "18.2.0", "ecosystem": "npm"}, ...]
        sa.Column("packages", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Source file type that was parsed
        sa.Column("source_type", sa.String(50), nullable=True),  # package.json, requirements.txt, etc.
        # Statistics
        sa.Column("package_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vulnerable_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        # Last scan timestamp
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index for faster lookups
    op.create_index("ix_tech_stacks_user_id", "tech_stacks", ["user_id"])
    op.create_index("ix_tech_stacks_session_id", "tech_stacks", ["session_id"])

    # Create tech_stack_matches table for caching CVE matches
    op.create_table(
        "tech_stack_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tech_stack_id", sa.Integer(), sa.ForeignKey("tech_stacks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vulnerability_id", sa.Integer(), sa.ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=False),
        # Package info
        sa.Column("package_name", sa.String(255), nullable=False),
        sa.Column("package_version", sa.String(100), nullable=True),
        sa.Column("ecosystem", sa.String(50), nullable=False),  # npm, pypi, rubygems, etc.
        # Match details
        sa.Column("match_type", sa.String(50), nullable=False),  # exact, version_range, product_name
        sa.Column("match_confidence", sa.Float(), nullable=False, server_default="0.5"),
        # Matched CPE or product info
        sa.Column("matched_cpe", sa.String(500), nullable=True),
        sa.Column("matched_vendor", sa.String(255), nullable=True),
        sa.Column("matched_product", sa.String(255), nullable=True),
        # Timestamps
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient querying
    op.create_index("ix_tech_stack_matches_tech_stack_id", "tech_stack_matches", ["tech_stack_id"])
    op.create_index("ix_tech_stack_matches_vulnerability_id", "tech_stack_matches", ["vulnerability_id"])
    op.create_index("ix_tech_stack_matches_package", "tech_stack_matches", ["package_name", "ecosystem"])

    # Create unique constraint to prevent duplicate matches
    op.create_unique_constraint(
        "uq_tech_stack_match",
        "tech_stack_matches",
        ["tech_stack_id", "vulnerability_id", "package_name"]
    )

    # Create package_cpe_mappings table for known package-to-CPE mappings
    # This helps with accurate matching
    op.create_table(
        "package_cpe_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ecosystem", sa.String(50), nullable=False),  # npm, pypi, etc.
        sa.Column("package_name", sa.String(255), nullable=False),
        # CPE components
        sa.Column("cpe_vendor", sa.String(255), nullable=False),
        sa.Column("cpe_product", sa.String(255), nullable=False),
        # Confidence and source
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("source", sa.String(50), nullable=False, server_default="'manual'"),  # manual, nvd, osv
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create unique constraint for package mappings
    op.create_unique_constraint(
        "uq_package_cpe_mapping",
        "package_cpe_mappings",
        ["ecosystem", "package_name", "cpe_vendor", "cpe_product"]
    )

    # Create index for fast lookups
    op.create_index("ix_package_cpe_mappings_lookup", "package_cpe_mappings", ["ecosystem", "package_name"])


def downgrade() -> None:
    op.drop_table("package_cpe_mappings")
    op.drop_table("tech_stack_matches")
    op.drop_table("tech_stacks")
