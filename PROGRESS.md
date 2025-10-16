# OpenThreat - Development Progress

## ✅ Completed Phases

### Phase 0 — Repo Setup
- ✅ LICENSE (Apache-2.0)
- ✅ .gitignore
- ✅ README.md
- ⏳ GitHub Actions (pending)
- ✅ Docker Compose (PostgreSQL, Redis)

### Phase 1 — Data Aggregation
- ✅ **CISA KEV Connector** - Known Exploited Vulnerabilities
- ✅ **NVD Recent Connector** - Last 7 days updates
- ✅ **NVD CVE Connector** - Comprehensive CVE data with full metadata
- ✅ **EU CVE Connector** - European CVE Search (CIRCL)
- ✅ **MITRE ATT&CK Connector** - Techniques and tactics
- ⏳ abuse.ch URLhaus Connector (needs fixing)
- ✅ **Pydantic Schemas** - Vulnerability, IOC, Technique models
- ✅ **Deduplication Logic** - Smart merging by CVE ID with source prioritization

**Data Sources:**
- 4 active connectors
- 3,209 unique CVEs after deduplication
- 1,436 exploited vulnerabilities (CISA)

### Phase 2 — Database & Updates ✅
- ✅ **PostgreSQL Database** with Docker
- ✅ **SQLAlchemy Models** - Vulnerability, Technique, IOC, IngestionRun, SearchCache
- ✅ **Alembic Migrations** - Version control for database schema
- ✅ **GIN Trigram Indexes** - Fast fuzzy text search
- ✅ **Ingestion Pipeline** - NDJSON → Database with priority scoring
- ✅ **Redis** - Caching and Celery message broker
- ✅ **Health Monitoring** - Ingestion run tracking
- ✅ **Celery Worker** - Background task processing
- ✅ **Celery Beat** - Scheduled task automation
- ✅ **Automated Updates** - Every 2 hours
- ✅ **Task Management API** - Trigger and monitor tasks
- ✅ **CLI Tools** - Manage tasks from command line

**Database Stats:**
- 3,209 vulnerabilities loaded
- Full-text search enabled
- Priority scoring implemented

### Phase 3 — Prioritization ✅
- ✅ **Priority Score Formula** - Exploitation (50%) + CVSS (40%) + Recency (10%)
- ✅ Automatic calculation during ingestion
- ✅ Plain-language explanations
- ⏳ Localization (de/en) (pending)

### Phase 4 — API (FastAPI) ✅
- ✅ **FastAPI Application** - Production-ready REST API
- ✅ **Vulnerability Endpoints**
  - List with pagination and filtering
  - Detail view by CVE ID
  - Exploited vulnerabilities
  - Recent vulnerabilities
  - Filter by vendor/product
- ✅ **Search Endpoint** - Advanced filtering (severity, CVSS, dates, CWE, vendor, product)
- ✅ **Statistics Endpoints**
  - Dashboard stats
  - Top vendors
  - Severity distribution
  - Publication timeline
  - Ingestion history
- ✅ **RSS/Atom Feeds**
  - Recent vulnerabilities
  - Exploited vulnerabilities
  - Critical vulnerabilities
- ✅ **OpenAPI Documentation** - Swagger UI + ReDoc
- ✅ **CORS** - Configured for frontend
- ⏳ Rate limiting (pending)

**API Endpoints:** 20+ endpoints ready

### Phase 5 — Frontend (Next.js) ✅
- ✅ **Next.js 14** with App Router
- ✅ **TailwindCSS** for modern styling
- ✅ **Dashboard with KPIs** - Total CVEs, Exploited, Critical, Recent updates
- ✅ **Severity Distribution** - Visual breakdown
- ✅ **Top Exploited Vulnerabilities** - Real-time list
- ✅ **Recent Vulnerabilities** - Latest additions
- ✅ **Vulnerability List Page** - Paginated list with filters (severity, exploited, sort)
- ✅ **Vulnerability Detail Page** - Complete CVE information with metadata
- ✅ **Advanced Search Page** - Multi-criteria search (text, severity, vendor, product, CVSS, dates)
- ✅ **RSS Feeds Page** - Subscribe to feeds with popular RSS readers
- ✅ **Responsive Design** - Mobile-friendly
- ✅ **Clean UI** - Professional and accessible
- ✅ **Loading States** - Smooth user experience
- ✅ **Plain-Language Explanations** - Severity, exploitation, CVSS, CWE, priority scores
- ✅ **Action Plans** - Step-by-step recommendations based on urgency
- ✅ **Tooltips** - Contextual help throughout the interface
- ✅ **About Page** - Mission, data sources, how it works

