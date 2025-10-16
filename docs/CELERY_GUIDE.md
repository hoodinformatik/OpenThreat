# Celery Background Processing Guide

## Overview

OpenThreat uses Celery for background task processing, including:
- Automatic LLM processing of CVEs
- Scheduled data updates
- Cache management
- Statistics updates

---

## Quick Start

### 1. Start Celery (Easy Way)

```bash
# Run the start script
.\start_celery.bat
```

This will:
- ✅ Check if Redis is running
- ✅ Check if Ollama is available
- ✅ Start Celery Worker (processes tasks)
- ✅ Start Celery Beat (schedules tasks)

### 2. Start Celery (Manual Way)

**Terminal 1 - Worker:**
```bash
celery -A backend.celery_app worker --loglevel=info --pool=solo
```

**Terminal 2 - Beat:**
```bash
celery -A backend.celery_app beat --loglevel=info
```

---

## What is Celery?

### Celery Worker
- **Purpose:** Executes background tasks
- **What it does:** Processes LLM requests, data updates, etc.
- **Required:** Yes (without it, no tasks run)

### Celery Beat
- **Purpose:** Schedules periodic tasks
- **What it does:** Triggers tasks at specific times
- **Required:** Optional (only needed for automatic scheduling)

### Redis
- **Purpose:** Message broker and result backend
- **What it does:** Queues tasks and stores results
- **Required:** Yes (Celery needs it)

---

## Scheduled Tasks

### LLM Processing

| Task | Schedule | Description |
|------|----------|-------------|
| **process-new-cves** | Every 5 minutes | Process newly added CVEs |
| **process-high-priority** | Every 10 minutes | Exploited, CRITICAL, Recent (< 7 days) |
| **process-medium-priority** | Every 30 minutes | HIGH severity, Recent (< 30 days) |
| **process-low-priority** | Every 2 hours | All other unprocessed CVEs |

### Data Updates

| Task | Schedule | Description |
|------|----------|-------------|
| **update-vulnerabilities** | Every 2 hours | Fetch new CVEs from NVD |
| **update-stats-cache** | Every 15 minutes | Refresh statistics cache |
| **clean-cache** | Daily at 3 AM | Remove old cache entries |

---

## Manual Task Execution

### Via CLI

```bash
# Get LLM processing statistics
python scripts/start_llm_processing.py --stats

# Process high priority CVEs (batch of 50)
python scripts/start_llm_processing.py --batch-size 50 --priority high

# Process all priorities
python scripts/start_llm_processing.py --batch-size 100 --priority all

# Process single CVE
python scripts/start_llm_processing.py --cve CVE-2024-1234
```

### Via API

```bash
# Get statistics
curl http://localhost:8001/api/v1/llm/stats

# Process single CVE
curl -X POST http://localhost:8001/api/v1/llm/process/CVE-2024-1234

# Process batch
curl -X POST "http://localhost:8001/api/v1/llm/process/batch?batch_size=50&priority=high"

# Check task status
curl http://localhost:8001/api/v1/llm/task/{task_id}
```

### Via Swagger UI

1. Open: http://localhost:8001/docs
2. Navigate to: **LLM Processing** section
3. Try out endpoints interactively

---

## Monitoring

### Check Worker Status

```bash
# List active workers
celery -A backend.celery_app inspect active

# Check registered tasks
celery -A backend.celery_app inspect registered

# Check scheduled tasks
celery -A backend.celery_app inspect scheduled
```

### View Task Queue

```bash
# Show queued tasks
celery -A backend.celery_app inspect reserved
```

### Monitor in Real-Time

**Option 1: Flower (Web UI)**
```bash
# Install Flower
pip install flower

# Start Flower
celery -A backend.celery_app flower

# Open: http://localhost:5555
```

**Option 2: Celery Events**
```bash
celery -A backend.celery_app events
```

---

## Troubleshooting

### Worker Not Starting

**Error:** `Cannot connect to Redis`

**Solution:**
```bash
# Check if Redis is running
docker ps | findstr redis

# Start Redis
docker-compose up -d redis
```

---

### Tasks Not Processing

**Problem:** Tasks are queued but not executing

**Solutions:**

1. **Check if Worker is running:**
   ```bash
   celery -A backend.celery_app inspect active
   ```

2. **Restart Worker:**
   - Close Worker window
   - Run `.\start_celery.bat` again

3. **Check logs:**
   - Look at Worker window for errors
   - Check Redis connection

