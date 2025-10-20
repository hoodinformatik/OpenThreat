"""
CVE Voting API endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CVEVote, User, Vulnerability
from ..utils.auth import get_current_active_user, get_optional_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class CVEVoteCreate(BaseModel):
    """Schema for voting on a CVE."""

    vote_type: int = Field(..., ge=-1, le=1)

    @field_validator("vote_type")
    @classmethod
    def validate_vote_type(cls, v: int) -> int:
        """Ensure vote_type is either 1 (upvote) or -1 (downvote)."""
        if v not in [-1, 1]:
            raise ValueError("vote_type must be 1 (upvote) or -1 (downvote)")
        return v


class CVEVoteResponse(BaseModel):
    """Response schema for CVE vote status."""

    cve_id: str
    upvotes: int
    downvotes: int
    user_vote: Optional[int] = None  # Current user's vote

    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/vulnerabilities/{cve_id}/vote", response_model=CVEVoteResponse)
async def vote_cve(
    cve_id: str,
    vote_data: CVEVoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Vote on a CVE (upvote or downvote).
    User can change their vote or remove it by voting the same type again.
    """
    # Verify CVE exists
    vulnerability = (
        db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
    )
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"CVE {cve_id} not found"
        )

    # Check if user already voted
    existing_vote = (
        db.query(CVEVote)
        .filter(CVEVote.cve_id == cve_id, CVEVote.user_id == current_user.id)
        .first()
    )

    if existing_vote:
        # If same vote type, remove the vote
        if existing_vote.vote_type == vote_data.vote_type:
            # Remove vote
            if existing_vote.vote_type == 1:
                vulnerability.upvotes = max(0, vulnerability.upvotes - 1)
            else:
                vulnerability.downvotes = max(0, vulnerability.downvotes - 1)

            db.delete(existing_vote)
            db.commit()
            db.refresh(vulnerability)

            logger.info(f"User {current_user.username} removed vote from CVE {cve_id}")

            user_vote = None
        else:
            # Change vote
            old_vote = existing_vote.vote_type
            existing_vote.vote_type = vote_data.vote_type
            existing_vote.updated_at = datetime.now(timezone.utc)

            # Update counts
            if old_vote == 1:
                vulnerability.upvotes = max(0, vulnerability.upvotes - 1)
                vulnerability.downvotes += 1
            else:
                vulnerability.downvotes = max(0, vulnerability.downvotes - 1)
                vulnerability.upvotes += 1

            db.commit()
            db.refresh(vulnerability)

            logger.info(f"User {current_user.username} changed vote on CVE {cve_id}")

            user_vote = vote_data.vote_type
    else:
        # Create new vote
        new_vote = CVEVote(
            cve_id=cve_id,
            user_id=current_user.id,
            vote_type=vote_data.vote_type,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Update counts
        if vote_data.vote_type == 1:
            vulnerability.upvotes += 1
        else:
            vulnerability.downvotes += 1

        db.add(new_vote)
        db.commit()
        db.refresh(vulnerability)

        logger.info(f"User {current_user.username} voted on CVE {cve_id}")

        user_vote = vote_data.vote_type

    return CVEVoteResponse(
        cve_id=vulnerability.cve_id,
        upvotes=vulnerability.upvotes,
        downvotes=vulnerability.downvotes,
        user_vote=user_vote,
    )


@router.get("/vulnerabilities/{cve_id}/vote", response_model=CVEVoteResponse)
async def get_cve_vote_status(
    cve_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Get vote status for a CVE.
    Returns vote counts and current user's vote if authenticated.
    """
    # Verify CVE exists
    vulnerability = (
        db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
    )
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"CVE {cve_id} not found"
        )

    # Get user's vote if authenticated
    user_vote = None
    if current_user:
        vote = (
            db.query(CVEVote)
            .filter(CVEVote.cve_id == cve_id, CVEVote.user_id == current_user.id)
            .first()
        )
        if vote:
            user_vote = vote.vote_type

    return CVEVoteResponse(
        cve_id=vulnerability.cve_id,
        upvotes=vulnerability.upvotes,
        downvotes=vulnerability.downvotes,
        user_vote=user_vote,
    )


@router.delete("/vulnerabilities/{cve_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cve_vote(
    cve_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Remove user's vote from a CVE.
    """
    # Verify CVE exists
    vulnerability = (
        db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
    )
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"CVE {cve_id} not found"
        )

    # Find and remove vote
    existing_vote = (
        db.query(CVEVote)
        .filter(CVEVote.cve_id == cve_id, CVEVote.user_id == current_user.id)
        .first()
    )

    if not existing_vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No vote found to remove"
        )

    # Update counts
    if existing_vote.vote_type == 1:
        vulnerability.upvotes = max(0, vulnerability.upvotes - 1)
    else:
        vulnerability.downvotes = max(0, vulnerability.downvotes - 1)

    db.delete(existing_vote)
    db.commit()

    logger.info(f"User {current_user.username} removed vote from CVE {cve_id}")

    return None
