# CVE Comments Feature

## Overview

The CVE Comments feature allows authenticated users to comment on vulnerabilities, reply to other comments, and vote on comments (upvote/downvote). The system is designed with **strict XSS protection** and only allows **plain text** comments.

## Features

### ✅ Core Functionality
- **Create Comments**: Post comments on CVEs
- **Nested Comments**: Reply to comments (up to 3 levels deep)
- **Edit Comments**: Edit your own comments
- **Delete Comments**: Delete your own comments (soft delete)
- **Voting System**: Upvote or downvote comments
- **Sorting**: Sort by newest or most upvoted
- **Pagination**: Handle large comment threads efficiently

### 🔒 Security Features
- **XSS Protection**: All HTML tags and scripts are stripped
- **Input Sanitization**: Content is sanitized on both frontend and backend
- **Authentication Required**: Only logged-in users can comment/vote
- **Authorization**: Users can only edit/delete their own comments (admins can delete any)
- **Rate Limiting**: Built-in rate limiting via Redis middleware
- **Plain Text Only**: No HTML, no images, no scripts - just text

### 🎨 UI/UX Features
- **Clean Design**: Modern, minimalist interface
- **Real-time Updates**: Comments update without page refresh
- **Character Counter**: Shows remaining characters (5000 max)
- **Loading States**: Clear feedback during operations
- **Error Handling**: User-friendly error messages
- **Responsive**: Works on mobile and desktop

## Architecture

### Database Models

**Comment Model** (`backend/models.py`):
```python
class Comment(Base):
    id: int
    content: str  # Plain text only
    cve_id: str
    user_id: int
    parent_id: int | None  # For nested comments
    created_at: datetime
    updated_at: datetime
    is_edited: bool
    is_deleted: bool  # Soft delete
    upvotes: int
    downvotes: int
```

**CommentVote Model** (`backend/models.py`):
```python
class CommentVote(Base):
    id: int
    comment_id: int
    user_id: int
    vote_type: int  # 1 for upvote, -1 for downvote
    created_at: datetime
    updated_at: datetime
```

### API Endpoints

All endpoints are in `backend/api/comments.py`:

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/vulnerabilities/{cve_id}/comments` | Create comment | ✅ |
| GET | `/api/v1/vulnerabilities/{cve_id}/comments` | Get comments | ❌ |
| PUT | `/api/v1/comments/{comment_id}` | Update comment | ✅ (author only) |
| DELETE | `/api/v1/comments/{comment_id}` | Delete comment | ✅ (author/admin) |
| POST | `/api/v1/comments/{comment_id}/vote` | Vote on comment | ✅ |
| GET | `/api/v1/comments/{comment_id}/replies` | Get replies | ❌ |

### Frontend Components

Located in `frontend/components/comments/`:

1. **CommentSection.tsx**: Main container component
   - Handles fetching, sorting, pagination
   - Manages comment state
   - Coordinates voting

2. **CommentForm.tsx**: Comment input form
   - Character counter
   - Input validation
   - XSS prevention

3. **CommentList.tsx**: List of comments
   - Simple wrapper component

4. **CommentItem.tsx**: Individual comment display
   - Voting buttons
   - Reply functionality
   - Edit/delete actions
   - Nested replies

## Security Implementation

### Backend XSS Protection

The `CommentCreate` and `CommentUpdate` schemas include a `sanitize_content` validator:

```python
@field_validator('content')
@classmethod
def sanitize_content(cls, v: str) -> str:
    # Remove HTML tags
    v = re.sub(r'<[^>]+>', '', v)
    
    # Remove script tags
    v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove style tags
    v = re.sub(r'<style[^>]*>.*?</style>', '', v, flags=re.IGNORECASE | re.DOTALL)
    
    # Escape HTML entities
    v = html.escape(v)
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'javascript:',
        r'on\w+\s*=',  # onclick, onload, etc.
        r'data:text/html',
    ]
    for pattern in dangerous_patterns:
        v = re.sub(pattern, '', v, flags=re.IGNORECASE)
    
    return v.strip()
```

### Frontend Protection

- **Input Validation**: Max 5000 characters
- **Whitespace Trimming**: Empty comments rejected
- **Display**: Uses `whitespace-pre-wrap` and `break-words` for safe rendering
- **No innerHTML**: All content rendered as text

## Usage

### Setup

1. **Run Database Migration**:
```bash
alembic upgrade head
```

2. **Restart Backend**:
```bash
python -m uvicorn backend.main:app --reload --port 8001
```

3. **Add Comment Section to CVE Page**:
```tsx
import { CommentSection } from "@/components/comments/CommentSection";

