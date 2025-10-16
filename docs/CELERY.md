# Celery - Automated Background Tasks

OpenThreat uses Celery for automated vulnerability updates and background processing.

## 🚀 Quick Start

### Start Everything (Recommended)

```bash
start-with-celery.bat
```

This starts:
- ✅ Docker (PostgreSQL + Redis)
- ✅ Backend API
- ✅ Frontend
- ✅ Celery Worker (processes tasks)
- ✅ Celery Beat (schedules tasks)

### Start Individually

**Celery Worker:**
```bash
start-celery-worker.bat
```

**Celery Beat (Scheduler):**
```bash
start-celery-beat.bat
```

**Or manually:**
```bash
# Worker
celery -A backend.celery_app worker --loglevel=info --pool=solo

# Beat
celery -A backend.celery_app beat --loglevel=info
```

---

## 📅 Scheduled Tasks

Celery Beat automatically runs these tasks:

| Task | Schedule | Description |
|------|----------|-------------|
| **Update Vulnerabilities** | Every 2 hours | Collects data from all sources and updates database |
| **Clean Cache** | Daily at 3 AM | Removes cache entries older than 24 hours |
| **Update Stats Cache** | Every 15 minutes | Recalculates dashboard statistics |

---

## 🎯 Manual Task Triggers

### Via API

**Trigger vulnerability update:**
```bash
curl -X POST http://localhost:8001/api/v1/tasks/update-vulnerabilities
```

**Check task status:**
```bash
curl http://localhost:8001/api/v1/tasks/{task_id}
```

**List scheduled tasks:**
```bash
curl http://localhost:8001/api/v1/tasks/scheduled/list
```

**Check worker status:**
```bash
curl http://localhost:8001/api/v1/tasks/workers/status
```

### Via CLI

**Trigger update:**
```bash
python scripts/manage_tasks.py update
```

**Test Celery connection:**
```bash
python scripts/manage_tasks.py test
```

**Check task status:**
```bash
python scripts/manage_tasks.py status <task_id>
```

**Monitor task (live):**
```bash
python scripts/manage_tasks.py monitor <task_id>
```

**List workers:**
```bash
python scripts/manage_tasks.py workers
```

**List scheduled tasks:**
```bash
python scripts/manage_tasks.py scheduled
```

---

## 📊 Task Details

### Update Vulnerabilities Task

**What it does:**
1. Runs all data connectors (CISA, NVD, EU CVE, MITRE)
2. Deduplicates and merges data
3. Ingests into PostgreSQL database
4. Updates priority scores

**Duration:** 10-30 minutes

**Schedule:** Every 2 hours at :00 (00:00, 02:00, 04:00, etc.)

**Manual trigger:**
```bash
# Via API
curl -X POST http://localhost:8001/api/v1/tasks/update-vulnerabilities

# Via CLI
python scripts/manage_tasks.py update
```

### Clean Cache Task

**What it does:**
- Removes search cache entries older than 24 hours
- Keeps database clean and performant

**Duration:** < 1 minute

**Schedule:** Daily at 3:00 AM

**Manual trigger:**
```bash
curl -X POST http://localhost:8001/api/v1/tasks/clean-cache
```

### Update Stats Cache Task

**What it does:**
- Recalculates dashboard statistics
- Updates cached values for faster loading

**Duration:** < 10 seconds

**Schedule:** Every 15 minutes

**Manual trigger:**
```bash
curl -X POST http://localhost:8001/api/v1/tasks/update-stats
```

---

## 🔍 Monitoring

### Check Worker Status

**Via API:**
```bash
curl http://localhost:8001/api/v1/tasks/workers/status
```

**Via CLI:**
```bash
python scripts/manage_tasks.py workers
```

**Expected output:**
```json
{
  "status": "healthy",
  "workers": [
    {
      "name": "celery@HOSTNAME",
      "active_tasks": 0,
      "registered_tasks": 5,
      "stats": {...}
    }
  ],
  "total_workers": 1
}
```

### Check Task Status