---

## 🚀 Current Status

### What's Working:
1. ✅ **Data Collection** - 4 sources, 3,209 CVEs
2. ✅ **Database** - PostgreSQL with 3,209 records
3. ✅ **API** - 25+ endpoints, fully functional
4. ✅ **Search** - Advanced filtering and full-text search
5. ✅ **RSS Feeds** - Subscribe to updates
6. ✅ **Documentation** - API docs, database docs, setup guides
7. ✅ **Frontend** - Complete Next.js UI with 5 pages
8. ✅ **Plain-Language Explanations** - User-friendly descriptions
9. ✅ **Automation** - Celery with scheduled updates every 2 hours
10. ✅ **Task Management** - API and CLI tools

### What's Next:
1. 🔄 **Localization** - German/English support
2. 🔄 **Rate limiting** - API protection
3. 🔄 **GitHub Actions** - CI/CD pipeline
4. 🔄 **Deployment** - Production deployment guide
5. 🔄 **Monitoring** - Grafana/Prometheus dashboards

---

## 📊 Statistics

### Data Coverage:
- **Total CVEs**: 3,209
- **Exploited in Wild**: 1,436 (44.7%)
- **Sources**: CISA KEV, NVD, EU CVE Search, MITRE ATT&CK
- **Update Frequency**: Manual (will be automated)

### Technical Stack:
- **Frontend**: Next.js 14, React 18, TailwindCSS, TypeScript
- **Backend**: Python 3.13, FastAPI, SQLAlchemy
- **Database**: PostgreSQL 16 with pg_trgm extension
- **Cache**: Redis 7
- **API Docs**: OpenAPI/Swagger
- **Containerization**: Docker Compose

---

## 🔧 Quick Start

### 1. Start Infrastructure
```bash
docker-compose up -d postgres redis
```

### 2. Run Migrations
```bash
alembic upgrade head
```

### 3. Collect Data
```bash
python Data_Sample_Connectors/run_all.py
```

### 4. Load into Database
```bash
python -m backend.ingestion Data_Sample_Connectors/out/deduplicated_cves.ndjson initial_load
```

### 5. Start API
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

### 6. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 7. Access
- **Frontend**: http://localhost:3000
- **API Swagger UI**: http://localhost:8001/docs
- **API Root**: http://localhost:8001
- **Health Check**: http://localhost:8001/health

---

## 📁 Project Structure

```
OpenThreat/
├── Data_Sample_Connectors/     # Data collection
│   ├── cisa_kev.py
│   ├── nvd_cve.py
│   ├── eu_cve.py
│   ├── mitre_attack_enterprise.py
│   ├── deduplicator.py
│   └── out/                    # NDJSON outputs
├── backend/                    # FastAPI application
│   ├── main.py                 # FastAPI app
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # DB configuration
│   ├── ingestion.py            # Data ingestion
│   └── api/                    # API endpoints
│       ├── health.py
│       ├── vulnerabilities.py
│       ├── search.py
│       ├── stats.py
│       └── feeds.py
├── alembic/                    # Database migrations
├── scripts/                    # Utility scripts
│   ├── setup_db.py
│   └── setup_sqlite.py
├── docker-compose.yml          # Docker services
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
├── API.md                      # API documentation
├── DATABASE.md                 # Database documentation
└── TODO.md                     # Development roadmap
```

---

## 🎯 MVP Definition of Done

### Completed ✅
- [x] All 4 data sources ingest successfully
- [x] Database populated with consistent schema & indices
- [x] Priority score available in API
- [x] RSS/Atom feeds for exploited vulnerabilities
- [x] API with search and filtering
- [x] Frontend dashboard with KPIs and real-time data


