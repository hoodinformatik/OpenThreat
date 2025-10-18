"""add email verification table

Revision ID: 006_add_email_verification
Revises: 005_add_users_table
Create Date: 2025-10-18 06:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_email_verification'
down_revision = '005_add_users_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_verifications table
    op.create_table(
        'email_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('verification_type', sa.String(length=20), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_email_verifications_user_id', 'email_verifications', ['user_id'])
    op.create_index('ix_email_verifications_email', 'email_verifications', ['email'])


def downgrade() -> None:
    op.drop_index('ix_email_verifications_email', table_name='email_verifications')
    op.drop_index('ix_email_verifications_user_id', table_name='email_verifications')
    op.drop_table('email_verifications')
