# OpenThreat Database Documentation

## Overview

OpenThreat uses **PostgreSQL** as its primary database. The database schema is managed using **SQLAlchemy ORM** with **Alembic** for migrations.

---

## Database Configuration

### Connection String
```
postgresql://openthreat:openthreat@localhost:5432/openthreat
```

### Environment Variables
```bash
DATABASE_URL=postgresql://openthreat:openthreat@localhost:5432/openthreat
POSTGRES_USER=openthreat
POSTGRES_PASSWORD=openthreat
POSTGRES_DB=openthreat
```

---

## Schema

### Tables

#### 1. `vulnerabilities`

Main table storing CVE information.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `cve_id` | VARCHAR(20) | No | CVE identifier (unique) |
| `title` | TEXT | Yes | Original vulnerability title |
| `description` | TEXT | Yes | Original technical description |
| `cvss_score` | FLOAT | Yes | CVSS base score (0.0-10.0) |
| `cvss_vector` | VARCHAR(100) | Yes | CVSS vector string |
| `severity` | VARCHAR(20) | Yes | Severity level (CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN) |
| `exploited_in_the_wild` | BOOLEAN | No | Whether actively exploited (default: false) |
| `priority_score` | FLOAT | Yes | Calculated priority score (0.0-1.0) |
| `published_at` | TIMESTAMP | Yes | Original publication date |
| `modified_at` | TIMESTAMP | Yes | Last modification date |
| `created_at` | TIMESTAMP | No | Record creation timestamp |
| `updated_at` | TIMESTAMP | No | Record update timestamp |
| `simple_title` | TEXT | Yes | LLM-generated simplified title |
| `simple_description` | TEXT | Yes | LLM-generated plain-language description |
| `llm_processed` | BOOLEAN | No | Whether LLM processing completed (default: false) |

**Indexes:**
- `ix_vulnerabilities_cve_id` (unique)
- `ix_vulnerabilities_severity`
- `ix_vulnerabilities_exploited_in_the_wild`
- `ix_vulnerabilities_published_at`
- `ix_vulnerabilities_cvss_score`
- `ix_vulnerabilities_priority_score`

**Constraints:**
- `cve_id` must be unique
- `severity` must be one of: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN

---

#### 2. `vulnerability_sources`

Junction table linking vulnerabilities to their data sources.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `vulnerability_id` | INTEGER | No | Foreign key to `vulnerabilities.id` |
| `source` | VARCHAR(50) | No | Source identifier (nvd, cisa_kev, vulncheck) |
| `created_at` | TIMESTAMP | No | Record creation timestamp |

**Indexes:**
- `ix_vulnerability_sources_vulnerability_id`
- `ix_vulnerability_sources_source`

**Foreign Keys:**
- `vulnerability_id` → `vulnerabilities.id` (CASCADE on delete)

**Unique Constraint:**
- (`vulnerability_id`, `source`)

---

#### 3. `vendors`

Table storing vendor/manufacturer information.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `name` | VARCHAR(255) | No | Vendor name (unique) |
| `created_at` | TIMESTAMP | No | Record creation timestamp |

**Indexes:**
- `ix_vendors_name` (unique)

---

#### 4. `products`

Table storing product information.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `name` | VARCHAR(255) | No | Product name |
| `vendor_id` | INTEGER | Yes | Foreign key to `vendors.id` |
| `created_at` | TIMESTAMP | No | Record creation timestamp |

**Indexes:**
- `ix_products_name`
- `ix_products_vendor_id`

**Foreign Keys:**
- `vendor_id` → `vendors.id` (SET NULL on delete)

**Unique Constraint:**
- (`name`, `vendor_id`)

---

#### 5. `vulnerability_products`

Junction table linking vulnerabilities to affected products.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `vulnerability_id` | INTEGER | No | Foreign key to `vulnerabilities.id` |
| `product_id` | INTEGER | No | Foreign key to `products.id` |
| `version_affected` | VARCHAR(100) | Yes | Affected version(s) |
| `created_at` | TIMESTAMP | No | Record creation timestamp |

**Indexes:**
- `ix_vulnerability_products_vulnerability_id`
- `ix_vulnerability_products_product_id`

