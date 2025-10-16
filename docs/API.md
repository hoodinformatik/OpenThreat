# OpenThreat API Documentation

## Base URL
```
http://localhost:8001/api/v1
```

## Authentication
Currently, no authentication is required. All endpoints are publicly accessible.

---

## Endpoints

### 1. Get Statistics

**GET** `/stats`

Returns overall statistics about vulnerabilities in the database.

**Response:**
```json
{
  "total_vulnerabilities": 3209,
  "exploited_vulnerabilities": 1436,
  "critical_vulnerabilities": 104,
  "high_vulnerabilities": 472,
  "by_severity": {
    "CRITICAL": 104,
    "HIGH": 472,
    "MEDIUM": 839,
    "LOW": 111,
    "UNKNOWN": 1683
  },
  "recent_updates": 3209,
  "last_update": "2025-10-13T20:07:46.096993Z"
}
```

---

### 2. List Vulnerabilities

**GET** `/vulnerabilities`

Returns a paginated list of vulnerabilities with optional filtering and sorting.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max: 100) |
| `sort_by` | string | "published_at" | Sort field: `published_at`, `modified_at`, `cvss_score`, `severity`, `priority_score` |
| `sort_order` | string | "desc" | Sort order: `asc` or `desc` |
| `severity` | string | - | Filter by severity: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` |
| `exploited` | boolean | - | Filter by exploitation status: `true` or `false` |
| `source` | string | - | Filter by source: `nvd`, `cisa_kev`, `vulncheck` |
| `vendor` | string | - | Filter by vendor name (partial match) |
| `product` | string | - | Filter by product name (partial match) |
| `search` | string | - | Search in CVE ID, title, and description |

**Example Request:**
```bash
GET /api/v1/vulnerabilities?severity=CRITICAL&exploited=true&page_size=10
```

**Response:**
```json
{
  "items": [
    {
      "cve_id": "CVE-2024-1234",
      "title": "Critical Remote Code Execution in Apache",
      "description": "A critical vulnerability allows remote attackers...",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "severity": "CRITICAL",
      "exploited_in_the_wild": true,
      "priority_score": 0.95,
      "published_at": "2024-10-15T12:00:00Z",
      "modified_at": "2024-10-15T14:30:00Z",
      "sources": ["nvd", "cisa_kev"],
      "simple_title": "Apache Server Hack Risk",
      "simple_description": "Hackers can remotely take control of Apache web servers...",
      "llm_processed": true
    }
  ],
  "total": 104,
  "page": 1,
  "page_size": 10,
  "total_pages": 11
}
```

---

### 3. Get Single Vulnerability

**GET** `/vulnerabilities/{cve_id}`

Returns detailed information about a specific CVE.

**Path Parameters:**
- `cve_id` (string, required): CVE identifier (e.g., `CVE-2024-1234`)

**Example Request:**
```bash
GET /api/v1/vulnerabilities/CVE-2024-1234
```

**Response:**
```json
{
  "cve_id": "CVE-2024-1234",
  "title": "Critical Remote Code Execution in Apache",
  "description": "A critical vulnerability allows remote attackers to execute arbitrary code...",
  "cvss_score": 9.8,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "severity": "CRITICAL",
  "exploited_in_the_wild": true,
  "priority_score": 0.95,
  "published_at": "2024-10-15T12:00:00Z",
  "modified_at": "2024-10-15T14:30:00Z",
  "sources": ["nvd", "cisa_kev"],
  "vendors": [
    {
      "name": "Apache Software Foundation",
      "products": ["Apache HTTP Server"]
    }
  ],
  "references": [
    {
      "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-1234",
      "source": "nvd"
    }
  ],
  "cwe_ids": ["CWE-78"],
  "simple_title": "Apache Server Hack Risk",
  "simple_description": "Hackers can remotely take control of Apache web servers without needing a password...",
  "llm_processed": true
}
```

**Error Response (404):**
```json
{
  "detail": "CVE not found"
}
```

---

### 4. Search Vulnerabilities

**GET** `/search`

Advanced search endpoint with full-text search capabilities.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20, max: 100) |

**Example Request:**
```bash
GET /api/v1/search?q=apache+remote+code+execution&page_size=10
```

**Response:**
Same format as `/vulnerabilities` endpoint.

---

### 5. Get RSS Feeds

**GET** `/feeds`

Returns a list of configured RSS feeds.

**Response:**
```json
{
  "feeds": [
    {
      "id": 1,
      "name": "NVD Recent CVEs",
      "url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
      "enabled": true,
      "last_fetched": "2024-10-15T12:00:00Z"
    }
  ]
}
```

---

### 6. Get Vendors

**GET** `/vendors`

Returns a list of all vendors in the database.

**Query Parameters:**
- `search` (string, optional): Filter vendors by name

**Response:**
```json
{
  "vendors": [
    {
      "name": "Apache Software Foundation",
      "product_count": 15,
      "vulnerability_count": 234
    }
  ]
}
```

---

### 7. Get Products

**GET** `/products`

Returns a list of all products in the database.

**Query Parameters:**
- `vendor` (string, optional): Filter by vendor name
- `search` (string, optional): Filter products by name

**Response:**
```json
{
  "products": [
    {
      "name": "Apache HTTP Server",
      "vendor": "Apache Software Foundation",
      "vulnerability_count": 89
    }
  ]
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid parameter value"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. This may change in future versions.

---

## CORS

CORS is enabled for all origins in development mode. In production, configure allowed origins in the backend configuration.

---

## Data Freshness

- **NVD Data**: Updated every 2 hours via background tasks
- **CISA KEV**: Updated daily
- **VulnCheck**: Updated every 6 hours (if configured)

---

## Pagination

All list endpoints support pagination with the following parameters:
- `page`: Page number (1-indexed)
- `page_size`: Items per page (max: 100)

Response includes:
- `total`: Total number of items
- `page`: Current page number
- `page_size`: Items per page
- `total_pages`: Total number of pages

---

## Sorting

Supported sort fields:
- `published_at`: Publication date
- `modified_at`: Last modification date
- `cvss_score`: CVSS score (0-10)
- `severity`: Severity level
- `priority_score`: Calculated priority (0-1)

Sort order:
- `asc`: Ascending
- `desc`: Descending (default)

---

## Filtering

### Severity Levels
- `CRITICAL`: CVSS 9.0-10.0
- `HIGH`: CVSS 7.0-8.9
- `MEDIUM`: CVSS 4.0-6.9
- `LOW`: CVSS 0.1-3.9
- `UNKNOWN`: No CVSS score available

### Sources
- `nvd`: National Vulnerability Database
- `cisa_kev`: CISA Known Exploited Vulnerabilities
- `vulncheck`: VulnCheck API

---

## LLM-Generated Content

Vulnerabilities may include simplified content generated by a local LLM:

- `simple_title`: Short, non-technical title
- `simple_description`: Plain-language explanation (2-3 sentences)
- `llm_processed`: Boolean indicating if LLM processing was successful

If `llm_processed` is `false`, fall back to original `title` and `description`.

---

## Examples

### Get all critical exploited vulnerabilities
```bash
curl "http://localhost:8001/api/v1/vulnerabilities?severity=CRITICAL&exploited=true"
```

### Search for Apache vulnerabilities
```bash
curl "http://localhost:8001/api/v1/search?q=apache"
```

### Get a specific CVE
```bash
curl "http://localhost:8001/api/v1/vulnerabilities/CVE-2024-1234"
```

### Get recent vulnerabilities (last 7 days)
```bash
curl "http://localhost:8001/api/v1/vulnerabilities?sort_by=published_at&sort_order=desc&page_size=20"
```
