# 🚀 Quick Start Guide

## ⚡ Quick Start (5 Minutes)

### 1. Start Infrastructure

```bash
docker-compose up -d
```

Wait until PostgreSQL and Redis are running (approx. 30 seconds).

### 2. Create Database Tables

**Windows:**
```bash
.\setup_database.bat
```

**Manually:**
```bash
# Make sure PostgreSQL is running
docker ps | findstr openthreat-db

# Run migrations
alembic upgrade head
```

**Verify:**
```bash
# Connect to database
docker exec -it openthreat-db psql -U openthreat -d openthreat

# List tables
\dt

# Exit
\q
```

### 3. Start Backend

**Windows:**
```bash
.\start_backend.bat
```

**Manually:**
```bash
# IMPORTANT: From the project root directory!
python -m uvicorn backend.main:app --reload --port 8001
```

**Verify:**
```bash
curl http://127.0.0.1:8001/health
```

### 4. Start Frontend (new terminal)

**Windows:**
```bash
.\start_frontend.bat
```

**Manually:**
```bash
cd frontend
npm install  # Only on first run
npm run dev
```

### 5. Test

- 🌐 **Frontend:** http://localhost:3000
- 📚 **API Docs:** http://localhost:8001/docs
- 🔍 **Health Check:** http://127.0.0.1:8001/health

## ❌ Common Errors

### "ImportError: attempted relative import with no known parent package"

**Problem:** Backend is started from the wrong directory.

**Solution:**
```bash
# ❌ WRONG
cd backend
uvicorn main:app --reload

# ✅ CORRECT
cd C:\Users\hoodi\Desktop\OpenThreat
python -m uvicorn backend.main:app --reload --port 8001
```

### "Connection refused" or "Cannot connect to backend"

**Problem:** Backend is not running or on wrong port.

**Solution:**
1. Check if backend is running:
   ```bash
   curl http://127.0.0.1:8001/health
   ```

2. Check if port 8001 is free:
   ```bash
   netstat -ano | findstr :8001
   ```

3. Restart backend with correct port

### "relation 'users' does not exist" or "Table not found"

**Problem:** Database tables were not created.

**Solution:**
```bash
# Run migrations
.\setup_database.bat

# Or manually
alembic upgrade head

# Check if tables exist
docker exec -it openthreat-db psql -U openthreat -d openthreat -c "\dt"
```

### "Database connection failed"

**Problem:** PostgreSQL is not running.

**Solution:**
```bash
# Check Docker containers
docker ps

# Start PostgreSQL
docker-compose up -d postgres

# Check logs
docker logs openthreat-db
```

### Frontend shows "API Error"

**Problem:** API routing is not working.

**Solution:**
1. Make sure backend is running on port 8001
2. Check `frontend/next.config.js` (should contain rewrites)
3. Restart frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## 📦 Populate Database (Optional)

After first start, the database is empty. To load data:

### Option 1: API (Recommended)

1. Open http://localhost:8001/docs
2. Navigate to `/api/v1/data-sources/nvd/fetch-recent`
3. Set `days=30`
4. Click "Execute"
5. Wait 5-30 minutes

### Option 2: Script

```bash
# Last 30 days (fast)
python scripts/fetch_nvd_complete.py --recent --days 30

# CISA KEV (exploited vulnerabilities)
python scripts/fetch_cisa_kev.py

# BSI CERT (German descriptions)
python scripts/fetch_bsi_cert.py
```

## 🎯 Next Steps

1. ✅ Backend running on http://127.0.0.1:8001
2. ✅ Frontend running on http://localhost:3000
3. ✅ Test registration: http://localhost:3000/auth
4. 📊 Load data (see above)
5. 🔍 Browse vulnerabilities

## 📚 Further Documentation

- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) - Detailed Development Guide
- [nginx/README.md](nginx/README.md) - Nginx Configuration
- [README.md](README.md) - Complete Documentation

## 🆘 Need Help?

1. Check [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for troubleshooting
2. Open an issue on GitHub
3. Contact: hoodinformatik@gmail.com