### To Do
- [x] Local LLM which processes CVEs and creates plain-language summaries ✅
  - ✅ Ollama integration with Llama 3.2
  - ✅ Simple title generation (< 10 words)
  - ✅ Simple description generation (2-3 sentences)
  - ✅ Database fields for LLM-generated content
  - ✅ CLI tool for batch processing
  - ✅ Fallback to original content if LLM unavailable

### Optional
- [ ] Localization (German/English)
- [ ] Rate limiting for API
- [ ] Deployment guide (Docker, Kubernetes)
- [ ] GitHub Actions CI/CD
- [ ] Monitoring dashboards (Grafana)

---

## 🌟 Key Features

### For Security Professionals:
- ✅ Comprehensive CVE database (3,209 CVEs)
- ✅ Exploitation status tracking (1,436 exploited)
- ✅ Priority scoring for triage
- ✅ Advanced search and filtering
- ✅ RSS feeds for monitoring
- ✅ REST API for integration

### For SMBs & NGOs:
- ✅ Free and open-source
- ✅ Easy to deploy (Docker)
- ✅ Clear severity ratings
- ✅ Plain-language explanations
- ✅ User-friendly web interface
- ✅ Action recommendations
- ✅ No security expertise required

### For Developers:
- ✅ Well-documented API
- ✅ OpenAPI/Swagger specs
- ✅ Extensible architecture
- ✅ Multiple data sources
- ✅ Deduplication logic

---

## 📈 Roadmap: Complete CVE Coverage & Automation

### Phase 6 — Complete Data Coverage 🔄

#### Goal: Collect ALL CVEs (200,000+) from comprehensive sources

**Primary Data Sources:**

1. **NVD Complete Database** ⏳
   - Full CVE dataset from 1999-present (~200,000 CVEs)
   - Method: NVD API 2.0 with pagination
   - Update Strategy: Initial bulk load + incremental updates
   - Frequency: Every 2 hours for new/modified CVEs
   - Implementation: `scripts/fetch_nvd_complete.py`

2. **CVE.org Official Feed** ⏳
   - Direct from MITRE CVE Program
   - JSON 5.0 format
   - Method: GitHub repository sync or API
   - Update Strategy: Daily full sync
   - Frequency: Daily at 00:00 UTC
   - Implementation: `backend/services/cve_org_service.py`

3. **CISA KEV (Known Exploited Vulnerabilities)** ✅
   - Already implemented
   - Update Strategy: Daily refresh
   - Frequency: Daily at 06:00 UTC

4. **BSI CERT-Bund (German CERT)** ✅
   - German security advisories with CVE references
   - Method: RSS feed parsing
   - Update Strategy: Daily enrichment
   - Frequency: Daily at 08:00 UTC
   - Implementation: `backend/services/bsi_cert_service.py`
   - Provides: German descriptions, severity ratings, official recommendations

5. **VulnCheck KEV** ⏳
   - Extended exploitation intelligence
   - Requires API key (free tier available)
   - Update Strategy: Daily sync
   - Frequency: Every 6 hours
   - Implementation: `backend/services/vulncheck_service.py`

**Secondary/Enrichment Sources:**

5. **Exploit-DB** ⏳
   - Public exploit database
   - Links CVEs to working exploits
   - Method: CSV/JSON export + scraping
   - Update Strategy: Weekly sync
   - Implementation: `backend/services/exploitdb_service.py`

6. **GitHub Security Advisories** ⏳
   - Open source vulnerability database
   - Method: GraphQL API
   - Update Strategy: Daily sync
   - Frequency: Daily at 12:00 UTC
   - Implementation: `backend/services/github_advisory_service.py`

7. **OSV (Open Source Vulnerabilities)** ⏳
   - Google's vulnerability database
   - Covers open source ecosystems
   - Method: REST API
   - Update Strategy: Daily sync
   - Implementation: `backend/services/osv_service.py`

8. **Vulners.com API** ⏳
   - Aggregated vulnerability data
   - Requires API key (free tier: 100 requests/day)
   - Update Strategy: Weekly enrichment
   - Implementation: `backend/services/vulners_service.py`

---

### Automation Strategy

#### 1. Initial Bulk Import (One-time)

