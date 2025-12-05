"""Add news sources and articles tables

Revision ID: 009_add_news_tables
Revises: 008_add_cve_voting
Create Date: 2024-12-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_news_tables'
down_revision = '008_add_cve_voting'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create news_sources table
    op.create_table(
        'news_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='rss'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('fetch_interval_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('last_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_fetch_status', sa.String(50), nullable=True),
        sa.Column('last_fetch_error', sa.Text(), nullable=True),
        sa.Column('total_articles', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index('ix_news_sources_id', 'news_sources', ['id'])
    op.create_index('ix_news_sources_is_active', 'news_sources', ['is_active'])

    # Create news_articles table
    op.create_table(
        'news_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('author', sa.String(200), nullable=True),
        sa.Column('original_summary', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('llm_summary', sa.Text(), nullable=True),
        sa.Column('llm_key_points', sa.JSON(), nullable=True),
        sa.Column('llm_relevance_score', sa.Float(), nullable=True),
        sa.Column('llm_processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('llm_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('categories', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('related_cves', sa.JSON(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['source_id'], ['news_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index('ix_news_articles_id', 'news_articles', ['id'])
    op.create_index('ix_news_articles_source_id', 'news_articles', ['source_id'])
    op.create_index('ix_news_articles_published_at', 'news_articles', ['published_at'])
    op.create_index('idx_news_articles_source_published', 'news_articles', ['source_id', 'published_at'])
    op.create_index('idx_news_articles_published', 'news_articles', ['published_at'])

    # Create trigram index for title search (PostgreSQL specific)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_news_title_trgm
        ON news_articles USING gin (title gin_trgm_ops)
    """)

    # Insert default news sources
    op.execute("""
        INSERT INTO news_sources (name, url, description, icon_url, is_default, is_active)
        VALUES
            ('Heise Security', 'https://www.heise.de/security/feed.xml',
             'German IT security news from Heise', 'https://www.heise.de/favicon.ico', true, true),
            ('Hacker News', 'https://hnrss.org/newest',
             'Tech and security news from Y Combinator''s Hacker News', 'https://news.ycombinator.com/favicon.ico', true, true),
            ('NCSC UK', 'https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml',
             'UK National Cyber Security Centre advisories', 'https://www.ncsc.gov.uk/favicon.ico', true, true),
            ('The Hacker News', 'https://feeds.feedburner.com/TheHackersNews',
             'Cybersecurity news and analysis', 'https://thehackernews.com/favicon.ico', true, true),
            ('Krebs on Security', 'https://krebsonsecurity.com/feed/',
             'In-depth security news and investigation by Brian Krebs', 'https://krebsonsecurity.com/favicon.ico', true, true),
            ('Bleeping Computer', 'https://www.bleepingcomputer.com/feed/',
             'Technology news and security updates', 'https://www.bleepingcomputer.com/favicon.ico', true, true)
        ON CONFLICT (url) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index('ix_news_title_trgm', 'news_articles')
    op.drop_index('idx_news_articles_published', 'news_articles')
    op.drop_index('idx_news_articles_source_published', 'news_articles')
    op.drop_index('ix_news_articles_published_at', 'news_articles')
    op.drop_index('ix_news_articles_source_id', 'news_articles')
    op.drop_index('ix_news_articles_id', 'news_articles')
    op.drop_table('news_articles')

    op.drop_index('ix_news_sources_is_active', 'news_sources')
    op.drop_index('ix_news_sources_id', 'news_sources')
    op.drop_table('news_sources')
