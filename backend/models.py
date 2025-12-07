"""
SQLAlchemy database models for OpenThreat.
"""

import enum
import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import JSON, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from .database import Base


# User roles enum
class UserRole(str, enum.Enum):
    """User role definitions."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(Base):
    """
    User accounts for authentication and authorization.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.VIEWER,
        nullable=False,
        index=True,
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Security
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


# Association table for many-to-many relationship between vulnerabilities and techniques
vulnerability_technique = Table(
    "vulnerability_technique",
    Base.metadata,
    Column(
        "vulnerability_id", Integer, ForeignKey("vulnerabilities.id"), primary_key=True
    ),
    Column("technique_id", Integer, ForeignKey("techniques.id"), primary_key=True),
)


class Vulnerability(Base):
    """
    Vulnerability records from all sources (CISA, NVD, EU CVE, etc.)
    """

    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)

    # Core identifiers
    cve_id = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # CVSS scoring
    cvss_score = Column(Float, nullable=True, index=True)
    cvss_vector = Column(String(200), nullable=True)
    severity = Column(
        String(20), nullable=True, index=True
    )  # CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN

    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    modified_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # CISA KEV specific
    exploited_in_the_wild = Column(Boolean, default=False, nullable=False, index=True)
    cisa_due_date = Column(Date, nullable=True)

    # CWE weaknesses (stored as JSON array)
    cwe_ids = Column(JSON, nullable=True)  # ["CWE-79", "CWE-89"]

    # Affected products (stored as JSON array)
    affected_products = Column(JSON, nullable=True)  # ["vendor:product:version"]
    vendors = Column(JSON, nullable=True)  # ["microsoft", "apache"]
    products = Column(JSON, nullable=True)  # ["windows", "http_server"]

    # References (stored as JSON array of objects)
    references = Column(JSON, nullable=True)  # [{"url": "...", "type": "patch"}]

    # Source tracking
    sources = Column(JSON, nullable=True)  # ["cisa", "nvd_cve", "eu_cve_search"]
    source_tags = Column(JSON, nullable=True)  # Additional tags from sources

    # Priority score (computed)
    priority_score = Column(Float, nullable=True, index=True)

    # LLM-generated fields (plain-language summaries)
    simple_title = Column(String(200), nullable=True)  # User-friendly title
    simple_description = Column(Text, nullable=True)  # Plain-language description
    llm_processed = Column(
        Boolean, default=False, nullable=False
    )  # Whether LLM processing was done
    llm_processed_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When LLM processing occurred

    # Vote counts (denormalized for performance)
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    techniques = relationship(
        "Technique", secondary=vulnerability_technique, back_populates="vulnerabilities"
    )

    # Indexes for full-text search (PostgreSQL specific)
    __table_args__ = (
        Index(
            "ix_vuln_cve_id_trgm",
            "cve_id",
            postgresql_using="gin",
            postgresql_ops={"cve_id": "gin_trgm_ops"},
        ),
        Index(
            "ix_vuln_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
        Index(
            "ix_vuln_description_trgm",
            "description",
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
        ),
    )


class Technique(Base):
    """
    MITRE ATT&CK techniques and tactics.
    """

    __tablename__ = "techniques"

    id = Column(Integer, primary_key=True, index=True)

    # MITRE identifiers
    technique_id = Column(String(20), unique=True, nullable=False, index=True)  # T1234
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Tactics (stored as JSON array)
    tactics = Column(JSON, nullable=True)  # ["initial-access", "execution"]

    # Platforms and data sources
    platforms = Column(JSON, nullable=True)  # ["Windows", "Linux"]
    data_sources = Column(JSON, nullable=True)

    # Detection and mitigation
    detection = Column(Text, nullable=True)
    mitigation = Column(Text, nullable=True)

    # References
    references = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    vulnerabilities = relationship(
        "Vulnerability", secondary=vulnerability_technique, back_populates="techniques"
    )


class IOC(Base):
    """
    Indicators of Compromise (URLs, domains, IPs, hashes, etc.)
    """

    __tablename__ = "iocs"

    id = Column(Integer, primary_key=True, index=True)

    # IOC details
    ioc_type = Column(
        String(50), nullable=False, index=True
    )  # url, domain, ip, hash, email
    value = Column(String(2000), nullable=False, index=True)

    # Threat classification
    threat_type = Column(String(100), nullable=True)  # malware, phishing, c2, etc.
    tags = Column(JSON, nullable=True)  # ["ransomware", "apt28"]

    # Confidence and status
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    status = Column(
        String(20), default="active", nullable=False
    )  # active, inactive, expired

    # Timestamps
    first_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Source information
    source = Column(String(100), nullable=True)
    source_url = Column(String(500), nullable=True)

    # Additional context
    context = Column(JSON, nullable=True)  # Flexible field for source-specific data

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index(
            "ix_ioc_value_trgm",
            "value",
            postgresql_using="gin",
            postgresql_ops={"value": "gin_trgm_ops"},
        ),
    )