```python
# scripts/initial_bulk_load.py
"""
Load complete historical CVE dataset
Estimated: 200,000+ CVEs
Duration: 6-12 hours
"""

Tasks:
1. Fetch NVD complete dataset (1999-2024)
2. Fetch CVE.org complete dataset
3. Deduplicate and merge
4. Bulk insert to database
5. Queue LLM processing (background)
```

**Execution Plan:**
```bash
# Step 1: Download all data (parallel)
python scripts/fetch_nvd_complete.py --start-year 1999 --end-year 2024

# Step 2: Merge and deduplicate
python scripts/merge_all_sources.py --output complete_cves.ndjson

# Step 3: Bulk load to database
python scripts/bulk_import.py --file complete_cves.ndjson --batch-size 1000

# Step 4: Process with LLM (background, low priority)
python scripts/process_with_llm.py --all --batch-size 100
```

---

#### 2. Incremental Updates (Automated)

**Celery Beat Schedule:**

```python
# backend/celery_app.py - Scheduled Tasks

CELERYBEAT_SCHEDULE = {
    # Every 2 hours: NVD recent changes
    'fetch-nvd-recent': {
        'task': 'tasks.fetch_nvd_recent',
        'schedule': crontab(minute=0, hour='*/2'),  # 00:00, 02:00, 04:00...
    },
    
    # Daily 00:00 UTC: CVE.org full sync
    'fetch-cve-org': {
        'task': 'tasks.fetch_cve_org',
        'schedule': crontab(minute=0, hour=0),
    },
    
    # Daily 06:00 UTC: CISA KEV
    'fetch-cisa-kev': {
        'task': 'tasks.fetch_cisa_kev',
        'schedule': crontab(minute=0, hour=6),
    },
    
    # Every 6 hours: VulnCheck KEV
    'fetch-vulncheck': {
        'task': 'tasks.fetch_vulncheck',
        'schedule': crontab(minute=0, hour='*/6'),
    },
    
    # Daily 12:00 UTC: GitHub Advisories
    'fetch-github-advisories': {
        'task': 'tasks.fetch_github_advisories',
        'schedule': crontab(minute=0, hour=12),
    },
    
    # Weekly Sunday 03:00 UTC: Exploit-DB
    'fetch-exploitdb': {
        'task': 'tasks.fetch_exploitdb',
        'schedule': crontab(minute=0, hour=3, day_of_week=0),
    },
    
    # Daily 18:00 UTC: OSV
    'fetch-osv': {
        'task': 'tasks.fetch_osv',
        'schedule': crontab(minute=0, hour=18),
    },
    
    # Weekly Monday 04:00 UTC: Vulners enrichment
    'enrich-vulners': {
        'task': 'tasks.enrich_with_vulners',
        'schedule': crontab(minute=0, hour=4, day_of_week=1),
    },
    
    # Continuous: LLM processing queue (process 10 CVEs every 5 minutes)
    'process-llm-queue': {
        'task': 'tasks.process_llm_queue',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    
    # Daily 02:00 UTC: Database maintenance
    'db-maintenance': {
        'task': 'tasks.database_vacuum',
        'schedule': crontab(minute=0, hour=2),
    },
}
```

---

#### 3. Smart Deduplication & Merging

```python
# backend/services/deduplication.py

Priority Order (highest to lowest):
1. NVD (official, most complete)
2. CVE.org (authoritative)
3. VulnCheck (enrichment)
4. CISA KEV (exploitation status)
5. GitHub Advisories (open source context)
6. Exploit-DB (proof of concept)
7. OSV (ecosystem-specific)
8. Vulners (aggregated)

Merge Strategy:
- CVE ID: Primary key (unique)
- Title: Prefer NVD > CVE.org > others
- Description: Prefer NVD (most detailed)
- CVSS: Prefer NVD official score
- Exploited: Union of all sources (if ANY source says exploited = true)
- References: Merge all unique URLs
- CWE: Merge all unique CWE IDs
- Vendors/Products: Merge all unique combinations
- Sources: Track all contributing sources
```

---

#### 4. LLM Processing Queue

