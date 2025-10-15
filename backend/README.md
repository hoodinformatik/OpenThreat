# Backend - OpenThreat

FastAPI-based backend for the OpenThreat platform.

## Structure

```
backend/
├── __init__.py
├── database.py          # Database configuration and session management
├── models.py            # SQLAlchemy ORM models
├── ingestion.py         # Data ingestion pipeline
├── main.py              # FastAPI application (coming in Phase 4)
├── api/                 # API endpoints (coming in Phase 4)
└── tasks.py             # Celery background tasks (coming in Phase 2)
```

## Database Models

### Vulnerability
Stores CVE records from all sources with:
- CVE identifiers and metadata
- CVSS scores and severity
- Exploitation status
- Affected products and vendors
- References and CWE mappings
- Computed priority scores

### Technique
MITRE ATT&CK techniques:
- Technique IDs and descriptions
- Tactics and platforms
- Detection and mitigation guidance

### IOC
Indicators of Compromise:
- URLs, domains, IPs, hashes
- Threat classification
- Confidence scores
- Status tracking

### IngestionRun
Tracks data ingestion:
- Source and status
- Record statistics
- Timing and errors

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Database

```bash
docker-compose up -d postgres redis
```

### 4. Run Migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 5. Load Data

```bash
python -m backend.ingestion Data_Sample_Connectors/out/deduplicated_cves.ndjson initial_load
```

## Usage

### Ingestion

```python
from pathlib import Path
from backend.ingestion import run_ingestion

# Ingest from NDJSON file
run = run_ingestion(
    file_path=Path("data/deduplicated_cves.ndjson"),
    source="deduplicated_cves"
)

print(f"Inserted: {run.records_inserted}")
print(f"Updated: {run.records_updated}")
```

### Database Queries

```python
from backend.database import SessionLocal
from backend.models import Vulnerability

db = SessionLocal()

# Get exploited vulnerabilities
exploited = db.query(Vulnerability).filter(
    Vulnerability.exploited_in_the_wild == True
).order_by(
    Vulnerability.priority_score.desc()
).limit(10).all()

for vuln in exploited:
    print(f"{vuln.cve_id}: {vuln.title} (Score: {vuln.priority_score})")
```

## Priority Score Calculation

The priority score (0.0-1.0) is calculated based on:

1. **Exploitation Status (50%)**: +0.5 if exploited in the wild
2. **CVSS Score (40%)**: Normalized from 0-10 to 0-0.4
3. **Recency (10%)**: Higher score for CVEs published in last 30 days

Example:
- Exploited CVE with CVSS 9.8 published 5 days ago: ~0.97
- Non-exploited CVE with CVSS 7.5 published 60 days ago: ~0.30

## Database Schema

See [DATABASE.md](../DATABASE.md) for detailed schema documentation.

## Development

### Run Tests

```bash
pytest backend/tests/
```

### Code Style

```bash
# Format code
black backend/

# Lint
ruff check backend/
```

## Next Steps

- Phase 3: Priority scoring and plain-language explanations
- Phase 4: FastAPI endpoints and RSS feeds
- Phase 5: Frontend integration
