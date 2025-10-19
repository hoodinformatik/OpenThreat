# 🔧 Development Setup Guide

## Problem

The frontend uses relative API paths (e.g., `/api/v1/auth/register`) that are routed through nginx in production. This doesn't work locally because frontend and backend run on different ports.

## Solution

### ✅ Next.js Rewrites (Recommended)

The `next.config.js` has been configured to automatically forward API requests to the backend:

```javascript
async rewrites() {
  if (process.env.NODE_ENV === 'development') {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8001/api/:path*',
      },
    ];
  }
  return [];
}
```

**Advantages:**
- ✅ Works out-of-the-box
- ✅ No additional configuration needed
- ✅ No CORS issues
- ✅ Production code remains unchanged

**Usage:**

1. Start backend (from project root):
```bash
# Windows
.\start_backend.bat

# Or manually
python -m uvicorn backend.main:app --reload --port 8001
```

2. Start frontend (in new terminal):
```bash
# Windows
.\start_frontend.bat

# Or manually
cd frontend
npm run dev
```

3. Test:
- Frontend: http://localhost:3000
- API calls are automatically forwarded

**IMPORTANT:** The backend must be started from the project root directory, not from the `backend` directory!

### 🐳 Nginx Development Config (Optional)

If you want to replicate the complete production environment locally, there's a `nginx/nginx.dev.conf`:

**Differences from Production:**
- No HTTPS (HTTP only)
- Relaxed rate limits
- No caching
- `host.docker.internal` instead of container names

**Usage:**

```bash
# Start Nginx container
docker run -d \
  --name openthreat-nginx \
  -p 80:80 \
  -v $(pwd)/nginx/nginx.dev.conf:/etc/nginx/nginx.conf:ro \
  --add-host host.docker.internal:host-gateway \
  nginx:alpine

# Start backend and frontend normally
cd backend && uvicorn main:app --reload --port 8001 &
cd frontend && npm run dev &

# Access via nginx
open http://localhost
```

## Comparison: Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| **Routing** | Next.js Rewrites | Nginx Reverse Proxy |
| **HTTPS** | ❌ No | ✅ Yes |
| **Rate Limits** | ❌ None | ✅ Strict |
| **Caching** | ❌ No | ✅ Yes |
| **Security Headers** | ⚠️ Minimal | ✅ Full |
| **Frontend Port** | 3000 | 3000 (internal) |
| **Backend Port** | 8001 | 8001 (internal) |
| **Access** | localhost:3000 | Domain (Port 443) |

## Important Files

- **`frontend/next.config.js`** - Next.js Rewrites for Development
- **`nginx/nginx.conf`** - Production Nginx Config (with HTTPS)
- **`nginx/nginx.dev.conf`** - Development Nginx Config (without HTTPS)
- **`nginx/README.md`** - Detailed Nginx Documentation

## Troubleshooting

### Problem: "ImportError: attempted relative import with no known parent package"

**Cause:** Backend is started from the wrong directory.

**Solution:**
```bash
# ❌ WRONG (from backend directory)
cd backend
uvicorn main:app --reload

# ✅ CORRECT (from project root)
cd C:\Users\hoodi\Desktop\OpenThreat
python -m uvicorn backend.main:app --reload --port 8001

# Or use the batch script
.\start_backend.bat
```

### Problem: API calls don't work

**Solution:**
1. Make sure the backend is running:
```bash
curl http://127.0.0.1:8001/health
```

2. Check the browser console for errors

3. Restart the Next.js dev server:
```bash
cd frontend
npm run dev
```

### Problem: "Cannot connect to backend"

**Solution:**
1. Check if the backend port is correct (8001)
2. Make sure no firewall is blocking access
3. Check `next.config.js` for the correct port

### Problem: Changes to next.config.js are not applied

**Solution:**
Next.js must be restarted after changes to `next.config.js`:
```bash
# Ctrl+C to stop
npm run dev
```

## Best Practices

### ✅ DO

- Use Next.js Rewrites for local development
- Test regularly with the production nginx config
- Keep `nginx.conf` and `nginx.dev.conf` in sync (except HTTPS/Rate Limits)
- Document changes to routing logic

### ❌ DON'T

- Don't hardcode absolute URLs in frontend code
- Don't use `NEXT_PUBLIC_API_URL` for API calls (use relative paths)
- Don't push local nginx configs to production
- Don't disable security features in production

## Deployment

When deploying to production:

1. ✅ `next.config.js` contains the rewrites (only active in development)
2. ✅ `nginx.conf` is used (with HTTPS and security)
3. ✅ Frontend code uses relative paths
4. ✅ No code changes needed

**The changes are production-safe!** 🎉

The rewrites in `next.config.js` are only active in development:
```javascript
if (process.env.NODE_ENV === 'development') {
  // Rewrites only in development
}
```

In production, nginx handles the routing.
