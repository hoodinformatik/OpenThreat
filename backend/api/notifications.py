"""
API endpoints for user notifications.
Handles mentions, replies, and other notification types.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Comment, Notification, User
from ..utils.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================


class UserInfo(BaseModel):
    """User information for notifications."""

    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Response schema for a notification."""

    id: int
    type: str
    title: str
    message: str
    comment_id: Optional[int]
    cve_id: Optional[str]
    actor: Optional[UserInfo]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response schema for list of notifications."""

    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationMarkReadRequest(BaseModel):
    """Request schema for marking notifications as read."""

    notification_ids: List[int]


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get notifications for the current user.
    Supports filtering by read status and type.
    """
    # Build query
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    # Apply filters
    if unread_only:
        query = query.filter(Notification.is_read == False)

    if notification_type:
        query = query.filter(Notification.type == notification_type)

    # Get total count
    total = query.count()

    # Get unread count
    unread_count = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .scalar()
        or 0
    )

    # Paginate and order by created_at desc
    notifications = (
        query.options(joinedload(Notification.actor))
        .order_by(desc(Notification.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert to response format
    notification_responses = []
    for notif in notifications:
        actor_info = None
        if notif.actor:
            actor_info = UserInfo(
                id=notif.actor.id,
                username=notif.actor.username,
                role=notif.actor.role.value,
            )

        notification_responses.append(
            NotificationResponse(
                id=notif.id,
                type=notif.type,
                title=notif.title,
                message=notif.message,
                comment_id=notif.comment_id,
                cve_id=notif.cve_id,
                actor=actor_info,
                is_read=notif.is_read,
                read_at=notif.read_at,
                created_at=notif.created_at,
            )
        )

    return NotificationListResponse(
        notifications=notification_responses,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.post("/notifications/mark-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Mark one or more notifications as read.
    Only the notification owner can mark them as read.
    """
    if not request.notification_ids:
        return

    # Update notifications
    updated = (
        db.query(Notification)
        .filter(
            Notification.id.in_(request.notification_ids),
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .update(
            {
                "is_read": True,
                "read_at": datetime.now(timezone.utc),
            },
            synchronize_session=False,
        )
    )

    db.commit()

    logger.info(
        f"User {current_user.username} marked {updated} notification(s) as read"
    )

    return None


@router.post("/notifications/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Mark all notifications as read for the current user.
    """
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .update(
            {
                "is_read": True,
                "read_at": datetime.now(timezone.utc),
            },
            synchronize_session=False,
        )
    )

    db.commit()

    logger.info(
        f"User {current_user.username} marked all {updated} notification(s) as read"
    )

    return None


@router.delete(
    "/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a notification.
    Only the notification owner can delete it.
    """
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    db.delete(notification)
    db.commit()

    logger.info(f"User {current_user.username} deleted notification {notification_id}")

    return None


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get the count of unread notifications for the current user.
    Useful for badge display.
    """
    count = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .scalar()
        or 0
    )

    return {"unread_count": count}
