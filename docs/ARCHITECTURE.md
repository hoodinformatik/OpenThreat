# OpenThreat Architecture Documentation

## System Overview

OpenThreat is a full-stack web application for tracking and analyzing cybersecurity vulnerabilities (CVEs). The system aggregates data from multiple sources, processes it with AI, and presents it through a modern web interface.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │  Search  │  │   Feeds  │  │   CVE    │   │
│  │   Page   │  │   Page   │  │   Page   │  │  Detail  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                    http://localhost:3000                     │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   REST API   │  │  Background  │  │     LLM      │     │
│  │  Endpoints   │  │    Tasks     │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                    http://localhost:8001                     │
└────────┬───────────────────┬───────────────────┬───────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │  Redis (Celery) │  │  Ollama (LLM)   │
│    Database     │  │   Task Queue    │  │  llama3.2:3b    │
│   Port: 5432    │  │   Port: 6379    │  │  Port: 11434    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         ▲
         │
         │ Data Ingestion
         │
┌────────┴────────────────────────────────────────────────────┐
│                    External Data Sources                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   NVD    │  │ CISA KEV │  │VulnCheck │  │RSS Feeds │   │
│  │   API    │  │   JSON   │  │   API    │  │   XML    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **UI Components:** shadcn/ui
- **Icons:** Lucide React
- **HTTP Client:** Native Fetch API

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Task Queue:** Celery
- **Validation:** Pydantic

### Infrastructure
- **Database:** PostgreSQL 15
- **Cache/Queue:** Redis 7
- **LLM:** Ollama (llama3.2:3b)
- **Container:** Docker & Docker Compose
- **Web Server:** Uvicorn (ASGI)

---

## Component Details

### 1. Frontend (Next.js)

**Location:** `/frontend`

**Key Features:**
- Server-side rendering (SSR) for SEO
- Client-side filtering and search
- Responsive design (mobile-first)
- Real-time data updates

**Pages:**
- `/` - Dashboard with recent vulnerabilities
- `/vulnerabilities` - Full vulnerability list with filters
- `/vulnerabilities/[cveId]` - CVE detail page
- `/search` - Advanced search interface
- `/feeds` - RSS feed management

**Components:**
```
frontend/
├── app/                    # Next.js App Router pages
├── components/
│   ├── ui/                # shadcn/ui components
│   └── custom/            # Custom components
├── lib/
│   ├── api.ts            # API client functions
│   └── utils.ts          # Utility functions
└── public/               # Static assets
```

---

### 2. Backend API (FastAPI)

**Location:** `/backend`

**Key Features:**
- RESTful API design
- Automatic OpenAPI documentation
- CORS enabled for frontend
- Background task processing
- LLM integration

**Structure:**
```
backend/
├── main.py               # FastAPI app entry point
├── models.py             # SQLAlchemy models
├── schemas.py            # Pydantic schemas
├── database.py           # Database connection
├── api/
│   └── v1/
│       ├── vulnerabilities.py  # CVE endpoints
│       ├── search.py           # Search endpoints
│       └── feeds.py            # Feed endpoints
├── services/
│   ├── nvd_service.py          # NVD data fetcher
│   ├── cisa_service.py         # CISA KEV fetcher
│   └── llm_service.py          # LLM integration
├── tasks/
│   └── celery_tasks.py         # Background tasks
└── scripts/
    ├── fetch_nvd.py            # NVD data import
    └── process_with_llm.py     # LLM processing
```

---

### 3. Database (PostgreSQL)

**Location:** Docker container `openthreat-db`

**Key Tables:**
- `vulnerabilities` - Main CVE data
- `vulnerability_sources` - Data source tracking
- `vendors` - Vendor information
- `products` - Product information
- `vulnerability_products` - CVE-Product mapping
- `references` - External links
- `cwe_mappings` - CWE classifications
- `rss_feeds` - Feed configurations

**See:** [DATABASE.md](./DATABASE.md) for detailed schema

---

### 4. Task Queue (Celery + Redis)

**Purpose:** Background processing for:
- Data fetching from external sources
- LLM processing of CVE descriptions
- Scheduled updates
- Bulk operations

**Tasks:**
```python
# Scheduled tasks
@celery.task
def fetch_nvd_data():
    """Fetch latest CVEs from NVD (every 2 hours)"""
    
@celery.task
def fetch_cisa_kev():
    """Fetch CISA KEV list (daily)"""
    
@celery.task
def process_cve_with_llm(cve_id):
    """Generate simplified descriptions (on-demand)"""
```

**Configuration:**
- **Broker:** Redis (localhost:6379)
- **Result Backend:** Redis
- **Concurrency:** 4 workers
- **Task Timeout:** 300 seconds

