"""
Trending/Hot CVE endpoints with time-based filtering.
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CVEVote, User, Vulnerability
from ..schemas import PaginatedResponse
from ..utils.auth import get_optional_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Enums
# ============================================================================


class TimeRangeEnum(str, Enum):
    """Time range options for trending CVEs."""

    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    ALL_TIME = "all_time"


class TrendingTypeEnum(str, Enum):
    """Type of trending calculation."""

    HOT = "hot"  # Based on recent activity (votes in time period)
    TOP = "top"  # Based on total score (upvotes - downvotes)


# ============================================================================
# Helper Functions
# ============================================================================


def get_time_cutoff(time_range: TimeRangeEnum) -> Optional[datetime]:
    """Get the cutoff datetime for a given time range."""
    now = datetime.now(timezone.utc)

    if time_range == TimeRangeEnum.TODAY:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == TimeRangeEnum.THIS_WEEK:
        # Start of week (Monday)
        days_since_monday = now.weekday()
        return (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif time_range == TimeRangeEnum.THIS_MONTH:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # ALL_TIME
        return None


def calculate_hot_score(
    upvotes: int, downvotes: int, vote_count: int, hours_old: float
) -> float:
    """
    Calculate "hot" score using a Reddit-like algorithm.

    Score considers:
    - Net votes (upvotes - downvotes)
    - Total engagement (vote_count)
    - Time decay (newer = higher score)
    """
    net_votes = upvotes - downvotes

    # Avoid division by zero
    if hours_old <= 0:
        hours_old = 0.1

    # Base score from votes
    score = net_votes + (vote_count * 0.5)

    # Time decay: divide by age in hours raised to 1.5
    # This means newer items get significantly higher scores
    hot_score = score / pow(hours_old + 2, 1.5)

    return hot_score


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/vulnerabilities/trending/{trending_type}", response_model=PaginatedResponse
)
async def get_trending_cves(
    trending_type: TrendingTypeEnum,
    time_range: TimeRangeEnum = Query(
        TimeRangeEnum.THIS_WEEK, description="Time range for trending calculation"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Get trending CVEs based on voting activity.

    **Trending Types:**
    - `hot`: CVEs with most recent voting activity (time-weighted)
    - `top`: CVEs with highest vote score (upvotes - downvotes)

    **Time Ranges:**
    - `today`: Last 24 hours
    - `this_week`: Current week (Monday to now)
    - `this_month`: Current month
    - `all_time`: All time
    """
    cutoff_time = get_time_cutoff(time_range)

    if trending_type == TrendingTypeEnum.HOT:
        # HOT: Based on recent voting activity with time decay

        # Build subquery for vote counts in time period
        vote_subquery = db.query(
            CVEVote.cve_id,
            func.count(CVEVote.id).label("vote_count"),
            func.min(CVEVote.created_at).label("first_vote_time"),
        )

        if cutoff_time:
            vote_subquery = vote_subquery.filter(CVEVote.created_at >= cutoff_time)

        vote_subquery = vote_subquery.group_by(CVEVote.cve_id).subquery()

        # Join with vulnerabilities
        query = (
            db.query(
                Vulnerability,
                vote_subquery.c.vote_count,
                vote_subquery.c.first_vote_time,
            )
            .join(vote_subquery, Vulnerability.cve_id == vote_subquery.c.cve_id)
            .filter(Vulnerability.cve_id.like("CVE-%"))
        )

        # Get results
        results = query.all()

        # Calculate hot scores
        now = datetime.now(timezone.utc)
        scored_results = []

        for vuln, vote_count, first_vote_time in results:
            # Calculate hours since first vote in period
            hours_old = (now - first_vote_time).total_seconds() / 3600

            hot_score = calculate_hot_score(
                vuln.upvotes, vuln.downvotes, vote_count or 0, hours_old
            )

            scored_results.append((vuln, hot_score))

        # Sort by hot score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Apply pagination
        total = len(scored_results)
        offset = (page - 1) * page_size
        items = [vuln for vuln, _ in scored_results[offset : offset + page_size]]

    else:  # TOP
        # TOP: Based on total vote score (upvotes - downvotes)

        query = db.query(Vulnerability).filter(Vulnerability.cve_id.like("CVE-%"))

        # If time range specified, filter by CVEs that received votes in that period
        if cutoff_time:
            # Get CVE IDs that received votes in the time period
            voted_cve_ids = (
                db.query(CVEVote.cve_id)
                .filter(CVEVote.created_at >= cutoff_time)
                .distinct()
                .subquery()
            )
            query = query.filter(Vulnerability.cve_id.in_(voted_cve_ids))

        # Calculate net score and sort
        query = query.order_by(
            desc(Vulnerability.upvotes - Vulnerability.downvotes),
            desc(Vulnerability.upvotes),  # Tiebreaker: more upvotes
        )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get("/vulnerabilities/trending/stats")
async def get_trending_stats(
    time_range: TimeRangeEnum = Query(
        TimeRangeEnum.THIS_WEEK, description="Time range for stats"
    ),
    db: Session = Depends(get_db),
):
    """
    Get statistics about trending CVEs.

    Returns:
    - Total CVEs with votes in time period
    - Total votes cast in time period
    - Most voted CVE in time period
    """
    cutoff_time = get_time_cutoff(time_range)

    # Build base query
    vote_query = db.query(CVEVote)
    if cutoff_time:
        vote_query = vote_query.filter(CVEVote.created_at >= cutoff_time)

    # Total votes in period
    total_votes = vote_query.count()

    # Unique CVEs voted on
    unique_cves = vote_query.distinct(CVEVote.cve_id).count()

    # Most voted CVE in period
    most_voted_cve = None
    if total_votes > 0:
        vote_counts = (
            vote_query.with_entities(
                CVEVote.cve_id, func.count(CVEVote.id).label("vote_count")
            )
            .group_by(CVEVote.cve_id)
            .order_by(desc("vote_count"))
            .first()
        )

        if vote_counts:
            cve_id, vote_count = vote_counts
            vuln = (
                db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
            )
            if vuln:
                most_voted_cve = {
                    "cve_id": vuln.cve_id,
                    "title": vuln.title,
                    "vote_count": vote_count,
                    "upvotes": vuln.upvotes,
                    "downvotes": vuln.downvotes,
                }

    return {
        "time_range": time_range.value,
        "total_votes": total_votes,
        "unique_cves": unique_cves,
        "most_voted_cve": most_voted_cve,
    }