class IngestionRun(Base):
    """
    Track data ingestion runs for monitoring and debugging.
    """

    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Run details
    source = Column(String(100), nullable=False, index=True)  # cisa_kev, nvd_cve, etc.
    status = Column(String(20), nullable=False, index=True)  # running, success, failed

    # Statistics
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Metadata
    config = Column(JSON, nullable=True)  # Store run configuration
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SearchCache(Base):
    """
    Cache for expensive search queries to improve performance.
    """

    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True, index=True)

    # Cache key (hash of query parameters)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)

    # Query details
    query_type = Column(
        String(50), nullable=False
    )  # vulnerability_search, ioc_search, etc.
    query_params = Column(JSON, nullable=False)

    # Cached results
    results = Column(JSON, nullable=False)
    result_count = Column(Integer, nullable=False)

    # Cache metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    hit_count = Column(Integer, default=0)


class EmailVerification(Base):
    """
    Email verification codes for user registration and email changes.
    """

    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # Nullable for registration
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)

    # Type: 'registration' or 'email_change'
    verification_type = Column(String(20), nullable=False)

    # Status
    is_used = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="email_verifications")

    @staticmethod
    def generate_code() -> str:
        """Generate a 6-digit verification code."""
        return "".join(secrets.choice(string.digits) for _ in range(6))

    @staticmethod
    def get_expiry_time() -> datetime:
        """Get expiry time (15 minutes from now)."""
        return datetime.now(timezone.utc) + timedelta(minutes=15)

    def is_expired(self) -> bool:
        """Check if code is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if code is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()


class Comment(Base):
    """
    Comments on CVEs - plain text only, no HTML/scripts allowed.
    Supports nested comments (replies).
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)

    # Content (plain text only)
    content = Column(Text, nullable=False)

    # Relationships
    cve_id = Column(
        String(50), ForeignKey("vulnerabilities.cve_id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(
        Integer, ForeignKey("comments.id"), nullable=True, index=True
    )  # For nested comments

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_edited = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete

    # Vote counts (denormalized for performance)
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", backref="comments")
    vulnerability = relationship("Vulnerability", backref="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    votes = relationship(
        "CommentVote", back_populates="comment", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_comments_cve_created", "cve_id", "created_at"),
        Index("idx_comments_user_created", "user_id", "created_at"),
        Index("idx_comments_parent", "parent_id"),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, cve_id={self.cve_id}, user={self.user.username if self.user else 'Unknown'})>"


class CommentVote(Base):
    """
    Votes on comments (upvote/downvote).
    One vote per user per comment.
    """

    __tablename__ = "comment_votes"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Vote type: 1 for upvote, -1 for downvote
    vote_type = Column(Integer, nullable=False)  # 1 or -1

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    comment = relationship("Comment", back_populates="votes")
    user = relationship("User", backref="comment_votes")

    # Constraints: one vote per user per comment
    __table_args__ = (
        Index("idx_comment_votes_unique", "comment_id", "user_id", unique=True),
        Index("idx_comment_votes_user", "user_id"),
    )

    def __repr__(self):
        vote_str = "upvote" if self.vote_type == 1 else "downvote"
        return f"<CommentVote(id={self.id}, comment_id={self.comment_id}, {vote_str})>"


class Bookmark(Base):
    """
    User bookmarks for tracking CVEs.
    """

    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cve_id = Column(
        String(50), ForeignKey("vulnerabilities.cve_id"), nullable=False, index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", backref="bookmarks")
    vulnerability = relationship("Vulnerability", backref="bookmarks")

    # Constraints
    __table_args__ = (
        Index("idx_bookmarks_user_created", "user_id", "created_at"),
        {"extend_existing": True},
    )


class CVEVote(Base):
    """
    Votes on CVEs (upvote/downvote).
    One vote per user per CVE.
    """

    __tablename__ = "cve_votes"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    cve_id = Column(
        String(50), ForeignKey("vulnerabilities.cve_id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Vote type: 1 for upvote, -1 for downvote
    vote_type = Column(Integer, nullable=False)  # 1 or -1

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    vulnerability = relationship("Vulnerability", backref="votes")
    user = relationship("User", backref="cve_votes")

    # Constraints: one vote per user per CVE
    __table_args__ = (
        Index("idx_cve_votes_unique", "cve_id", "user_id", unique=True),
        Index("idx_cve_votes_user", "user_id"),
        Index("idx_cve_votes_cve_created", "cve_id", "created_at"),
    )

    def __repr__(self):
        vote_str = "upvote" if self.vote_type == 1 else "downvote"
        return f"<CVEVote(id={self.id}, cve_id={self.cve_id}, {vote_str})>"


class Notification(Base):
    """
    User notifications for mentions, replies, and other events.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Recipient
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Notification type
    type = Column(
        String(50), nullable=False, index=True
    )  # 'mention', 'reply', 'vote', etc.

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Related entities (optional, depends on notification type)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True, index=True)
    cve_id = Column(
        String(50), ForeignKey("vulnerabilities.cve_id"), nullable=True, index=True
    )

    # Actor (who triggered the notification)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="notifications")
    actor = relationship("User", foreign_keys=[actor_id])
    comment = relationship("Comment", backref="notifications")
    vulnerability = relationship("Vulnerability", backref="notifications")

    # Indexes for performance
    __table_args__ = (
        Index("idx_notifications_user_created", "user_id", "created_at"),
        Index("idx_notifications_user_unread", "user_id", "is_read"),
        Index("idx_notifications_type", "type"),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, is_read={self.is_read})>"


class NewsSource(Base):
    """
    RSS/Atom feed sources for security news.
    """

    __tablename__ = "news_sources"

    id = Column(Integer, primary_key=True, index=True)

    # Source details
    name = Column(String(200), nullable=False)
    url = Column(String(500), unique=True, nullable=False)  # RSS feed URL
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)  # Favicon or logo

    # Source type
    source_type = Column(String(50), default="rss", nullable=False)  # rss, atom, api

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(
        Boolean, default=False, nullable=False
    )  # Pre-configured sources

    # Fetch settings
    fetch_interval_minutes = Column(Integer, default=30, nullable=False)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_fetch_status = Column(String(50), nullable=True)  # success, error
    last_fetch_error = Column(Text, nullable=True)

    # Statistics
    total_articles = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    articles = relationship(
        "NewsArticle", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<NewsSource(name={self.name}, url={self.url})>"


class NewsArticle(Base):
    """
    Security news articles fetched from RSS feeds.
    """

    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)

    # Source relationship
    source_id = Column(
        Integer, ForeignKey("news_sources.id"), nullable=False, index=True
    )

    # Article details
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False)  # Original article URL
    author = Column(String(200), nullable=True)

    # Content
    original_summary = Column(Text, nullable=True)  # Original RSS description
    content = Column(Text, nullable=True)  # Full content if available

    # LLM-processed fields
    llm_summary = Column(Text, nullable=True)  # LLM-generated summary
    llm_key_points = Column(JSON, nullable=True)  # Key takeaways as list
    llm_relevance_score = Column(Float, nullable=True)  # 0-1 relevance to security
    llm_processed = Column(Boolean, default=False, nullable=False)
    llm_processed_at = Column(DateTime(timezone=True), nullable=True)

    # Categorization
    categories = Column(JSON, nullable=True)  # ["vulnerability", "malware", "breach"]
    tags = Column(JSON, nullable=True)  # Extracted tags

    # Related CVEs (if mentioned in article)
    related_cves = Column(JSON, nullable=True)  # ["CVE-2024-1234", ...]

    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    source = relationship("NewsSource", back_populates="articles")

    # Indexes
    __table_args__ = (
        Index("idx_news_articles_source_published", "source_id", "published_at"),
        Index("idx_news_articles_published", "published_at"),
        Index(
            "ix_news_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

    def __repr__(self):
        return f"<NewsArticle(title={self.title[:50]}...)>"


class WaitlistEntry(Base):
    """
    Waitlist entries for beta launch signups.
    Uses token-based email verification (link in email).
    """

    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Email verification via token
    verification_token = Column(String(64), unique=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Launch notification
    notified = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<WaitlistEntry(email={self.email}, verified={self.is_verified})>"


# =============================================================================
# Tech Stack Models - For CVE Matching
# =============================================================================


class TechStack(Base):
    """
    User's technology stack for CVE vulnerability matching.
    Can be created by anonymous users (session_id) or authenticated users (user_id).
    """

    __tablename__ = "tech_stacks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Owner - either session_id (anonymous) or user_id (authenticated)
    session_id = Column(String(64), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # Packages stored as JSONB array
    # Format: [{"name": "react", "version": "18.2.0", "ecosystem": "npm"}, ...]
    packages = Column(JSONB, nullable=False, default=list)

    # Source file type that was parsed
    source_type = Column(
        String(50), nullable=True
    )  # package.json, requirements.txt, etc.

    # Statistics (cached for performance)
    package_count = Column(Integer, nullable=False, default=0)
    vulnerable_count = Column(Integer, nullable=False, default=0)
    critical_count = Column(Integer, nullable=False, default=0)
    high_count = Column(Integer, nullable=False, default=0)

    # Last scan timestamp
    last_scanned_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="tech_stacks")
    matches = relationship(
        "TechStackMatch", back_populates="tech_stack", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TechStack(name={self.name}, packages={self.package_count})>"


class TechStackMatch(Base):
    """
    Cached CVE matches for a tech stack package.
    Links a package in a tech stack to a vulnerability.
    """

    __tablename__ = "tech_stack_matches"

    id = Column(Integer, primary_key=True, index=True)
    tech_stack_id = Column(
        Integer, ForeignKey("tech_stacks.id", ondelete="CASCADE"), nullable=False
    )
    vulnerability_id = Column(
        Integer, ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=False
    )

    # Package info
    package_name = Column(String(255), nullable=False)
    package_version = Column(String(100), nullable=True)
    ecosystem = Column(String(50), nullable=False)  # npm, pypi, rubygems, etc.

    # Match details
    match_type = Column(
        String(50), nullable=False
    )  # exact, version_range, product_name
    match_confidence = Column(Float, nullable=False, default=0.5)

    # Matched CPE or product info
    matched_cpe = Column(String(500), nullable=True)
    matched_vendor = Column(String(255), nullable=True)
    matched_product = Column(String(255), nullable=True)

    # Timestamps
    matched_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tech_stack = relationship("TechStack", back_populates="matches")
    vulnerability = relationship("Vulnerability")

    # Indexes
    __table_args__ = (
        Index("ix_tech_stack_matches_package", "package_name", "ecosystem"),
    )

    def __repr__(self):
        return f"<TechStackMatch(package={self.package_name}, cve={self.vulnerability_id})>"


class PageView(Base):
    """
    Track page views for site analytics.
    Stores anonymous visitor data for statistics.
    """

    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)

    # Page info
    path = Column(String(500), nullable=False, index=True)
    referrer = Column(String(1000), nullable=True)

    # Visitor info (anonymized)
    visitor_id = Column(String(64), nullable=True, index=True)  # Anonymous session ID
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(200), nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Indexes for analytics queries
    __table_args__ = (
        Index("idx_page_views_path_created", "path", "created_at"),
        Index("idx_page_views_date", "created_at"),
    )

    def __repr__(self):
        return f"<PageView(path={self.path}, created_at={self.created_at})>"


class PackageCPEMapping(Base):
    """
    Known mappings between package names and CPE identifiers.
    Used to improve CVE matching accuracy.
    """

    __tablename__ = "package_cpe_mappings"

    id = Column(Integer, primary_key=True, index=True)
    ecosystem = Column(String(50), nullable=False)  # npm, pypi, etc.
    package_name = Column(String(255), nullable=False)

    # CPE components
    cpe_vendor = Column(String(255), nullable=False)
    cpe_product = Column(String(255), nullable=False)

    # Confidence and source
    confidence = Column(Float, nullable=False, default=1.0)
    source = Column(String(50), nullable=False, default="manual")  # manual, nvd, osv
    verified = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index("ix_package_cpe_mappings_lookup", "ecosystem", "package_name"),
    )

    def __repr__(self):
        return f"<PackageCPEMapping({self.ecosystem}:{self.package_name} -> {self.cpe_vendor}:{self.cpe_product})>"