---

### 5. LLM Service (Ollama)

**Purpose:** Generate simplified, non-technical descriptions of CVEs

**Model:** llama3.2:3b (3 billion parameters)

**Features:**
- Local inference (no external API calls)
- Privacy-preserving (data stays local)
- Fast generation (~2-5 seconds per CVE)
- Automatic cleanup of LLM artifacts

**Processing:**
1. Extract CVE metadata (severity, CVSS, vendors)
2. Generate simplified title (50 tokens)
3. Generate plain-language description (150 tokens)
4. Clean up meta-text and formatting
5. Store in database

**See:** `backend/llm_service.py`

---

## Data Flow

### 1. Data Ingestion Flow

```
External Source → Fetcher Service → Database → API → Frontend
```

**Example: NVD CVE Import**
1. Celery task triggers `fetch_nvd_data()`
2. NVD Service fetches recent CVEs via API
3. Data is parsed and validated (Pydantic)
4. SQLAlchemy creates/updates database records
5. Background task queues LLM processing
6. Frontend fetches updated data via API

---

### 2. User Request Flow

```
User → Frontend → API → Database → API → Frontend → User
```

**Example: View CVE Details**
1. User clicks CVE card on dashboard
2. Next.js navigates to `/vulnerabilities/CVE-2024-1234`
3. Frontend fetches data: `GET /api/v1/vulnerabilities/CVE-2024-1234`
4. Backend queries database (SQLAlchemy)
5. Response includes LLM-generated content
6. Frontend renders CVE details

---

### 3. LLM Processing Flow

```
Database → LLM Service → Ollama → LLM Service → Database
```

**Example: Generate Simplified Description**
1. Script/task identifies unprocessed CVEs
2. LLM Service extracts CVE metadata
3. Prompts are constructed with context
4. Ollama generates title and description
5. Text is cleaned (remove meta-text)
6. Database is updated with results

---

## API Design

### RESTful Principles

**Resource-based URLs:**
```
GET    /api/v1/vulnerabilities          # List all
GET    /api/v1/vulnerabilities/{id}     # Get one
POST   /api/v1/vulnerabilities          # Create (admin)
PUT    /api/v1/vulnerabilities/{id}     # Update (admin)
DELETE /api/v1/vulnerabilities/{id}     # Delete (admin)
```

**Query Parameters:**
```
?page=1&page_size=20                    # Pagination
?sort_by=published_at&sort_order=desc   # Sorting
?severity=CRITICAL&exploited=true       # Filtering
?search=apache                          # Search
```

**Response Format:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**See:** [API.md](./API.md) for complete API documentation

---

## Security Considerations

### Current Implementation

1. **No Authentication:** API is publicly accessible (development)
2. **CORS Enabled:** All origins allowed (development)
3. **SQL Injection:** Protected by SQLAlchemy ORM
4. **XSS:** React/Next.js auto-escapes output
5. **Local LLM:** No data sent to external services

### Production Recommendations

1. **Add Authentication:**
   - JWT tokens for API access
   - OAuth2 for user login
   - API key for external integrations

2. **Rate Limiting:**
   - Limit requests per IP/user
   - Prevent abuse and DoS

3. **HTTPS Only:**
   - SSL/TLS certificates
   - Secure cookies

4. **Input Validation:**
   - Strict Pydantic schemas
   - Sanitize user input

5. **Database Security:**
   - Strong passwords
   - Encrypted connections
   - Regular backups

---

## Scalability

### Current Capacity

- **Database:** ~10,000 CVEs (tested with 3,209)
- **API:** ~100 requests/second (single instance)
- **LLM:** ~20 CVEs/minute (local processing)

### Scaling Strategies

#### Horizontal Scaling

**Frontend:**
- Deploy multiple Next.js instances
- Use load balancer (Nginx, AWS ALB)
- CDN for static assets (Cloudflare, Vercel)

**Backend:**
- Run multiple FastAPI instances
- Load balance with Nginx/Traefik
- Shared PostgreSQL and Redis

**Workers:**
- Scale Celery workers independently
- Dedicated workers for LLM tasks

#### Vertical Scaling

**Database:**
- Increase PostgreSQL resources
- Add read replicas for queries
- Partition large tables

**LLM:**
- Use GPU for faster inference
- Larger models for better quality
- Batch processing for efficiency

---

## Monitoring and Logging

### Current Implementation

