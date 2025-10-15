"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


class VulnerabilityBase(BaseModel):
    """Base vulnerability schema."""
    cve_id: str
    title: str
    description: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    severity: Optional[str] = None
    exploited_in_the_wild: bool = False
    priority_score: Optional[float] = None


class VulnerabilityList(VulnerabilityBase):
    """Vulnerability schema for list views."""
    published_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    sources: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class VulnerabilityDetail(VulnerabilityBase):
    """Vulnerability schema for detail views."""
    id: int
    published_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    cisa_due_date: Optional[date] = None
    cwe_ids: Optional[List[str]] = None
    affected_products: Optional[List[str]] = None
    vendors: Optional[List[str]] = None
    products: Optional[List[str]] = None
    references: Optional[List[dict]] = None
    sources: Optional[List[str]] = None
    source_tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[VulnerabilityList]


class StatsResponse(BaseModel):
    """Statistics response."""
    total_vulnerabilities: int
    exploited_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    by_severity: dict
    recent_updates: int
    last_update: Optional[datetime] = None


class SearchQuery(BaseModel):
    """Search query parameters."""
    q: Optional[str] = Field(None, description="Search query")
    severity: Optional[str] = Field(None, description="Filter by severity")
    exploited: Optional[bool] = Field(None, description="Filter by exploitation status")
    vendor: Optional[str] = Field(None, description="Filter by vendor")
    product: Optional[str] = Field(None, description="Filter by product")
    cwe: Optional[str] = Field(None, description="Filter by CWE ID")
    min_cvss: Optional[float] = Field(None, ge=0.0, le=10.0, description="Minimum CVSS score")
    max_cvss: Optional[float] = Field(None, ge=0.0, le=10.0, description="Maximum CVSS score")
    published_after: Optional[date] = Field(None, description="Published after date")
    published_before: Optional[date] = Field(None, description="Published before date")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("priority_score", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")


class TechniqueBase(BaseModel):
    """Base technique schema."""
    technique_id: str
    name: str
    description: Optional[str] = None
    tactics: Optional[List[str]] = None
    platforms: Optional[List[str]] = None


class TechniqueDetail(TechniqueBase):
    """Technique schema for detail views."""
    id: int
    data_sources: Optional[List[str]] = None
    detection: Optional[str] = None
    mitigation: Optional[str] = None
    references: Optional[List[dict]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IOCBase(BaseModel):
    """Base IOC schema."""
    ioc_type: str
    value: str
    threat_type: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "active"


class IOCDetail(IOCBase):
    """IOC schema for detail views."""
    id: int
    tags: Optional[List[str]] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    context: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    version: str
    timestamp: datetime
