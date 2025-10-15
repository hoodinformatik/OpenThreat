# OpenThreat API Documentation

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

Currently, the API is **public and does not require authentication**.

---

## Endpoints

### Health Check

#### `GET /health`

Check API and database health.

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-10-13T20:00:00Z"
}
```

---

### Vulnerabilities

#### `GET /api/v1/vulnerabilities`

List vulnerabilities with pagination and filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `severity` (string): Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `exploited` (boolean): Filter by exploitation status
- `sort_by` (string): Sort field (default: priority_score)
- `sort_order` (string): Sort order (asc/desc, default: desc)

**Example:**
```bash
curl "http://localhost:8000/api/v1/vulnerabilities?page=1&page_size=10&severity=CRITICAL"
```

**Response:**
```json
{
  "total": 3209,
  "page": 1,
  "page_size": 10,
  "total_pages": 321,
  "items": [
    {
      "cve_id": "CVE-2024-1234",
      "title": "Critical Vulnerability in...",
      "description": "...",
      "cvss_score": 9.8,
      "severity": "CRITICAL",
      "exploited_in_the_wild": true,
      "priority_score": 0.95,
      "published_at": "2024-01-15T10:00:00Z",
      "sources": ["cisa", "nvd_cve"]
    }
  ]
}
```

---

#### `GET /api/v1/vulnerabilities/exploited`

List vulnerabilities exploited in the wild.

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page

**Example:**
```bash
curl "http://localhost:8000/api/v1/vulnerabilities/exploited"
```

---

#### `GET /api/v1/vulnerabilities/recent`

List recently published vulnerabilities.

**Query Parameters:**
- `days` (int): Number of days to look back (default: 30, max: 365)
- `page` (int): Page number
- `page_size` (int): Items per page

**Example:**
```bash
curl "http://localhost:8000/api/v1/vulnerabilities/recent?days=7"
```

---

#### `GET /api/v1/vulnerabilities/{cve_id}`

Get detailed information about a specific vulnerability.

**Path Parameters:**
- `cve_id` (string): CVE identifier (e.g., CVE-2024-1234)

**Example:**
```bash
curl "http://localhost:8000/api/v1/vulnerabilities/CVE-2024-1234"
```

**Response:**
```json
{
  "id": 123,
  "cve_id": "CVE-2024-1234",
  "title": "Critical Vulnerability...",
  "description": "Detailed description...",
  "cvss_score": 9.8,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "severity": "CRITICAL",
  "exploited_in_the_wild": true,
  "priority_score": 0.95,
  "published_at": "2024-01-15T10:00:00Z",
  "modified_at": "2024-01-20T15:30:00Z",
  "cisa_due_date": "2024-02-15",
  "cwe_ids": ["CWE-79", "CWE-89"],
  "affected_products": ["vendor:product:version"],
  "vendors": ["microsoft", "apache"],
  "products": ["windows", "http_server"],
  "references": [
    {
      "url": "https://...",
      "type": "patch",
      "tags": ["Patch", "Vendor Advisory"]
    }
  ],
  "sources": ["cisa", "nvd_cve"],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z"
}
```

---

#### `GET /api/v1/vulnerabilities/vendor/{vendor}`

List vulnerabilities affecting a specific vendor.

**Path Parameters:**
- `vendor` (string): Vendor name (case-insensitive)

**Example:**
```bash
curl "http://localhost:8000/api/v1/vulnerabilities/vendor/microsoft"
```

---

### Search

#### `GET /api/v1/search`

Advanced search with multiple filters.

**Query Parameters:**
- `q` (string): Search query (CVE ID, title, description)
- `severity` (string): Filter by severity
- `exploited` (boolean): Filter by exploitation status
- `vendor` (string): Filter by vendor
- `product` (string): Filter by product
- `cwe` (string): Filter by CWE ID
- `min_cvss` (float): Minimum CVSS score (0.0-10.0)
- `max_cvss` (float): Maximum CVSS score (0.0-10.0)
- `published_after` (string): Published after date (YYYY-MM-DD)
- `published_before` (string): Published before date (YYYY-MM-DD)
- `page` (int): Page number
- `page_size` (int): Items per page
- `sort_by` (string): Sort field
- `sort_order` (string): Sort order

**Example:**
```bash
curl "http://localhost:8000/api/v1/search?q=apache&min_cvss=7.0&exploited=true"
```

---

#### `GET /api/v1/search/suggest`

Get search suggestions based on partial query.

**Query Parameters:**
- `q` (string): Search query (min 2 characters)
- `limit` (int): Number of suggestions (default: 10, max: 50)

**Example:**
```bash
curl "http://localhost:8000/api/v1/search/suggest?q=CVE-2024"
```

**Response:**
```json
{
  "suggestions": [
    {
      "cve_id": "CVE-2024-1234",
      "title": "Critical Vulnerability..."
    }
  ]
}
```

---

### Statistics

#### `GET /api/v1/stats`

Get overall statistics for the dashboard.

**Example:**
```bash
curl "http://localhost:8000/api/v1/stats"
```

**Response:**
```json
{
  "total_vulnerabilities": 3209,
  "exploited_vulnerabilities": 1436,
  "critical_vulnerabilities": 450,
  "high_vulnerabilities": 1200,
  "by_severity": {
    "CRITICAL": 450,
    "HIGH": 1200,
    "MEDIUM": 1000,
    "LOW": 500,
    "UNKNOWN": 59
  },
  "recent_updates": 150,
  "last_update": "2024-10-13T20:00:00Z"
}
```

---

#### `GET /api/v1/stats/top-vendors`

Get top vendors by vulnerability count.

**Query Parameters:**
- `limit` (int): Number of vendors (default: 20)

**Example:**
```bash
curl "http://localhost:8000/api/v1/stats/top-vendors?limit=10"
```

**Response:**
```json
{
  "vendors": [
    {"name": "microsoft", "count": 450},
    {"name": "apache", "count": 320}
  ]
}
```

---

#### `GET /api/v1/stats/severity-distribution`

Get vulnerability distribution by severity.

**Example:**
```bash
curl "http://localhost:8000/api/v1/stats/severity-distribution"
```

**Response:**
```json
{
  "distribution": [
    {
      "severity": "CRITICAL",
      "count": 450,
      "percentage": 14.02
    }
  ],
  "total": 3209
}
```

---

#### `GET /api/v1/stats/timeline`

Get vulnerability publication timeline.

**Query Parameters:**
- `days` (int): Number of days (default: 30)

**Example:**
```bash
curl "http://localhost:8000/api/v1/stats/timeline?days=7"
```

**Response:**
```json
{
  "timeline": [
    {"date": "2024-10-13", "count": 25},
    {"date": "2024-10-12", "count": 18}
  ]
}
```

---

#### `GET /api/v1/stats/ingestion-history`

Get recent ingestion run history.

**Query Parameters:**
- `limit` (int): Number of runs (default: 10)

**Example:**
```bash
curl "http://localhost:8000/api/v1/stats/ingestion-history"
```

---

### RSS Feeds

#### `GET /api/v1/feeds/rss`

RSS feed of recent vulnerabilities.

**Query Parameters:**
- `limit` (int): Number of items (default: 50, max: 100)
- `exploited_only` (boolean): Only exploited vulnerabilities

**Example:**
```bash
curl "http://localhost:8000/api/v1/feeds/rss?limit=20"
```

---

#### `GET /api/v1/feeds/exploited`

RSS feed of exploited vulnerabilities.

**Example:**
```bash
curl "http://localhost:8000/api/v1/feeds/exploited"
```

---

#### `GET /api/v1/feeds/critical`

RSS feed of critical vulnerabilities.

**Example:**
```bash
curl "http://localhost:8000/api/v1/feeds/critical"
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Vulnerability CVE-2024-9999 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

## Rate Limiting

Currently **no rate limiting** is implemented. This will be added in a future release.

---

## CORS

CORS is enabled for the following origins (configurable via `ALLOWED_ORIGINS` env variable):
- `http://localhost:3000`
- `http://localhost:8000`

---

## Running the API

### Development
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Examples

### Get top 10 exploited vulnerabilities
```bash
curl "http://localhost:8000/api/v1/vulnerabilities/exploited?page_size=10"
```

### Search for Apache vulnerabilities with CVSS > 7.0
```bash
curl "http://localhost:8000/api/v1/search?vendor=apache&min_cvss=7.0"
```

### Get critical vulnerabilities from last 7 days
```bash
curl "http://localhost:8000/api/v1/search?severity=CRITICAL&published_after=2024-10-06"
```

### Subscribe to RSS feed in your reader
```
http://localhost:8000/api/v1/feeds/exploited
```
