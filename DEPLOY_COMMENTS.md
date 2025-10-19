# Deployment Guide: Comments Feature

## 🚀 Production Deployment Checklist

### 1. Backend Deployment

#### A. Update Code on Server
```bash
# SSH into your production server
ssh user@your-server.com

# Navigate to project directory
cd /path/to/OpenThreat

# Pull latest changes
git pull origin main

# Or if you're using a specific branch:
git pull origin feature/comments
```

#### B. Run Database Migration
```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run Alembic migration
cd backend
alembic upgrade head

# You should see:
# INFO  [alembic.runtime.migration] Running upgrade 006_add_email_verification -> 007_add_comments_tables
```

#### C. Restart Backend Service
```bash
# If using systemd:
sudo systemctl restart openthreat-backend

# If using Docker:
docker-compose restart backend

# If using PM2:
pm2 restart openthreat-backend

# Verify backend is running:
curl http://localhost:8001/health
# Should return: {"status":"healthy"}
```

### 2. Nginx Configuration

#### A. Update Nginx Config
```bash
# Copy new nginx.conf to server
scp nginx/nginx.conf user@your-server.com:/etc/nginx/nginx.conf

# Or if already on server, copy from repo:
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
```

#### B. Test Nginx Configuration
```bash
# Test configuration syntax
sudo nginx -t

# Should output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

#### C. Reload Nginx
```bash
# Reload without downtime
sudo nginx -s reload

# Or restart if needed:
sudo systemctl restart nginx
```

### 3. Frontend Deployment

#### A. Build Frontend
```bash
cd frontend

# Install dependencies (if new)
npm install

# Build for production
npm run build

# Start production server
npm start

# Or if using PM2:
pm2 restart openthreat-frontend
```

#### B. Verify Frontend
```bash
# Check if frontend is running
curl http://localhost:3000

# Should return HTML
```

### 4. Verification

#### A. Test Comment Endpoints
```bash
# Test GET comments (should work without auth)
curl https://your-domain.com/api/v1/vulnerabilities/CVE-2024-1234/comments

# Should return:
# {"comments":[],"total":0,"page":1,"page_size":20}

# Test POST comment (requires auth token)
curl -X POST https://your-domain.com/api/v1/vulnerabilities/CVE-2024-1234/comments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test comment"}'

# Should return the created comment
```

#### B. Check Nginx Logs
```bash
# Watch access logs
sudo tail -f /var/log/nginx/access.log | grep comments

# Watch error logs
sudo tail -f /var/log/nginx/error.log
```

#### C. Check Backend Logs
```bash
# If using systemd:
sudo journalctl -u openthreat-backend -f

# If using Docker:
docker logs -f openthreat-backend

# If using PM2:
pm2 logs openthreat-backend
```

### 5. Browser Testing

1. **Open your production site**: https://your-domain.com
2. **Navigate to a CVE page**
3. **Scroll to bottom** - You should see "Comments (0)"
4. **Sign in** to your account
5. **Write a test comment**
6. **Test voting** (upvote/downvote)
7. **Test reply** functionality
8. **Test edit/delete** your own comments

---

## 🔧 Troubleshooting

### Issue: 500 Internal Server Error

**Check Backend Logs:**
```bash
# Look for Python errors
sudo journalctl -u openthreat-backend -n 50
```

**Common causes:**
- Database migration not run
- Missing dependencies
- Auth function errors

**Solution:**
```bash
# Re-run migration
alembic upgrade head