// In your CVE detail page:
<CommentSection cveId={cveId} />
```

### Testing

1. **Create a Comment**:
   - Sign in
   - Navigate to a CVE page
   - Enter text in comment form
   - Click "Post Comment"

2. **Test XSS Protection**:
   Try posting:
   ```
   <script>alert('XSS')</script>
   <img src=x onerror=alert('XSS')>
   javascript:alert('XSS')
   ```
   All should be sanitized and displayed as plain text.

3. **Test Voting**:
   - Click upvote/downvote buttons
   - Vote count should update
   - Click same button again to remove vote
   - Click opposite button to change vote

4. **Test Replies**:
   - Click "Reply" on a comment
   - Enter reply text
   - Reply should appear nested under parent

5. **Test Edit/Delete**:
   - Click menu (three dots) on your comment
   - Edit: Change text and save
   - Delete: Confirm deletion

## Rate Limiting

Comments are protected by the existing Redis rate limiting middleware:

- **General Rate Limit**: 100 requests/minute per IP
- **API Rate Limit**: 60 requests/minute per IP

To adjust for comments specifically, add to `nginx/nginx.conf`:

```nginx
location /api/v1/vulnerabilities/*/comments {
    limit_req zone=api burst=20 nodelay;
    # ... rest of config
}
```

## Performance Considerations

### Database Indexes

The migration creates these indexes for performance:
- `idx_comments_cve_created`: Fast lookup by CVE + sort by date
- `idx_comments_user_created`: Fast lookup by user + sort by date
- `idx_comments_parent`: Fast nested comment queries
- `idx_comment_votes_unique`: Ensures one vote per user per comment

### Denormalized Vote Counts

Vote counts (`upvotes`, `downvotes`) are stored directly on comments for fast retrieval, avoiding expensive JOIN queries.

### Pagination

Comments are paginated (20 per page by default) to avoid loading thousands of comments at once.

## Future Enhancements

Potential improvements:

1. **Markdown Support**: Allow basic markdown (bold, italic, links) with strict sanitization
2. **Mentions**: @username mentions with notifications
3. **Moderation**: Flag/report inappropriate comments
4. **Sorting Options**: Add "controversial" (high vote activity)
5. **Real-time Updates**: WebSocket for live comment updates
6. **Search**: Search within comments
7. **Notifications**: Email/in-app notifications for replies
8. **Rich Embeds**: Safe embedding of CVE references

## Troubleshooting

### Comments Not Showing

1. Check if migration ran: `alembic current`
2. Check backend logs for errors
3. Verify user is authenticated
4. Check browser console for API errors

### XSS Test Failing

If HTML is rendering:
1. Verify backend sanitization is active
2. Check frontend is using `whitespace-pre-wrap` not `innerHTML`
3. Ensure latest code is deployed

### Voting Not Working

1. Verify user is authenticated
2. Check Redis is running: `docker ps | grep redis`
3. Check backend logs for vote endpoint errors

### Performance Issues

1. Check database indexes: `\d comments` in psql
2. Monitor query performance
3. Consider increasing pagination size
4. Add caching for frequently accessed comments

## API Examples

### Create Comment
```bash
curl -X POST "http://localhost:8001/api/v1/vulnerabilities/CVE-2024-1234/comments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "This is a test comment"}'
```

### Get Comments
```bash
curl "http://localhost:8001/api/v1/vulnerabilities/CVE-2024-1234/comments?page=1&page_size=20&sort_by=created_at&order=desc"
```

### Vote on Comment
```bash
curl -X POST "http://localhost:8001/api/v1/comments/1/vote" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": 1}'
```

### Update Comment
```bash
curl -X PUT "http://localhost:8001/api/v1/comments/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated comment text"}'
```

### Delete Comment
```bash
curl -X DELETE "http://localhost:8001/api/v1/comments/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Security Checklist

Before deploying to production:

- [ ] XSS protection tested with various payloads
- [ ] Rate limiting configured appropriately
- [ ] Authentication required for all write operations
- [ ] Authorization checks in place (users can only edit own comments)
- [ ] Input validation on both frontend and backend
- [ ] SQL injection protection (using SQLAlchemy ORM)
- [ ] CSRF protection enabled (existing middleware)
- [ ] Content length limits enforced (5000 chars)
- [ ] Soft delete implemented (no data loss)
- [ ] Database indexes created for performance
- [ ] Error messages don't leak sensitive information
- [ ] Logging in place for security events

## Maintenance

### Database Cleanup

To hard-delete soft-deleted comments older than 90 days:

```sql
DELETE FROM comments 
WHERE is_deleted = true 
AND updated_at < NOW() - INTERVAL '90 days';
```

### Monitoring

Monitor these metrics:
- Comment creation rate
- Vote activity
- Failed authentication attempts on comment endpoints
- XSS attempt patterns in logs
- Database query performance

## Support

For issues or questions:
- Check logs: `docker logs openthreat-backend`
- Review API docs: http://localhost:8001/docs
- Check database: `docker exec -it openthreat-db psql -U openthreat`
- Contact: hoodinformatik@gmail.com
