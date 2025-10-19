"""
API endpoints for CVE comments.
Supports nested comments and voting with strict XSS protection.
"""

import html
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Comment, CommentVote, User, Vulnerability
from ..utils.auth import get_current_active_user, get_optional_current_user
from ..utils.notifications import create_reply_notification, create_vote_notification

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Schemas with XSS Protection
# ============================================================================


class CommentCreate(BaseModel):
    """Schema for creating a comment - plain text only."""

    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[int] = None

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """
        Sanitize content to prevent XSS attacks.
        - Strip all HTML tags
        - Remove script tags
        - Escape special characters
        - Trim whitespace
        """
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")

        # Remove any HTML tags
        v = re.sub(r"<[^>]+>", "", v)

        # Remove script tags and their content
        v = re.sub(r"<script[^>]*>.*?</script>", "", v, flags=re.IGNORECASE | re.DOTALL)

        # Remove style tags and their content
        v = re.sub(r"<style[^>]*>.*?</style>", "", v, flags=re.IGNORECASE | re.DOTALL)

        # Escape HTML entities
        v = html.escape(v)

        # Remove any remaining dangerous patterns
        dangerous_patterns = [
            r"javascript:",
            r"on\w+\s*=",  # onclick, onload, etc.
            r"data:text/html",
        ]
        for pattern in dangerous_patterns:
            v = re.sub(pattern, "", v, flags=re.IGNORECASE)

        # Trim whitespace
        v = v.strip()

        if not v:
            raise ValueError("Content cannot be empty after sanitization")

        return v


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""

    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Same sanitization as CommentCreate."""
        return CommentCreate.sanitize_content(v)


class CommentVoteCreate(BaseModel):
    """Schema for voting on a comment."""

    vote_type: int = Field(..., ge=-1, le=1)

    @field_validator("vote_type")
    @classmethod
    def validate_vote_type(cls, v: int) -> int:
        """Ensure vote_type is either 1 (upvote) or -1 (downvote)."""
        if v not in [-1, 1]:
            raise ValueError("vote_type must be 1 (upvote) or -1 (downvote)")
        return v


class UserInfo(BaseModel):
    """User information for comment responses."""

    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Response schema for a comment."""

    id: int
    content: str
    cve_id: str
    user_id: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_edited: bool
    is_deleted: bool
    upvotes: int
    downvotes: int
    user: UserInfo
    reply_count: int = 0
    user_vote: Optional[int] = None  # Current user's vote on this comment

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Response schema for list of comments."""

    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/vulnerabilities/{cve_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    cve_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new comment on a CVE.
    Requires authentication.
    """
    # Verify CVE exists
    vulnerability = (
        db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
    )
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"CVE {cve_id} not found"
        )

    # If parent_id is provided, verify parent comment exists
    if comment_data.parent_id:
        parent_comment = (
            db.query(Comment)
            .filter(
                Comment.id == comment_data.parent_id,
                Comment.cve_id == cve_id,
                Comment.is_deleted == False,
            )
            .first()
        )
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found"
            )

    # Create comment
    new_comment = Comment(
        content=comment_data.content,
        cve_id=cve_id,
        user_id=current_user.id,
        parent_id=comment_data.parent_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    logger.info(
        f"User {current_user.username} created comment {new_comment.id} on CVE {cve_id}"
    )

    # Load user relationship
    db.refresh(new_comment, ["user"])

    # Handle notifications
    # Notify parent comment author if this is a reply
    if comment_data.parent_id:
        parent_comment = (
            db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
        )
        if parent_comment:
            create_reply_notification(db, new_comment, current_user, parent_comment)

    return CommentResponse(
        id=new_comment.id,
        content=new_comment.content,
        cve_id=new_comment.cve_id,
        user_id=new_comment.user_id,
        parent_id=new_comment.parent_id,
        created_at=new_comment.created_at,
        updated_at=new_comment.updated_at,
        is_edited=new_comment.is_edited,
        is_deleted=new_comment.is_deleted,
        upvotes=new_comment.upvotes,
        downvotes=new_comment.downvotes,
        user=UserInfo(
            id=new_comment.user.id,
            username=new_comment.user.username,
            role=new_comment.user.role.value,
        ),
        reply_count=0,
        user_vote=None,
    )


@router.get("/vulnerabilities/{cve_id}/comments", response_model=CommentListResponse)
async def get_comments(
    cve_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|upvotes)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    parent_id: Optional[int] = Query(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comments for a CVE.
    Supports pagination, sorting, and filtering by parent_id.
    """
    # Verify CVE exists
    vulnerability = (
        db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()
    )
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"CVE {cve_id} not found"
        )

    # Build query
    query = db.query(Comment).filter(
        Comment.cve_id == cve_id, Comment.is_deleted == False
    )

    # Filter by parent_id
    if parent_id is not None:
        query = query.filter(Comment.parent_id == parent_id)
    else:
        # Only get top-level comments (no parent)
        query = query.filter(Comment.parent_id.is_(None))

    # Apply sorting
    if sort_by == "upvotes":
        sort_column = Comment.upvotes - Comment.downvotes
    else:
        sort_column = Comment.created_at

    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    comments = (
        query.options(joinedload(Comment.user)).offset(offset).limit(page_size).all()
    )

    # Get reply counts for each comment
    comment_ids = [c.id for c in comments]
    reply_counts = {}
    if comment_ids:
        reply_count_query = (
            db.query(Comment.parent_id, func.count(Comment.id).label("count"))
            .filter(Comment.parent_id.in_(comment_ids), Comment.is_deleted == False)
            .group_by(Comment.parent_id)
            .all()
        )

        reply_counts = {parent_id: count for parent_id, count in reply_count_query}

    # Get user's votes if authenticated
    user_votes = {}
    if current_user:
        votes = (
            db.query(CommentVote)
            .filter(
                CommentVote.comment_id.in_(comment_ids),
                CommentVote.user_id == current_user.id,
            )
            .all()
        )
        user_votes = {vote.comment_id: vote.vote_type for vote in votes}

    # Build response
    comment_responses = []
    for comment in comments:
        comment_responses.append(
            CommentResponse(
                id=comment.id,
                content=comment.content,
                cve_id=comment.cve_id,
                user_id=comment.user_id,
                parent_id=comment.parent_id,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                is_edited=comment.is_edited,
                is_deleted=comment.is_deleted,
                upvotes=comment.upvotes,
                downvotes=comment.downvotes,
                user=UserInfo(
                    id=comment.user.id,
                    username=comment.user.username,
                    role=comment.user.role.value,
                ),
                reply_count=reply_counts.get(comment.id, 0),
                user_vote=user_votes.get(comment.id),
            )
        )

    return CommentListResponse(
        comments=comment_responses, total=total, page=page, page_size=page_size
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update a comment.
    Only the comment author can update their comment.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Check if user is the author
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    # Check if comment is deleted
    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Comment has been deleted"
        )

    # Update comment
    comment.content = comment_data.content
    comment.updated_at = datetime.now(timezone.utc)
    comment.is_edited = True

    db.commit()
    db.refresh(comment, ["user"])

    logger.info(f"User {current_user.username} updated comment {comment_id}")

    # Get reply count
    reply_count = (
        db.query(func.count(Comment.id))
        .filter(Comment.parent_id == comment_id, Comment.is_deleted == False)
        .scalar()
        or 0
    )

    # Get user's vote
    user_vote = (
        db.query(CommentVote)
        .filter(
            CommentVote.comment_id == comment_id, CommentVote.user_id == current_user.id
        )
        .first()
    )

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        cve_id=comment.cve_id,
        user_id=comment.user_id,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_edited=comment.is_edited,
        is_deleted=comment.is_deleted,
        upvotes=comment.upvotes,
        downvotes=comment.downvotes,
        user=UserInfo(
            id=comment.user.id,
            username=comment.user.username,
            role=comment.user.role.value,
        ),
        reply_count=reply_count,
        user_vote=user_vote.vote_type if user_vote else None,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a comment (soft delete).
    Only the comment author or admin can delete a comment.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Check if user is the author or admin
    if comment.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    # Soft delete
    comment.is_deleted = True
    comment.content = "[deleted]"
    comment.updated_at = datetime.now(timezone.utc)

    db.commit()

    logger.info(f"User {current_user.username} deleted comment {comment_id}")

    return None


@router.post("/comments/{comment_id}/vote", response_model=CommentResponse)
async def vote_comment(
    comment_id: int,
    vote_data: CommentVoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Vote on a comment (upvote or downvote).
    User can change their vote or remove it by voting the same type again.
    """
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.is_deleted == False)
        .first()
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Check if user already voted
    existing_vote = (
        db.query(CommentVote)
        .filter(
            CommentVote.comment_id == comment_id, CommentVote.user_id == current_user.id
        )
        .first()
    )

    if existing_vote:
        # If same vote type, remove the vote
        if existing_vote.vote_type == vote_data.vote_type:
            # Remove vote
            if existing_vote.vote_type == 1:
                comment.upvotes = max(0, comment.upvotes - 1)
            else:
                comment.downvotes = max(0, comment.downvotes - 1)

            db.delete(existing_vote)
            db.commit()
            db.refresh(comment, ["user"])

            logger.info(
                f"User {current_user.username} removed vote from comment {comment_id}"
            )

            user_vote = None
        else:
            # Change vote
            old_vote = existing_vote.vote_type
            existing_vote.vote_type = vote_data.vote_type
            existing_vote.updated_at = datetime.now(timezone.utc)

            # Update counts
            if old_vote == 1:
                comment.upvotes = max(0, comment.upvotes - 1)
                comment.downvotes += 1
            else:
                comment.downvotes = max(0, comment.downvotes - 1)
                comment.upvotes += 1

            db.commit()
            db.refresh(comment, ["user"])

            logger.info(
                f"User {current_user.username} changed vote on comment {comment_id}"
            )

            user_vote = vote_data.vote_type
    else:
        # Create new vote
        new_vote = CommentVote(
            comment_id=comment_id,
            user_id=current_user.id,
            vote_type=vote_data.vote_type,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Update counts
        if vote_data.vote_type == 1:
            comment.upvotes += 1
        else:
            comment.downvotes += 1

        db.add(new_vote)
        db.commit()
        db.refresh(comment, ["user"])

        logger.info(f"User {current_user.username} voted on comment {comment_id}")

        # Create notification for vote milestones
        create_vote_notification(db, comment, current_user, vote_data.vote_type)

        user_vote = vote_data.vote_type

    # Get reply count
    reply_count = (
        db.query(func.count(Comment.id))
        .filter(Comment.parent_id == comment_id, Comment.is_deleted == False)
        .scalar()
        or 0
    )

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        cve_id=comment.cve_id,
        user_id=comment.user_id,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_edited=comment.is_edited,
        is_deleted=comment.is_deleted,
        upvotes=comment.upvotes,
        downvotes=comment.downvotes,
        user=UserInfo(
            id=comment.user.id,
            username=comment.user.username,
            role=comment.user.role.value,
        ),
        reply_count=reply_count,
        user_vote=user_vote,
    )


@router.get("/comments/{comment_id}/replies", response_model=CommentListResponse)
async def get_comment_replies(
    comment_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Get replies to a specific comment.
    """
    # Verify parent comment exists
    parent_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Get replies
    return await get_comments(
        cve_id=parent_comment.cve_id,
        page=page,
        page_size=page_size,
        sort_by="created_at",
        order="asc",
        parent_id=comment_id,
        current_user=current_user,
        db=db,
    )