```python
# backend/tasks/llm_tasks.py

Strategy:
1. Priority Queue:
   - High Priority: Exploited CVEs, CRITICAL severity, Recent (< 7 days)
   - Medium Priority: HIGH severity, Recent (< 30 days)
   - Low Priority: All others

2. Rate Limiting:
   - Process 10 CVEs per batch
   - 5-minute intervals
   - ~2,880 CVEs per day
   - Complete 200,000 CVEs in ~70 days (background)

3. Retry Logic:
   - 3 retries on failure
   - Exponential backoff
   - Mark as failed after 3 attempts
   - Manual review queue

4. Monitoring:
   - Track processing rate
   - Monitor Ollama health
   - Alert on failures
   - Dashboard for progress
```

---

#### 5. Data Freshness Monitoring

```python
# backend/api/v1/health.py

Health Check Endpoint:
GET /api/v1/health/sources

Response:
{
  "sources": [
    {
      "name": "NVD",
      "last_update": "2024-10-16T06:00:00Z",
      "status": "healthy",
      "next_update": "2024-10-16T08:00:00Z",
      "total_cves": 198543
    },
    {
      "name": "CISA KEV",
      "last_update": "2024-10-16T06:00:00Z",
      "status": "healthy",
      "next_update": "2024-10-17T06:00:00Z",
      "total_cves": 1436
    }
  ],
  "database": {
    "total_cves": 200145,
    "llm_processed": 45230,
    "llm_pending": 154915
  }
}
```

---

### Implementation Checklist

**Phase 6.1: Complete Data Sources** ⏳
- [ ] NVD Complete API integration
- [ ] CVE.org feed integration
- [ ] VulnCheck API integration
- [ ] Exploit-DB integration
- [ ] GitHub Security Advisories integration
- [ ] OSV integration
- [ ] Vulners API integration

**Phase 6.2: Automation Infrastructure** ⏳
- [ ] Celery Beat schedule configuration
- [ ] Task monitoring dashboard
- [ ] Error handling and retry logic
- [ ] Rate limiting for external APIs
- [ ] Health check endpoints
- [ ] Alert system for failures

**Phase 6.3: Bulk Import** ⏳
- [ ] Bulk download scripts
- [ ] Parallel processing
- [ ] Progress tracking
- [ ] Resume capability (checkpoint)
- [ ] Database optimization for bulk insert

**Phase 6.4: LLM Processing** ⏳
- [ ] Priority queue implementation
- [ ] Batch processing optimization
- [ ] Progress dashboard
- [ ] Manual review queue
- [ ] Quality metrics

**Phase 6.5: Monitoring & Maintenance** ⏳
- [ ] Grafana dashboards
- [ ] Prometheus metrics
- [ ] Log aggregation
- [ ] Database backup automation
- [ ] Performance monitoring

---

### Estimated Timeline

**Week 1-2: Data Source Integration**
- Implement all 8 data sources
- Test individual connectors
- Validate data quality

**Week 3: Bulk Import**
- Download complete datasets
- Merge and deduplicate
- Load into database
- Verify data integrity

**Week 4: Automation Setup**
- Configure Celery Beat
- Implement all scheduled tasks
- Test update cycles
- Monitor for 7 days

**Week 5-6: LLM Processing**
- Process high-priority CVEs first
- Monitor processing rate
- Optimize prompts
- Background processing for remaining CVEs

**Week 7-8: Monitoring & Polish**
- Set up dashboards
- Configure alerts
- Performance tuning
- Documentation

---

### Success Metrics

**Data Coverage:**
- ✅ Target: 200,000+ CVEs
- ✅ Update Latency: < 2 hours for critical CVEs
- ✅ Data Freshness: 95% of CVEs updated within 24 hours

**Automation:**
- ✅ Uptime: 99.5% for scheduled tasks
- ✅ Error Rate: < 1% for data fetching
- ✅ LLM Processing: 100% coverage within 90 days

**Performance:**
- ✅ API Response Time: < 200ms (p95)
- ✅ Search Performance: < 500ms for complex queries
- ✅ Database Size: < 50GB (optimized)

---

## 🙏 Acknowledgments

Data sources:
- CISA Known Exploited Vulnerabilities Catalog
- National Vulnerability Database (NVD)
- CVE Search (CIRCL)
- MITRE ATT&CK Framework

---

**Last Updated**: 2024-10-13
**Version**: 0.1.0 (MVP in progress)
