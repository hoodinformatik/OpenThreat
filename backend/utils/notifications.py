"""
Utility functions for creating and managing notifications.
"""

import logging
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Comment, Notification, User

logger = logging.getLogger(__name__)


def extract_mentions(text: str) -> List[str]:
    """
    Extract @username mentions from text.
    Returns list of unique usernames (without the @ symbol).

    Examples:
        "@john hello @jane" -> ["john", "jane"]
        "Hey @user123 and @user_name" -> ["user123", "user_name"]
    """
    # Match @username pattern (alphanumeric and underscore)
    pattern = r"@(\w+)"
    mentions = re.findall(pattern, text)

    # Return unique mentions
    return list(set(mentions))


def create_mention_notifications(
    db: Session,
    comment: Comment,
    actor: User,
    mentioned_usernames: List[str],
) -> int:
    """
    Create notifications for users mentioned in a comment.

    Args:
        db: Database session
        comment: The comment containing mentions
        actor: User who created the comment
        mentioned_usernames: List of usernames that were mentioned

    Returns:
        Number of notifications created
    """
    if not mentioned_usernames:
        return 0

    # Find users by username
    mentioned_users = (
        db.query(User).filter(User.username.in_(mentioned_usernames)).all()
    )

    notifications_created = 0

    for user in mentioned_users:
        # Don't notify if user mentions themselves
        if user.id == actor.id:
            continue

        # Check if notification already exists (avoid duplicates)
        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.comment_id == comment.id,
                Notification.type == "mention",
            )
            .first()
        )

        if existing:
            continue

        # Create notification
        notification = Notification(
            user_id=user.id,
            type="mention",
            title=f"{actor.username} mentioned you",
            message=f"@{actor.username} mentioned you in a comment on {comment.cve_id}",
            comment_id=comment.id,
            cve_id=comment.cve_id,
            actor_id=actor.id,
        )

        db.add(notification)
        notifications_created += 1

    if notifications_created > 0:
        db.commit()
        logger.info(
            f"Created {notifications_created} mention notification(s) for comment {comment.id}"
        )

    return notifications_created


def create_reply_notification(
    db: Session,
    comment: Comment,
    actor: User,
    parent_comment: Comment,
) -> bool:
    """
    Create notification when someone replies to a comment.

    Args:
        db: Database session
        comment: The reply comment
        actor: User who created the reply
        parent_comment: The comment being replied to

    Returns:
        True if notification was created, False otherwise
    """
    # Don't notify if user replies to their own comment
    if parent_comment.user_id == actor.id:
        return False

    # Check if notification already exists
    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == parent_comment.user_id,
            Notification.comment_id == comment.id,
            Notification.type == "reply",
        )
        .first()
    )

    if existing:
        return False

    # Create notification
    notification = Notification(
        user_id=parent_comment.user_id,
        type="reply",
        title=f"{actor.username} replied to your comment",
        message=f"@{actor.username} replied to your comment on {comment.cve_id}",
        comment_id=comment.id,
        cve_id=comment.cve_id,
        actor_id=actor.id,
    )

    db.add(notification)
    db.commit()

    logger.info(
        f"Created reply notification for user {parent_comment.user_id} on comment {comment.id}"
    )

    return True


def create_vote_notification(
    db: Session,
    comment: Comment,
    actor: User,
    vote_type: int,
) -> bool:
    """
    Create notification when someone upvotes a comment.
    Only notify on upvotes (not downvotes) to keep it positive.

    Args:
        db: Database session
        comment: The comment that was voted on
        actor: User who voted
        vote_type: 1 for upvote, -1 for downvote

    Returns:
        True if notification was created, False otherwise
    """
    # Only notify on upvotes
    if vote_type != 1:
        return False

    # Don't notify if user votes on their own comment
    if comment.user_id == actor.id:
        return False

    # Don't create notification for every vote (would be spammy)
    # Only notify on milestone upvotes: 5, 10, 25, 50, 100, etc.
    milestones = [5, 10, 25, 50, 100, 250, 500, 1000]
    if comment.upvotes not in milestones:
        return False

    # Check if notification already exists for this milestone
    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == comment.user_id,
            Notification.comment_id == comment.id,
            Notification.type == "vote_milestone",
            Notification.message.contains(f"{comment.upvotes} upvotes"),
        )
        .first()
    )

    if existing:
        return False

    # Create notification
    notification = Notification(
        user_id=comment.user_id,
        type="vote_milestone",
        title=f"Your comment reached {comment.upvotes} upvotes!",
        message=f"Your comment on {comment.cve_id} has reached {comment.upvotes} upvotes",
        comment_id=comment.id,
        cve_id=comment.cve_id,
        actor_id=None,  # No specific actor for milestones
    )

    db.add(notification)
    db.commit()

    logger.info(
        f"Created vote milestone notification for user {comment.user_id} on comment {comment.id}"
    )

    return True
