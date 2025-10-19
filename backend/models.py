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
