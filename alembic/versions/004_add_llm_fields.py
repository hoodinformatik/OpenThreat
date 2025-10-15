"""add llm fields

Revision ID: 004_add_llm_fields
Revises: 5316abe9027f
Create Date: 2024-10-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_llm_fields'
down_revision = '5316abe9027f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add LLM-generated fields to vulnerabilities table
    op.add_column('vulnerabilities', sa.Column('simple_title', sa.String(length=200), nullable=True))
    op.add_column('vulnerabilities', sa.Column('simple_description', sa.Text(), nullable=True))
    op.add_column('vulnerabilities', sa.Column('llm_processed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('vulnerabilities', sa.Column('llm_processed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove LLM fields
    op.drop_column('vulnerabilities', 'llm_processed_at')
    op.drop_column('vulnerabilities', 'llm_processed')
    op.drop_column('vulnerabilities', 'simple_description')
    op.drop_column('vulnerabilities', 'simple_title')
