"""
Enums for API input validation.

Prevents SQL injection and ensures type safety.
"""

from enum import Enum


class SeverityEnum(str, Enum):
    """Vulnerability severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class SortOrderEnum(str, Enum):
    """Sort order for queries."""

    ASC = "asc"
    DESC = "desc"


class VulnerabilitySortFieldEnum(str, Enum):
    """Allowed sort fields for vulnerabilities."""

    PRIORITY_SCORE = "priority_score"
    CVSS_SCORE = "cvss_score"
    PUBLISHED_AT = "published_at"
    MODIFIED_AT = "modified_at"
    CVE_ID = "cve_id"
    SEVERITY = "severity"


class SearchSortFieldEnum(str, Enum):
    """Allowed sort fields for search."""

    RELEVANCE = "relevance"
    PUBLISHED_AT = "published_at"
    CVSS_SCORE = "cvss_score"
    PRIORITY_SCORE = "priority_score"


class DataSourceEnum(str, Enum):
    """Available data sources."""

    CISA_KEV = "cisa_kev"
    NVD_CVE = "nvd_cve"
    EU_CVE_SEARCH = "eu_cve_search"
    BSI_CERT = "bsi_cert"
    ALL = "all"


class LLMPriorityEnum(str, Enum):
    """LLM processing priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
