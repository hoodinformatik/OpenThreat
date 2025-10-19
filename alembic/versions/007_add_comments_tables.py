"""add comments and comment votes tables

Revision ID: 007_add_comments_tables
Revises: 006_add_email_verification
Create Date: 2025-10-19 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_comments_tables'
down_revision = '006_add_email_verification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create comments table
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('cve_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('upvotes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('downvotes', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['cve_id'], ['vulnerabilities.cve_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for comments
    op.create_index('ix_comments_id', 'comments', ['id'])
    op.create_index('ix_comments_cve_id', 'comments', ['cve_id'])
    op.create_index('ix_comments_user_id', 'comments', ['user_id'])
    op.create_index('ix_comments_parent_id', 'comments', ['parent_id'])
    op.create_index('idx_comments_cve_created', 'comments', ['cve_id', 'created_at'])
    op.create_index('idx_comments_user_created', 'comments', ['user_id', 'created_at'])
    op.create_index('idx_comments_parent', 'comments', ['parent_id'])
    
    # Create comment_votes table
    op.create_table(
        'comment_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vote_type', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for comment_votes
    op.create_index('ix_comment_votes_id', 'comment_votes', ['id'])
    op.create_index('ix_comment_votes_comment_id', 'comment_votes', ['comment_id'])
    op.create_index('ix_comment_votes_user_id', 'comment_votes', ['user_id'])
    op.create_index('idx_comment_votes_unique', 'comment_votes', ['comment_id', 'user_id'], unique=True)


def downgrade() -> None:
    # Drop comment_votes table
    op.drop_index('idx_comment_votes_unique', table_name='comment_votes')
    op.drop_index('ix_comment_votes_user_id', table_name='comment_votes')
    op.drop_index('ix_comment_votes_comment_id', table_name='comment_votes')
    op.drop_index('ix_comment_votes_id', table_name='comment_votes')
    op.drop_table('comment_votes')
    
    # Drop comments table
    op.drop_index('idx_comments_parent', table_name='comments')
    op.drop_index('idx_comments_user_created', table_name='comments')
    op.drop_index('idx_comments_cve_created', table_name='comments')
    op.drop_index('ix_comments_parent_id', table_name='comments')
    op.drop_index('ix_comments_user_id', table_name='comments')
    op.drop_index('ix_comments_cve_id', table_name='comments')
    op.drop_index('ix_comments_id', table_name='comments')
    op.drop_table('comments')