**Via API:**
```bash
curl http://localhost:8001/api/v1/tasks/{task_id}
```

**Via CLI:**
```bash
python scripts/manage_tasks.py status <task_id>
```

**Status values:**
- `PENDING` - Task is waiting to be executed
- `STARTED` - Task has started
- `SUCCESS` - Task completed successfully
- `FAILURE` - Task failed
- `RETRY` - Task is being retried

---

## 🐛 Troubleshooting

### No Workers Running

**Symptom:**
```
No Celery workers are running
```

**Solution:**
```bash
start-celery-worker.bat
```

### Redis Connection Failed

**Symptom:**
```
Error: Cannot connect to Redis
```

**Solution:**
1. Check if Redis is running:
   ```bash
   docker ps | findstr redis
   ```

2. Start Redis:
   ```bash
   docker-compose up -d redis
   ```

3. Check Redis URL in environment:
   ```bash
   echo %REDIS_URL%
   ```

### Task Stuck in PENDING

**Symptom:**
Task stays in PENDING status forever

**Possible causes:**
1. Worker not running
2. Worker can't connect to Redis
3. Task name mismatch

**Solution:**
1. Check workers: `python scripts/manage_tasks.py workers`
2. Restart worker: Stop and start `start-celery-worker.bat`
3. Check logs in worker window

### Task Failed

**Symptom:**
Task status is FAILURE

**Solution:**
1. Check task result for error:
   ```bash
   python scripts/manage_tasks.py status <task_id>
   ```

2. Check worker logs in the Celery Worker window

3. Common issues:
   - Database connection failed
   - Data connector timeout
   - File not found

---

## ⚙️ Configuration

### Celery Settings

Located in `backend/celery_app.py`:

```python
# Task time limits
task_time_limit = 3600  # 1 hour max
task_soft_time_limit = 3300  # 55 minutes soft limit

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50
```

### Schedule Configuration

Modify `beat_schedule` in `backend/celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    "update-vulnerabilities": {
        "task": "backend.tasks.update_vulnerabilities_task",
        "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
    },
}
```

**Crontab examples:**
- `crontab(minute=0, hour="*/2")` - Every 2 hours
- `crontab(minute=0, hour=3)` - Daily at 3 AM
- `crontab(minute="*/15")` - Every 15 minutes
- `crontab(hour=0, minute=0, day_of_week=1)` - Every Monday at midnight

---

## 🔐 Production Deployment

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/openthreat
```

### Systemd Service (Linux)

**Worker service** (`/etc/systemd/system/celery-worker.service`):
```ini
[Unit]
Description=Celery Worker for OpenThreat
After=network.target redis.service postgresql.service

[Service]
Type=forking
User=openthreat
Group=openthreat
WorkingDirectory=/opt/openthreat
ExecStart=/opt/openthreat/venv/bin/celery -A backend.celery_app worker --loglevel=info --detach
ExecStop=/opt/openthreat/venv/bin/celery -A backend.celery_app control shutdown
Restart=always

[Install]
WantedBy=multi-user.target
```

**Beat service** (`/etc/systemd/system/celery-beat.service`):
```ini
[Unit]
Description=Celery Beat for OpenThreat
After=network.target redis.service

[Service]
Type=simple
User=openthreat
Group=openthreat
WorkingDirectory=/opt/openthreat
ExecStart=/opt/openthreat/venv/bin/celery -A backend.celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

---

## 📈 Performance Tips

1. **Use separate workers for different task types:**
   ```bash
   # Fast tasks
   celery -A backend.celery_app worker -Q fast --concurrency=4
   
   # Slow tasks
   celery -A backend.celery_app worker -Q slow --concurrency=1
   ```

2. **Monitor with Flower:**
   ```bash
   pip install flower
   celery -A backend.celery_app flower
   ```
   Open http://localhost:5555

3. **Adjust worker pool:**
   - Windows: Use `--pool=solo` (required)
   - Linux: Use `--pool=prefork` for better performance

---

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Crontab Guru](https://crontab.guru/) - Cron schedule helper

---

**Last Updated:** 2024-10-14
