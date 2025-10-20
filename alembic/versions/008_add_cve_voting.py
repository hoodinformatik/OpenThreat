"""add cve voting system

Revision ID: 008_add_cve_voting
Revises: 007_add_comments_tables
Create Date: 2025-10-20 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_cve_voting'
down_revision = '007_add_comments_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add upvotes and downvotes columns to vulnerabilities table
    op.add_column('vulnerabilities', sa.Column('upvotes', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('vulnerabilities', sa.Column('downvotes', sa.Integer(), nullable=False, server_default='0'))

    # Create cve_votes table
    op.create_table(
        'cve_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cve_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vote_type', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cve_id'], ['vulnerabilities.cve_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_cve_votes_unique', 'cve_votes', ['cve_id', 'user_id'], unique=True)
    op.create_index('idx_cve_votes_user', 'cve_votes', ['user_id'])
    op.create_index('idx_cve_votes_cve_created', 'cve_votes', ['cve_id', 'created_at'])
    op.create_index(op.f('ix_cve_votes_cve_id'), 'cve_votes', ['cve_id'])
    op.create_index(op.f('ix_cve_votes_id'), 'cve_votes', ['id'])
    op.create_index(op.f('ix_cve_votes_user_id'), 'cve_votes', ['user_id'])


def downgrade() -> None:
    # Drop cve_votes table and indexes
    op.drop_index(op.f('ix_cve_votes_user_id'), table_name='cve_votes')
    op.drop_index(op.f('ix_cve_votes_id'), table_name='cve_votes')
    op.drop_index(op.f('ix_cve_votes_cve_id'), table_name='cve_votes')
    op.drop_index('idx_cve_votes_cve_created', table_name='cve_votes')
    op.drop_index('idx_cve_votes_user', table_name='cve_votes')
    op.drop_index('idx_cve_votes_unique', table_name='cve_votes')
    op.drop_table('cve_votes')

    # Remove upvotes and downvotes columns from vulnerabilities
    op.drop_column('vulnerabilities', 'downvotes')
    op.drop_column('vulnerabilities', 'upvotes')
