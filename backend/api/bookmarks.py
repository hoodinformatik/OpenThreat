"""
API endpoints for CVE bookmarks/watchlist.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Bookmark, User, Vulnerability
from ..utils.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================


class BookmarkCreate(BaseModel):
    """Schema for creating a bookmark."""

    cve_id: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)


class BookmarkUpdate(BaseModel):
    """Schema for updating bookmark notes."""

    notes: Optional[str] = Field(None, max_length=1000)


class VulnerabilityInfo(BaseModel):
    """Minimal vulnerability info for bookmark response."""

    cve_id: str
    description: str
    severity: Optional[str]
    cvss_score: Optional[float]
    published_date: Optional[datetime]
    is_exploited: bool

    class Config:
        from_attributes = True


class BookmarkResponse(BaseModel):
    """Response schema for a bookmark."""

    id: int
    cve_id: str
    user_id: int
    created_at: datetime
    notes: Optional[str]
    vulnerability: Optional[VulnerabilityInfo]

    class Config:
        from_attributes = True


class BookmarkListResponse(BaseModel):
    """Response schema for list of bookmarks."""

    bookmarks: List[BookmarkResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED
)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Add a CVE to user's bookmarks.
    """
    # Verify CVE exists
    vulnerability = (
        db.query(Vulnerability)
        .filter(Vulnerability.cve_id == bookmark_data.cve_id)
        .first()
    )
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CVE {bookmark_data.cve_id} not found",
        )

    # Check if already bookmarked
    existing = (
        db.query(Bookmark)
        .filter(
            Bookmark.user_id == current_user.id,
            Bookmark.cve_id == bookmark_data.cve_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CVE already bookmarked",
        )

    # Create bookmark
    bookmark = Bookmark(
        user_id=current_user.id,
        cve_id=bookmark_data.cve_id,
        notes=bookmark_data.notes,
        created_at=datetime.now(timezone.utc),
    )

    db.add(bookmark)

    # Update bookmark count
    vulnerability.bookmark_count = (vulnerability.bookmark_count or 0) + 1

    db.commit()
    db.refresh(bookmark)

    logger.info(f"User {current_user.username} bookmarked CVE {bookmark_data.cve_id}")

    # Load vulnerability relationship
    db.refresh(bookmark, ["vulnerability"])

    return BookmarkResponse(
        id=bookmark.id,
        cve_id=bookmark.cve_id,
        user_id=bookmark.user_id,
        created_at=bookmark.created_at,
        notes=bookmark.notes,
        vulnerability=(
            VulnerabilityInfo(
                cve_id=vulnerability.cve_id,
                description=vulnerability.description,
                severity=vulnerability.severity,
                cvss_score=vulnerability.cvss_score,
                published_date=vulnerability.published_date,
                is_exploited=vulnerability.is_exploited,
            )
            if bookmark.vulnerability
            else None
        ),
    )


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def get_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get user's bookmarked CVEs.
    """
    # Build query
    query = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == current_user.id)
        .options(joinedload(Bookmark.vulnerability))
        .order_by(desc(Bookmark.created_at))
    )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    bookmarks = query.offset(offset).limit(page_size).all()

    # Build response
    bookmark_responses = []
    for bookmark in bookmarks:
        bookmark_responses.append(
            BookmarkResponse(
                id=bookmark.id,
                cve_id=bookmark.cve_id,
                user_id=bookmark.user_id,
                created_at=bookmark.created_at,
                notes=bookmark.notes,
                vulnerability=(
                    VulnerabilityInfo(
                        cve_id=bookmark.vulnerability.cve_id,
                        description=bookmark.vulnerability.description,
                        severity=bookmark.vulnerability.severity,
                        cvss_score=bookmark.vulnerability.cvss_score,
                        published_date=bookmark.vulnerability.published_date,
                        is_exploited=bookmark.vulnerability.is_exploited,
                    )
                    if bookmark.vulnerability
                    else None
                ),
            )
        )

    return BookmarkListResponse(
        bookmarks=bookmark_responses, total=total, page=page, page_size=page_size
    )


@router.get("/bookmarks/check/{cve_id}", response_model=dict)
async def check_bookmark(
    cve_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Check if a CVE is bookmarked by the current user.
    """
    bookmark = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == current_user.id, Bookmark.cve_id == cve_id)
        .first()
    )

    return {
        "is_bookmarked": bookmark is not None,
        "bookmark_id": bookmark.id if bookmark else None,
    }


@router.put("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: int,
    bookmark_data: BookmarkUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update bookmark notes.
    """
    bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
        )

    # Check ownership
    if bookmark.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own bookmarks",
        )

    # Update notes
    bookmark.notes = bookmark_data.notes
    db.commit()
    db.refresh(bookmark, ["vulnerability"])

    logger.info(f"User {current_user.username} updated bookmark {bookmark_id}")

    return BookmarkResponse(
        id=bookmark.id,
        cve_id=bookmark.cve_id,
        user_id=bookmark.user_id,
        created_at=bookmark.created_at,
        notes=bookmark.notes,
        vulnerability=(
            VulnerabilityInfo(
                cve_id=bookmark.vulnerability.cve_id,
                description=bookmark.vulnerability.description,
                severity=bookmark.vulnerability.severity,
                cvss_score=bookmark.vulnerability.cvss_score,
                published_date=bookmark.vulnerability.published_date,
                is_exploited=bookmark.vulnerability.is_exploited,
            )
            if bookmark.vulnerability
            else None
        ),
    )


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Remove a bookmark.
    """
    bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
        )

    # Check ownership
    if bookmark.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own bookmarks",
        )

    # Get vulnerability to update count
    vulnerability = (
        db.query(Vulnerability).filter(Vulnerability.cve_id == bookmark.cve_id).first()
    )
    if vulnerability:
        vulnerability.bookmark_count = max(0, (vulnerability.bookmark_count or 0) - 1)

    db.delete(bookmark)
    db.commit()

    logger.info(f"User {current_user.username} removed bookmark {bookmark_id}")

    return None


@router.delete("/bookmarks/cve/{cve_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark_by_cve(
    cve_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Remove a bookmark by CVE ID.
    """
    bookmark = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == current_user.id, Bookmark.cve_id == cve_id)
        .first()
    )
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
        )

    # Get vulnerability to update count
    vulnerability = (
        db.query(Vulnerability).filter(Vulnerability.cve_id == bookmark.cve_id).first()
    )
    if vulnerability:
        vulnerability.bookmark_count = max(0, (vulnerability.bookmark_count or 0) - 1)

    db.delete(bookmark)
    db.commit()

    logger.info(f"User {current_user.username} removed bookmark for CVE {cve_id}")

    return None