**Foreign Keys:**
- `vulnerability_id` → `vulnerabilities.id` (CASCADE on delete)
- `product_id` → `products.id` (CASCADE on delete)

**Unique Constraint:**
- (`vulnerability_id`, `product_id`)

---

#### 6. `references`

Table storing external reference links.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `vulnerability_id` | INTEGER | No | Foreign key to `vulnerabilities.id` |
| `url` | TEXT | No | Reference URL |
| `source` | VARCHAR(50) | Yes | Reference source |
| `created_at` | TIMESTAMP | No | Record creation timestamp |

**Indexes:**
- `ix_references_vulnerability_id`

**Foreign Keys:**
- `vulnerability_id` → `vulnerabilities.id` (CASCADE on delete)

---

#### 7. `cwe_mappings`

Junction table linking vulnerabilities to CWE (Common Weakness Enumeration) IDs.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `vulnerability_id` | INTEGER | No | Foreign key to `vulnerabilities.id` |
| `cwe_id` | VARCHAR(20) | No | CWE identifier (e.g., CWE-78) |
| `created_at` | TIMESTAMP | No | Record creation timestamp |

**Indexes:**
- `ix_cwe_mappings_vulnerability_id`
- `ix_cwe_mappings_cwe_id`

**Foreign Keys:**
- `vulnerability_id` → `vulnerabilities.id` (CASCADE on delete)

**Unique Constraint:**
- (`vulnerability_id`, `cwe_id`)

---

#### 8. `rss_feeds`

Table storing RSS feed configurations.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Primary key (auto-increment) |
| `name` | VARCHAR(255) | No | Feed name |
| `url` | TEXT | No | Feed URL |
| `enabled` | BOOLEAN | No | Whether feed is active (default: true) |
| `last_fetched` | TIMESTAMP | Yes | Last successful fetch timestamp |
| `created_at` | TIMESTAMP | No | Record creation timestamp |
| `updated_at` | TIMESTAMP | No | Record update timestamp |

**Indexes:**
- `ix_rss_feeds_enabled`

---

## Entity Relationships

```
vulnerabilities (1) ←→ (N) vulnerability_sources
vulnerabilities (1) ←→ (N) vulnerability_products ←→ (N) products
vulnerabilities (1) ←→ (N) references
vulnerabilities (1) ←→ (N) cwe_mappings
products (N) ←→ (1) vendors
```

### Diagram

```
┌─────────────────┐
│  vulnerabilities│
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌────────────────┐  ┌──────────────┐
│vulnerability_  │  │vulnerability_│
│sources         │  │products      │
└────────────────┘  └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  products    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   vendors    │
                    └──────────────┘
```

---

## Data Sources

### 1. NVD (National Vulnerability Database)
- **Source ID:** `nvd`
- **Update Frequency:** Every 2 hours
- **Data:** CVE details, CVSS scores, descriptions, references

### 2. CISA KEV (Known Exploited Vulnerabilities)
- **Source ID:** `cisa_kev`
- **Update Frequency:** Daily
- **Data:** Actively exploited CVEs, exploitation status

### 3. VulnCheck
- **Source ID:** `vulncheck`
- **Update Frequency:** Every 6 hours
- **Data:** Enhanced CVE data, exploitation intelligence

---

## Priority Score Calculation

The `priority_score` is calculated based on:

1. **CVSS Score** (40% weight)
   - CRITICAL (9.0-10.0): 1.0
   - HIGH (7.0-8.9): 0.7
   - MEDIUM (4.0-6.9): 0.4
   - LOW (0.1-3.9): 0.2

2. **Exploitation Status** (40% weight)
   - Exploited in the wild: 1.0
   - Not exploited: 0.0

3. **Recency** (20% weight)
   - Published within 7 days: 1.0
   - Published within 30 days: 0.5
   - Older: 0.0

**Formula:**
```
priority_score = (cvss_weight * 0.4) + (exploited_weight * 0.4) + (recency_weight * 0.2)
```

---

## Indexes and Performance

### Query Optimization

**Most Common Queries:**

1. **Get recent vulnerabilities:**
   ```sql
   SELECT * FROM vulnerabilities 
   ORDER BY published_at DESC 
   LIMIT 20;
   ```
   - Uses: `ix_vulnerabilities_published_at`