---

### LLM Processing Fails

**Error:** `Ollama not available`

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
# Open Ollama desktop app
```

**Error:** `Model not found`

**Solution:**
```bash
# Pull the model
ollama pull llama3.2:3b
```

---

### Beat Not Scheduling

**Problem:** Scheduled tasks don't run

**Solutions:**

1. **Check if Beat is running:**
   - Look for "Celery Beat" window
   - Should show: "Scheduler: Starting..."

2. **Check schedule:**
   ```bash
   celery -A backend.celery_app inspect scheduled
   ```

3. **Restart Beat:**
   - Close Beat window
   - Run `.\start_celery.bat` again

---

## Performance Tuning

### Worker Concurrency

**Default:** 1 worker (solo pool for Windows)

**Increase workers (Linux/Mac):**
```bash
celery -A backend.celery_app worker --concurrency=4
```

### Task Priorities

Tasks are processed in this order:
1. High priority (exploited, critical)
2. Medium priority (high severity)
3. Low priority (everything else)

### Rate Limiting

**LLM Processing:**
- Max 10 CVEs per batch (high priority)
- Max 20 CVEs per batch (medium priority)
- Max 50 CVEs per batch (low priority)

**Adjust in:** `backend/celery_app.py`

---

## Configuration

### Environment Variables

Add to `.env`:

```env
# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

### Task Timeouts

**Default:**
- Hard limit: 1 hour
- Soft limit: 55 minutes

**Change in:** `backend/celery_app.py`
```python
task_time_limit=3600,      # 1 hour
task_soft_time_limit=3300, # 55 minutes
```

---

## Production Deployment

### Systemd Service (Linux)

**Worker Service:**
```ini
[Unit]
Description=Celery Worker for OpenThreat
After=network.target redis.service

[Service]
Type=forking
User=openthreat
WorkingDirectory=/opt/openthreat
ExecStart=/opt/openthreat/venv/bin/celery -A backend.celery_app worker --loglevel=info --detach
Restart=always

[Install]
WantedBy=multi-user.target
```

**Beat Service:**
```ini
[Unit]
Description=Celery Beat for OpenThreat
After=network.target redis.service

[Service]
Type=simple
User=openthreat
WorkingDirectory=/opt/openthreat
ExecStart=/opt/openthreat/venv/bin/celery -A backend.celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Compose

```yaml
services:
  celery-worker:
    build: .
    command: celery -A backend.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/openthreat
    restart: always

  celery-beat:
    build: .
    command: celery -A backend.celery_app beat --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/openthreat
    restart: always
```

---

## Best Practices

### Development

1. **Always run Worker + Beat together**
2. **Check logs regularly** for errors
3. **Monitor task queue** to avoid backlog
4. **Test tasks manually** before scheduling

### Production

1. **Use multiple workers** for concurrency
2. **Set up monitoring** (Flower, Prometheus)
3. **Configure alerts** for failed tasks
4. **Regular health checks** for Redis/Ollama
5. **Log rotation** to manage disk space

---

## Common Commands

```bash
# Start everything
.\start_celery.bat

# Stop everything
# Close both Celery windows (Worker + Beat)

# Restart worker only
# Close Worker window, run: celery -A backend.celery_app worker --loglevel=info --pool=solo

# Restart beat only
# Close Beat window, run: celery -A backend.celery_app beat --loglevel=info

# Purge all tasks
celery -A backend.celery_app purge

# Check stats
python scripts/start_llm_processing.py --stats
```

---

## FAQ

### Q: Do I need to keep Celery running all the time?

**A:** Only if you want automatic background processing. You can also trigger tasks manually via API/CLI.

### Q: How much RAM does Celery use?

**A:** ~100-200 MB per worker. With LLM processing, Ollama uses ~2-4 GB.

### Q: Can I run Celery without Ollama?

**A:** Yes! LLM tasks will be skipped, but other tasks (data updates, cache) still work.

### Q: How fast is LLM processing?

**A:** ~2-5 seconds per CVE with llama3.2:3b. Faster with GPU.

### Q: What happens if a task fails?

**A:** Tasks retry up to 3 times with exponential backoff. After 3 failures, they're marked as failed.

---

## Need Help?

1. Check logs in Worker/Beat windows
2. Review this guide
3. Check `backend/celery_app.py` for configuration
4. Check `backend/tasks/llm_tasks.py` for task definitions

---

**Last Updated:** 2024-10-16