# Restart backend
sudo systemctl restart openthreat-backend
```

### Issue: 404 Not Found on Comment Endpoints

**Check Nginx Config:**
```bash
# Verify comment location block exists
sudo nginx -T | grep -A 10 "comments"
```

**Solution:**
```bash
# Update nginx.conf
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo nginx -s reload
```

### Issue: Comments Not Loading (Cached)

**Clear Nginx Cache:**
```bash
# Clear cache directory
sudo rm -rf /var/cache/nginx/*

# Reload nginx
sudo nginx -s reload
```

**Verify No-Cache Headers:**
```bash
# Check response headers
curl -I https://your-domain.com/api/v1/vulnerabilities/CVE-2024-1234/comments

# Should include:
# Cache-Control: no-store, no-cache, must-revalidate
```

### Issue: CORS Errors

**Check Nginx Headers:**
```bash
# Verify CORS headers in nginx.conf
sudo nginx -T | grep -i cors
```

**Add if missing:**
```nginx
add_header Access-Control-Allow-Origin "*" always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
```

### Issue: Rate Limiting (429 Too Many Requests)

**Check Rate Limit:**
```bash
# View current rate limit for comments
sudo nginx -T | grep -A 5 "location.*comments"
```

**Increase if needed:**
```nginx
# In nginx.conf, increase burst:
limit_req zone=api burst=50 nodelay;  # Increase from 30 to 50
```

---

## 📊 Monitoring

### Key Metrics to Monitor

1. **Comment Creation Rate**
   ```bash
   # Count comments in last hour
   curl -s https://your-domain.com/api/v1/vulnerabilities/CVE-*/comments | jq '.total'
   ```

2. **Response Times**
   ```bash
   # Check nginx access logs for response times
   sudo tail -f /var/log/nginx/access.log | grep comments | awk '{print $NF}'
   ```

3. **Error Rate**
   ```bash
   # Count 5xx errors
   sudo grep "comments" /var/log/nginx/access.log | grep " 5[0-9][0-9] " | wc -l
   ```

4. **Database Performance**
   ```sql
   -- Check comment query performance
   SELECT 
       query, 
       calls, 
       mean_exec_time, 
       max_exec_time 
   FROM pg_stat_statements 
   WHERE query LIKE '%comments%' 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;
   ```

---

## 🔐 Security Checklist

- [ ] XSS protection tested with malicious payloads
- [ ] Rate limiting configured (30 requests/burst for comments)
- [ ] Authentication required for POST/PUT/DELETE
- [ ] Authorization checks (users can only edit own comments)
- [ ] Input validation (max 5000 characters)
- [ ] SQL injection protection (using ORM)
- [ ] HTTPS enabled
- [ ] CSRF protection active
- [ ] No caching of dynamic comment data
- [ ] Proper error messages (no sensitive data leaked)

---

## 📝 Rollback Plan

If something goes wrong:

### 1. Rollback Database
```bash
# Downgrade migration
alembic downgrade -1

# This will drop comments and comment_votes tables
```

### 2. Rollback Code
```bash
# Revert to previous commit
git revert HEAD
git push

# Or checkout previous version
git checkout <previous-commit-hash>
```

### 3. Rollback Nginx
```bash
# Restore previous config
sudo cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
sudo nginx -s reload
```

### 4. Restart Services
```bash
sudo systemctl restart openthreat-backend
sudo systemctl restart nginx
pm2 restart openthreat-frontend
```

---

## ✅ Post-Deployment Verification

Run these tests after deployment:

```bash
# 1. Health check
curl https://your-domain.com/health

# 2. Get comments (unauthenticated)
curl https://your-domain.com/api/v1/vulnerabilities/CVE-2024-1234/comments

# 3. Create comment (authenticated)
curl -X POST https://your-domain.com/api/v1/vulnerabilities/CVE-2024-1234/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Deployment test"}'

# 4. Vote on comment
curl -X POST https://your-domain.com/api/v1/comments/1/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type":1}'

# 5. Check response headers (no caching)
curl -I https://your-domain.com/api/v1/vulnerabilities/CVE-2024-1234/comments | grep -i cache
```

---

## 📞 Support

If you encounter issues:

1. Check logs (backend, nginx, frontend)
2. Review this troubleshooting guide
3. Check `docs/COMMENTS_FEATURE.md` for technical details
4. Contact: hoodinformatik@gmail.com

---

## 🎉 Success Indicators

You'll know the deployment was successful when:

- ✅ Comment section visible on CVE pages
- ✅ Users can create comments
- ✅ Voting works (upvote/downvote)
- ✅ Replies work (nested comments)
- ✅ Edit/delete works for own comments
- ✅ No 500 errors in logs
- ✅ Response times < 200ms
- ✅ XSS protection working (HTML stripped)
- ✅ Rate limiting active (no abuse)
- ✅ No caching issues (comments update immediately)
