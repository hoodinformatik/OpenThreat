# Notifications & @Mentions Feature

## Overview

This feature adds user notifications and @username mentions to OpenThreat, enabling better community engagement and interaction.

## Features

### 1. @Username Mentions
- **Syntax**: Use `@username` in comments to mention users
- **Detection**: Automatic extraction of mentions from comment text
- **Notifications**: Mentioned users receive instant notifications
- **Validation**: Only existing usernames trigger notifications

### 2. Reply Notifications
- Users are notified when someone replies to their comment
- Prevents self-notifications (replying to your own comment)
- Links directly to the reply

### 3. Vote Milestones
- Notifications for upvote milestones: 5, 10, 25, 50, 100, 250, 500, 1000
- Only positive milestones (upvotes, not downvotes)
- Prevents spam by only notifying on specific thresholds

### 4. Notification Center
- Bell icon in navigation with unread count badge
- Dropdown panel with recent notifications
- Mark as read (individual or all)
- Delete notifications
- Auto-refresh every 30 seconds
- Direct links to related CVEs/comments

## Database Schema

### Notifications Table
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR(50) NOT NULL,  -- 'mention', 'reply', 'vote_milestone'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    comment_id INTEGER REFERENCES comments(id),
    cve_id VARCHAR(50) REFERENCES vulnerabilities(cve_id),
    actor_id INTEGER REFERENCES users(id),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

## API Endpoints

### Get Notifications
```
GET /api/v1/notifications
Query params:
  - page (default: 1)
  - page_size (default: 20, max: 100)
  - unread_only (default: false)
  - notification_type (optional: 'mention', 'reply', 'vote_milestone')
```

### Mark as Read
```
POST /api/v1/notifications/mark-read
Body: { "notification_ids": [1, 2, 3] }
```

### Mark All as Read
```
POST /api/v1/notifications/mark-all-read
```

### Delete Notification
```
DELETE /api/v1/notifications/{notification_id}
```

### Get Unread Count
```
GET /api/v1/notifications/unread-count
Response: { "unread_count": 5 }
```

## Frontend Components

### NotificationCenter
- Location: `frontend/components/NotificationCenter.tsx`
- Features:
  - Bell icon with badge
  - Dropdown panel
  - Real-time updates (30s polling)
  - Mark as read/delete actions
  - Direct navigation to CVEs

### Integration
Added to `Navigation` component in the header, visible to all authenticated users.

## Usage Examples

### Mentioning Users in Comments
```
Hey @john, have you seen this CVE? It affects the same product as CVE-2024-12345.

@jane and @admin, we should prioritize this one.
```

### Notification Types

**Mention Notification:**
```
Title: "john mentioned you"
Message: "@john mentioned you in a comment on CVE-2024-12345"
Type: "mention"
```

**Reply Notification:**
```
Title: "jane replied to your comment"
Message: "@jane replied to your comment on CVE-2024-12345"
Type: "reply"
```

**Vote Milestone:**
```
Title: "Your comment reached 10 upvotes!"
Message: "Your comment on CVE-2024-12345 has reached 10 upvotes"
Type: "vote_milestone"
```

## Implementation Details

### Backend
- **Models**: `Notification` model in `backend/models.py`
- **API**: `backend/api/notifications.py`
- **Utils**: `backend/utils/notifications.py`
  - `extract_mentions()`: Regex-based mention extraction
  - `create_mention_notifications()`: Create notifications for mentions
  - `create_reply_notification()`: Create notification for replies
  - `create_vote_notification()`: Create milestone notifications

### Frontend
- **Types**: `frontend/types/notification.ts`
- **Component**: `frontend/components/NotificationCenter.tsx`
- **Integration**: Added to `frontend/components/navigation.tsx`

### Mention Detection
- Pattern: `@(\w+)` (alphanumeric + underscore)
- Case-sensitive username matching
- Duplicate mentions are deduplicated
- Invalid usernames are silently ignored

## Migration

Run the migration to create the notifications table:

```bash
# Automatic (on backend restart)
docker restart openthreat-backend-1 openthreat-backend-2

# Or manual
cat backend/migrations/add_notifications.sql | docker compose exec -T postgres psql -U openthreat -d openthreat
```

## Testing

### Test @Mentions
1. Create a comment with `@username`
2. Check that the mentioned user receives a notification
3. Verify the notification links to the correct comment

### Test Replies
1. Reply to someone's comment
2. Check that the original author receives a notification
3. Verify no notification when replying to your own comment

### Test Vote Milestones
1. Upvote a comment to reach a milestone (5, 10, 25, etc.)
2. Check that the comment author receives a notification
3. Verify no duplicate notifications for the same milestone

### Test Notification Center
1. Check bell icon shows unread count
2. Open dropdown and verify notifications display
3. Test mark as read (individual and all)
4. Test delete notification
5. Test navigation to CVE/comment

## Future Enhancements

- [ ] Email notifications (optional, user preference)
- [ ] WebSocket for real-time updates (instead of polling)
- [ ] Notification preferences (mute certain types)
- [ ] Notification history page
- [ ] Group notifications ("@john and 2 others mentioned you")
- [ ] Push notifications (PWA)
- [ ] Digest emails (daily/weekly summary)

## Performance Considerations

- Indexes on `user_id`, `is_read`, `created_at` for fast queries
- Polling interval: 30 seconds (configurable)
- Pagination: 20 notifications per page
- Auto-cleanup: Consider archiving old notifications after 30 days

## Security

- Users can only see their own notifications
- Users can only mark their own notifications as read
- Users can only delete their own notifications
- Mention extraction is XSS-safe (no HTML execution)
- All API endpoints require authentication