**Logging:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Processing CVE-2024-1234")
```

**Locations:**
- Backend logs: `backend/logs/`
- Frontend logs: Browser console
- Database logs: Docker logs

### Production Recommendations

1. **Centralized Logging:**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Grafana Loki
   - CloudWatch (AWS)

2. **Metrics:**
   - Prometheus + Grafana
   - Track: API latency, error rates, DB queries
   - Alerts for anomalies

3. **Health Checks:**
   - `/health` endpoint
   - Database connectivity
   - Redis availability
   - Ollama status

4. **Error Tracking:**
   - Sentry for exception tracking
   - Automatic error notifications

---

## Deployment

### Development (Current)

```bash
# Start all services
./start.bat

# Services:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8001
# - Database: localhost:5432
# - Redis: localhost:6379
# - Ollama: localhost:11434
```

### Production Recommendations

**Option 1: Docker Compose (Simple)**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Option 2: Kubernetes (Scalable)**
```yaml
# Separate deployments for:
# - Frontend (3 replicas)
# - Backend (5 replicas)
# - Workers (10 replicas)
# - PostgreSQL (StatefulSet)
# - Redis (StatefulSet)
```

**Option 3: Cloud Services**
- Frontend: Vercel, Netlify
- Backend: AWS ECS, Google Cloud Run
- Database: AWS RDS, Google Cloud SQL
- Queue: AWS SQS, Google Pub/Sub

---

## Development Workflow

### Local Development

1. **Start services:** `./start.bat`
2. **Make changes:** Edit code in `/frontend` or `/backend`
3. **Hot reload:** Changes auto-reload (Next.js, Uvicorn)
4. **Test:** Manual testing in browser
5. **Commit:** Git commit with descriptive message

### Database Changes

1. **Modify models:** Edit `backend/models.py`
2. **Create migration:** `alembic revision --autogenerate -m "Description"`
3. **Review migration:** Check `backend/alembic/versions/`
4. **Apply migration:** `alembic upgrade head`

### Adding New Features

1. **Backend:**
   - Add model (if needed)
   - Create schema (Pydantic)
   - Implement endpoint (FastAPI)
   - Test with Swagger UI

2. **Frontend:**
   - Create/update page
   - Add API client function
   - Implement UI components
   - Test in browser

---

## Testing Strategy

### Current State

- **Manual Testing:** Browser-based testing
- **API Testing:** Swagger UI (`/docs`)

### Recommended Testing

**Backend:**
```python
# Unit tests
pytest backend/tests/test_api.py
pytest backend/tests/test_services.py

# Integration tests
pytest backend/tests/test_integration.py

# Coverage
pytest --cov=backend
```

**Frontend:**
```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Component tests
npm run test:components
```

---

## Performance Optimization

### Database

1. **Indexes:** Already optimized for common queries
2. **Connection Pooling:** SQLAlchemy pool (20 connections)
3. **Query Optimization:** Use `select_related` for joins
4. **Caching:** Redis for frequently accessed data

### API

1. **Pagination:** Limit results to 100 per page
2. **Field Selection:** Only return needed fields
3. **Compression:** Gzip responses
4. **Caching:** Cache headers for static data

### Frontend

1. **Code Splitting:** Next.js automatic splitting
2. **Image Optimization:** Next.js Image component
3. **Lazy Loading:** Load components on demand
4. **Memoization:** React.memo for expensive renders

### LLM

1. **Batch Processing:** Process multiple CVEs together
2. **Async Processing:** Don't block API requests
3. **Caching:** Store results in database
4. **Queue Management:** Prioritize critical CVEs

---

## Future Enhancements

### Planned Features

1. **User Authentication:**
   - User accounts
   - Saved searches
   - Custom alerts

2. **Advanced Analytics:**
   - Trend analysis
   - Vulnerability forecasting
   - Risk scoring

3. **Notifications:**
   - Email alerts for new CVEs
   - Webhook integrations
   - Slack/Discord bots

4. **API Enhancements:**
   - GraphQL endpoint
   - WebSocket for real-time updates
   - Bulk export (CSV, JSON)

5. **AI Improvements:**
   - Better LLM prompts
   - Multi-language support
   - Automatic remediation suggestions

---

## Troubleshooting

### Common Issues

**Frontend not loading:**
```bash
# Check if backend is running
curl http://localhost:8001/api/v1/stats

# Restart frontend
cd frontend
npm run dev
```

**Database connection error:**
```bash
# Check if PostgreSQL is running
docker ps | grep openthreat-db

# Restart database
docker restart openthreat-db
```

**LLM processing slow:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Use smaller batch size
python scripts/process_with_llm.py --limit 10
```

---

## Contact and Support

For questions or issues:
- Check documentation in `/docs`
- Review code comments
- Check logs in `/backend/logs`
- Open GitHub issue (if applicable)
