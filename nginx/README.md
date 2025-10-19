# Nginx Configuration

This directory contains two nginx configurations:

## 📁 Files

- **`nginx.conf`** - Production configuration (with HTTPS, strict rate limits)
- **`nginx.dev.conf`** - Development configuration (without HTTPS, relaxed rate limits)

## 🚀 Local Testing

### Option 1: Next.js Rewrites (Recommended for Development)

The easiest method is to use Next.js Rewrites. These are already configured in `frontend/next.config.js`.

**Prerequisites:**
- Backend running on `http://127.0.0.1:8001`
- Frontend running on `http://localhost:3000`

**Start:**
```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8001

# Terminal 2: Start frontend
cd frontend
npm run dev
```

**Test:**
- Frontend: http://localhost:3000
- API calls are automatically forwarded to http://127.0.0.1:8001

### Option 2: Nginx locally with Docker

If you want to replicate the complete production environment locally:

**1. Docker Compose with nginx.dev.conf:**

Create a `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: openthreat-nginx-dev
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.dev.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
    networks:
      - openthreat-network
    extra_hosts:
      - "host.docker.internal:host-gateway"

  backend:
    # ... your backend configuration
    
  frontend:
    # ... your frontend configuration

networks:
  openthreat-network:
    driver: bridge
```

**2. Start:**
```bash
docker-compose -f docker-compose.dev.yml up
```

**3. Test:**
- Everything via nginx: http://localhost

## 🔒 Production Deployment

In production, `nginx.conf` is used, which provides the following features:

- ✅ HTTPS with TLS 1.2/1.3
- ✅ Strict rate limits
- ✅ Security headers (CSP, HSTS, etc.)
- ✅ Caching for API responses
- ✅ Compression (gzip)

**Important:** The `nginx.conf` is optimized for production and should not be used locally because it:
- Expects HTTPS certificates
- Redirects HTTP to HTTPS
- Has stricter rate limits

## 🔄 Differences between dev and prod

| Feature | Development (`nginx.dev.conf`) | Production (`nginx.conf`) |
|---------|-------------------------------|---------------------------|
| HTTPS | ❌ No (HTTP only) | ✅ Yes (with redirect) |
| Rate Limits | 🟢 Relaxed (50-100 req/s) | 🔴 Strict (2-20 req/s) |
| Caching | ❌ Disabled | ✅ Enabled |
| SSL/TLS | ❌ Not configured | ✅ TLS 1.2/1.3 |
| Security Headers | ⚠️ Minimal | ✅ Full (CSP, HSTS) |
| Upstream | `host.docker.internal` | `backend:8001`, `frontend:3000` |

## 📝 Customizations

### Change Backend Port

If your backend runs on a different port:

**In `next.config.js`:**
```javascript
destination: 'http://127.0.0.1:YOUR_PORT/api/:path*',
```

**In `nginx.dev.conf`:**
```nginx
upstream backend {
    server host.docker.internal:YOUR_PORT;
}
```

### Change Frontend Port

**In `nginx.dev.conf`:**
```nginx
upstream frontend {
    server host.docker.internal:YOUR_PORT;
}
```

## 🐛 Troubleshooting

### Problem: "502 Bad Gateway" in nginx

**Solution:** Make sure backend and frontend are running:
```bash
# Test backend
curl http://127.0.0.1:8001/health

# Test frontend
curl http://localhost:3000
```

### Problem: API calls don't work locally

**Solution 1:** Make sure the Next.js dev server was restarted after changes to `next.config.js`:
```bash
cd frontend
npm run dev
```

**Solution 2:** Check the browser console for CORS errors. Next.js Rewrites should avoid CORS issues.

### Problem: "host.docker.internal" not reachable

**Solution:** On Linux, you must add `extra_hosts` to docker-compose:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

## 📚 Further Information

- [Next.js Rewrites Documentation](https://nextjs.org/docs/api-reference/next.config.js/rewrites)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
