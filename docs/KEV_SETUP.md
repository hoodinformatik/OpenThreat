# CISA KEV (Known Exploited Vulnerabilities) Setup

## Overview

OpenThreat automatically tracks vulnerabilities that are actively exploited in the wild using the CISA Known Exploited Vulnerabilities (KEV) catalog via the NVD API.

## Initial Setup

After cloning the repository, run the initial KEV import once:

```bash
python3 scripts/fetch_cisa_kev.py
```

This will:
- Fetch all CVEs marked as KEV from the NVD API
- Mark them as `exploited_in_the_wild = True` in the database
- Update priority scores (exploited CVEs get higher priority)
- Add `cisa_kev` as a data source

**Expected output:**
```
[2025-10-19 11:31:29] Starting CISA KEV fetch...
✓ CISA KEV import completed:
  - Total KEV entries: 1442
  - Updated in DB: 1442
  - Not found in DB: 0
```

## Automatic Updates

Once the initial import is complete, the system automatically updates KEV data:

### Celery Beat Schedule

KEV data is automatically fetched **daily at 09:00 UTC** via Celery Beat.

See `backend/celery_app.py`:
```python
"fetch-cisa-kev": {
    "task": "tasks.fetch_cisa_kev",
    "schedule": crontab(minute=0, hour=9),  # Daily at 09:00 UTC
},
```

### Manual Trigger

You can also manually trigger a KEV update:

**Via Script:**
```bash
python3 scripts/fetch_cisa_kev.py
```

**Via API (requires ADMIN role):**
```bash
curl -X POST https://your-domain.com/api/v1/data-sources/cisa-kev/fetch \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## How It Works

1. **Data Source**: Uses NVD API with `hasKev` parameter
   - URL: `https://services.nvd.nist.gov/rest/json/cves/2.0?hasKev`
   - No direct CISA website access needed (avoids blocking)

2. **Rate Limiting**: Respects NVD API limits
   - 5 requests per 30 seconds without API key
   - 6-second delay between requests

3. **Database Updates**:
   - Sets `exploited_in_the_wild = True`
   - Adds `cisa_kev` to sources array
   - Recalculates priority scores (exploited = higher priority)

4. **Stats API**: Automatically reflects exploited count
   - Endpoint: `/api/v1/stats`
   - Field: `exploited_vulnerabilities`
   - Cached for 5 minutes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     NVD API (hasKev)                        │
│   https://services.nvd.nist.gov/rest/json/cves/2.0?hasKev  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            CISAKEVService (backend/services)                │
│  - fetch_kev_cves(): Fetch from NVD API                     │
│  - update_exploited_vulnerabilities(): Update DB            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Celery Task (backend/tasks/data_tasks.py)           │
│  - fetch_cisa_kev_task: Scheduled daily at 09:00 UTC       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  - exploited_in_the_wild: Boolean flag                      │
│  - sources: JSON array with "cisa_kev"                      │
│  - priority_score: Recalculated with exploitation factor    │
└─────────────────────────────────────────────────────────────┘
```

## Files

- **Service**: `backend/services/cisa_kev_service.py`
- **Task**: `backend/tasks/data_tasks.py` → `fetch_cisa_kev_task`
- **API**: `backend/api/v1/data_sources.py` → `/cisa-kev/fetch`
- **Schedule**: `backend/celery_app.py` → `beat_schedule`
- **Script**: `scripts/fetch_cisa_kev.py`

## Troubleshooting

### No exploited vulnerabilities showing

1. Check if initial import was run:
   ```bash
   python3 scripts/fetch_cisa_kev.py
   ```

2. Verify database:
   ```sql
   SELECT COUNT(*) FROM vulnerabilities WHERE exploited_in_the_wild = true;
   ```

3. Clear stats cache:
   ```bash
   python3 scripts/clear_stats_cache.py
   ```

### Celery Beat not running

Ensure Celery Beat is started:
```bash
celery -A backend.celery_app beat --loglevel=info
```

### NVD API rate limiting

If you hit rate limits, get a free NVD API key:
- https://nvd.nist.gov/developers/request-an-api-key
- Add to `.env`: `NVD_API_KEY=your-key-here`

## Monitoring

Check KEV status via API:
```bash
curl https://your-domain.com/api/v1/data-sources/cisa-kev/status
```

Response:
```json
{
  "source": "cisa_kev",
  "status": "active",
  "exploited_vulnerabilities": 1442,
  "cves_from_cisa": 1442,
  "catalog_url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
}
```

## References

- [CISA KEV Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [NVD API Documentation](https://nvd.nist.gov/developers/vulnerabilities)
- [NVD API hasKev Parameter](https://services.nvd.nist.gov/rest/json/cves/2.0?hasKev)
