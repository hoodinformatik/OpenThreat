"""
Search endpoints with advanced filtering.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func, cast, String
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models import Vulnerability
from ..schemas import PaginatedResponse

router = APIRouter()


@router.get("/search", response_model=PaginatedResponse)
async def search_vulnerabilities(
    q: Optional[str] = Query(None, description="Search query (CVE ID, title, description)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    exploited: Optional[bool] = Query(None, description="Filter by exploitation status"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    product: Optional[str] = Query(None, description="Filter by product"),
    cwe: Optional[str] = Query(None, description="Filter by CWE ID"),
    min_cvss: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum CVSS score"),
    max_cvss: Optional[float] = Query(None, ge=0.0, le=10.0, description="Maximum CVSS score"),
    published_after: Optional[str] = Query(None, description="Published after date (YYYY-MM-DD)"),
    published_before: Optional[str] = Query(None, description="Published before date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("priority_score", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Advanced search for vulnerabilities.
    
    **Search Parameters:**
    - `q`: Full-text search in CVE ID, title, and description
    - `severity`: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
    - `exploited`: Filter by exploitation status (true/false)
    - `vendor`: Filter by vendor name
    - `product`: Filter by product name
    - `cwe`: Filter by CWE ID (e.g., CWE-79)
    - `min_cvss`, `max_cvss`: CVSS score range
    - `published_after`, `published_before`: Publication date range
    - `sort_by`: Field to sort by (priority_score, cvss_score, published_at, etc.)
    - `sort_order`: Sort direction (asc/desc)
    """
    # Build query - only CVEs
    query = db.query(Vulnerability).filter(Vulnerability.cve_id.like('CVE-%'))
    
    # Text search
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Vulnerability.cve_id.ilike(search_term),
                Vulnerability.title.ilike(search_term),
                Vulnerability.description.ilike(search_term)
            )
        )
    
    # Severity filter
    if severity:
        query = query.filter(Vulnerability.severity == severity.upper())
    
    # Exploitation filter
    if exploited is not None:
        query = query.filter(Vulnerability.exploited_in_the_wild == exploited)
    
    # Vendor filter
    if vendor:
        query = query.filter(
            func.lower(cast(Vulnerability.vendors, String)).contains(vendor.lower())
        )
    
    # Product filter
    if product:
        query = query.filter(
            func.lower(cast(Vulnerability.products, String)).contains(product.lower())
        )
    
    # CWE filter
    if cwe:
        cwe_upper = cwe.upper()
        if not cwe_upper.startswith("CWE-"):
            cwe_upper = f"CWE-{cwe_upper}"
        query = query.filter(
            cast(Vulnerability.cwe_ids, String).contains(cwe_upper)
        )
    
    # CVSS score range
    if min_cvss is not None:
        query = query.filter(Vulnerability.cvss_score >= min_cvss)
    
    if max_cvss is not None:
        query = query.filter(Vulnerability.cvss_score <= max_cvss)
    
    # Publication date range
    if published_after:
        try:
            date_after = datetime.fromisoformat(published_after)
            query = query.filter(Vulnerability.published_at >= date_after)
        except ValueError:
            pass
    
    if published_before:
        try:
            date_before = datetime.fromisoformat(published_before)
            query = query.filter(Vulnerability.published_at <= date_before)
        except ValueError:
            pass
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Vulnerability, sort_by, Vulnerability.priority_score)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )


@router.get("/search/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on partial query.
    
    Returns CVE IDs and titles that match the query.
    """
    search_term = f"%{q}%"
    
    results = db.query(
        Vulnerability.cve_id,
        Vulnerability.title
    ).filter(
        or_(
            Vulnerability.cve_id.ilike(search_term),
            Vulnerability.title.ilike(search_term)
        )
    ).order_by(
        desc(Vulnerability.priority_score)
    ).limit(limit).all()
    
    return {
        "suggestions": [
            {"cve_id": cve_id, "title": title}
            for cve_id, title in results
        ]
    }