2. **Filter by severity:**
   ```sql
   SELECT * FROM vulnerabilities 
   WHERE severity = 'CRITICAL';
   ```
   - Uses: `ix_vulnerabilities_severity`

3. **Filter by exploitation:**
   ```sql
   SELECT * FROM vulnerabilities 
   WHERE exploited_in_the_wild = true;
   ```
   - Uses: `ix_vulnerabilities_exploited_in_the_wild`

4. **Get CVE by ID:**
   ```sql
   SELECT * FROM vulnerabilities 
   WHERE cve_id = 'CVE-2024-1234';
   ```
   - Uses: `ix_vulnerabilities_cve_id` (unique)

---

## Migrations

### Alembic Setup

**Initialize migrations:**
```bash
cd backend
alembic init alembic
```

**Create migration:**
```bash
alembic revision --autogenerate -m "Description"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

### Migration History

Migrations are stored in `backend/alembic/versions/`.

---

## Backup and Restore

### Backup Database

```bash
docker exec openthreat-db pg_dump -U openthreat openthreat > backup.sql
```

### Restore Database

```bash
docker exec -i openthreat-db psql -U openthreat openthreat < backup.sql
```

---

## Database Maintenance

### Vacuum and Analyze

Run periodically to optimize performance:

```sql
VACUUM ANALYZE vulnerabilities;
VACUUM ANALYZE vulnerability_sources;
VACUUM ANALYZE products;
```

### Check Table Sizes

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Sample Queries

### Get all critical exploited CVEs with products

```sql
SELECT 
    v.cve_id,
    v.title,
    v.cvss_score,
    v.published_at,
    array_agg(DISTINCT p.name) as products,
    array_agg(DISTINCT vn.name) as vendors
FROM vulnerabilities v
LEFT JOIN vulnerability_products vp ON v.id = vp.vulnerability_id
LEFT JOIN products p ON vp.product_id = p.id
LEFT JOIN vendors vn ON p.vendor_id = vn.id
WHERE v.severity = 'CRITICAL' 
  AND v.exploited_in_the_wild = true
GROUP BY v.id
ORDER BY v.published_at DESC;
```

### Get vulnerability count by vendor

```sql
SELECT 
    vn.name as vendor,
    COUNT(DISTINCT v.id) as vulnerability_count
FROM vendors vn
JOIN products p ON vn.id = p.vendor_id
JOIN vulnerability_products vp ON p.id = vp.product_id
JOIN vulnerabilities v ON vp.vulnerability_id = v.id
GROUP BY vn.name
ORDER BY vulnerability_count DESC
LIMIT 10;
```

### Get recent vulnerabilities with LLM processing status

```sql
SELECT 
    cve_id,
    title,
    simple_title,
    llm_processed,
    published_at
FROM vulnerabilities
WHERE published_at >= NOW() - INTERVAL '7 days'
ORDER BY published_at DESC;
```

---

## Data Integrity

### Constraints

1. **Unique CVE IDs:** Each CVE can only exist once
2. **Referential Integrity:** Foreign keys ensure data consistency
3. **Cascade Deletes:** Deleting a vulnerability removes all related data
4. **Timestamps:** All records track creation time

### Validation

- `cve_id` format: `CVE-YYYY-NNNNN`
- `cvss_score` range: 0.0 - 10.0
- `severity` enum: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
- `priority_score` range: 0.0 - 1.0

---

## Performance Considerations

### Recommended Settings

For production, adjust PostgreSQL settings:

```ini
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### Connection Pooling

SQLAlchemy connection pool settings:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## Monitoring

### Useful Queries

**Active connections:**
```sql
SELECT count(*) FROM pg_stat_activity;
```

**Long-running queries:**
```sql
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

**Table statistics:**
```sql
SELECT * FROM pg_stat_user_tables;
```

---

## Security

### Best Practices

1. **Never expose database directly** - Always use API layer
2. **Use strong passwords** - Change default credentials
3. **Regular backups** - Automated daily backups
4. **Monitor access** - Log all database connections
5. **Principle of least privilege** - API user has minimal permissions

### Recommended Permissions

```sql
-- Create read-only user for reporting
CREATE USER openthreat_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE openthreat TO openthreat_readonly;
GRANT USAGE ON SCHEMA public TO openthreat_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO openthreat_readonly;
```
