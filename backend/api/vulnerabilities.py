"""
Vulnerability endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional

from ..database import get_db
from ..models import Vulnerability
from ..schemas import VulnerabilityList, VulnerabilityDetail, PaginatedResponse

router = APIRouter()


@router.get("/vulnerabilities", response_model=PaginatedResponse)
async def list_vulnerabilities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    exploited: Optional[bool] = Query(None, description="Filter by exploitation status"),
    sort_by: str = Query("priority_score", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    List vulnerabilities with pagination and filtering.
    
    **Filters:**
    - `severity`: CRITICAL, HIGH, MEDIUM, LOW
    - `exploited`: true/false for exploited in the wild
    - `sort_by`: priority_score, cvss_score, published_at, modified_at
    - `sort_order`: asc, desc
    """
    # Build query
    query = db.query(Vulnerability)
    
    # Apply filters
    if severity:
        query = query.filter(Vulnerability.severity == severity.upper())
    
    if exploited is not None:
        query = query.filter(Vulnerability.exploited_in_the_wild == exploited)
    
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


@router.get("/vulnerabilities/exploited", response_model=PaginatedResponse)
async def list_exploited_vulnerabilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List vulnerabilities exploited in the wild.
    
    Returns vulnerabilities with `exploited_in_the_wild = true`,
    sorted by priority score.
    """
    query = db.query(Vulnerability).filter(
        Vulnerability.exploited_in_the_wild == True
    )
    
    total = query.count()
    
    query = query.order_by(desc(Vulnerability.priority_score))
    
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )


@router.get("/vulnerabilities/recent", response_model=PaginatedResponse)
async def list_recent_vulnerabilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_db)
):
    """
    List recently published vulnerabilities.
    
    Returns vulnerabilities published in the last N days,
    sorted by publication date (newest first).
    """
    from datetime import datetime, timedelta, timezone
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = db.query(Vulnerability).filter(
        Vulnerability.published_at >= cutoff_date
    )
    
    total = query.count()
    
    query = query.order_by(desc(Vulnerability.published_at))
    
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )


@router.get("/vulnerabilities/{cve_id}", response_model=VulnerabilityDetail)
async def get_vulnerability(
    cve_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific vulnerability.
    
    **Path Parameters:**
    - `cve_id`: CVE identifier (e.g., CVE-2024-1234)
    """
    vuln = db.query(Vulnerability).filter(
        Vulnerability.cve_id == cve_id.upper()
    ).first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail=f"Vulnerability {cve_id} not found")
    
    return vuln


@router.get("/vulnerabilities/vendor/{vendor}", response_model=PaginatedResponse)
async def list_vulnerabilities_by_vendor(
    vendor: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List vulnerabilities affecting a specific vendor.
    
    **Path Parameters:**
    - `vendor`: Vendor name (case-insensitive)
    """
    from sqlalchemy import func, cast, String
    
    # Search in vendors JSON array
    query = db.query(Vulnerability).filter(
        func.lower(cast(Vulnerability.vendors, String)).contains(vendor.lower())
    )
    
    total = query.count()
    
    query = query.order_by(desc(Vulnerability.priority_score))
    
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )
