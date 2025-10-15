# Database Documentation

## Overview

OpenThreat uses **PostgreSQL** as the primary database with the following extensions:
- `pg_trgm` - Trigram-based fuzzy text search
- `btree_gin` - GIN index support for efficient searching

## Schema

### Tables

#### `vulnerabilities`
Stores CVE records from all sources (CISA KEV, NVD, EU CVE Search).

**Key Fields:**
- `cve_id` (unique) - CVE identifier
- `title`, `description` - Vulnerability details
- `cvss_score`, `severity` - Risk metrics
- `exploited_in_the_wild` - Boolean flag for active exploitation
- `priority_score` - Computed score (0.0-1.0) for prioritization
- `sources` - JSON array of data sources
- `affected_products`, `vendors`, `products` - JSON arrays
- `references` - JSON array of URLs and metadata

**Indexes:**
- GIN trigram indexes on `cve_id`, `title`, `description` for fuzzy search
- B-tree indexes on `cvss_score`, `severity`, `exploited_in_the_wild`, timestamps

#### `techniques`
MITRE ATT&CK techniques and tactics.

**Key Fields:**
- `technique_id` (unique) - MITRE technique ID (e.g., T1234)
- `name`, `description` - Technique details
- `tactics` - JSON array of tactics
- `platforms` - JSON array of affected platforms

#### `iocs`
Indicators of Compromise (URLs, domains, IPs, hashes).

**Key Fields:**
- `ioc_type` - Type: url, domain, ip, hash, email
- `value` - The actual IOC value
- `threat_type` - Classification: malware, phishing, c2, etc.
- `confidence` - Confidence score (0.0-1.0)
- `status` - active, inactive, expired

#### `ingestion_runs`
Tracks data ingestion runs for monitoring.

**Key Fields:**
- `source` - Data source identifier
- `status` - running, success, failed
- `records_fetched`, `records_inserted`, `records_updated`, `records_failed`
- `started_at`, `completed_at`, `duration_seconds`

#### `search_cache`
Caches expensive search queries.

**Key Fields:**
- `cache_key` - Hash of query parameters
- `results` - Cached JSON results
- `expires_at` - Cache expiration timestamp

## Setup

### 1. Start Database

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Check status
docker-compose ps
```

### 2. Run Migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 3. Load Data

```bash
# Ingest deduplicated CVEs
python -m backend.ingestion Data_Sample_Connectors/out/deduplicated_cves.ndjson initial_load
```

### Quick Setup Script

```bash
python scripts/setup_db.py
```

## Database Operations

### Connect to Database

```bash
# Using Docker
docker exec -it openthreat-db psql -U openthreat -d openthreat

# Using psql directly
psql postgresql://openthreat:openthreat@localhost:5432/openthreat
```

### Useful Queries

```sql
-- Count vulnerabilities
SELECT COUNT(*) FROM vulnerabilities;

-- Count exploited vulnerabilities
SELECT COUNT(*) FROM vulnerabilities WHERE exploited_in_the_wild = true;

-- Top 10 by priority score
SELECT cve_id, title, priority_score, cvss_score, exploited_in_the_wild
FROM vulnerabilities
ORDER BY priority_score DESC
LIMIT 10;

-- Search by CVE ID (fuzzy)
SELECT cve_id, title, cvss_score
FROM vulnerabilities
WHERE cve_id ILIKE '%2024%'
LIMIT 10;

-- Recent ingestion runs
SELECT id, source, status, records_inserted, records_updated, started_at
FROM ingestion_runs
ORDER BY started_at DESC
LIMIT 10;

-- Vulnerabilities by severity
SELECT severity, COUNT(*) as count
FROM vulnerabilities
GROUP BY severity
ORDER BY count DESC;

-- Top vendors by vulnerability count
SELECT 
    jsonb_array_elements_text(vendors::jsonb) as vendor,
    COUNT(*) as vuln_count
FROM vulnerabilities
WHERE vendors IS NOT NULL
GROUP BY vendor
ORDER BY vuln_count DESC
LIMIT 20;
```

### Backup and Restore

```bash
# Backup
docker exec openthreat-db pg_dump -U openthreat openthreat > backup.sql

# Restore
docker exec -i openthreat-db psql -U openthreat openthreat < backup.sql
```

## Migrations

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field"

# Create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Performance Tuning

### Indexes

The schema includes several indexes for performance:

1. **GIN Trigram Indexes** - Fast fuzzy text search
   - `ix_vuln_cve_id_trgm`
   - `ix_vuln_title_trgm`
   - `ix_vuln_description_trgm`

2. **B-tree Indexes** - Fast exact lookups and range queries
   - `ix_vulnerabilities_cvss_score`
   - `ix_vulnerabilities_severity`
   - `ix_vulnerabilities_exploited_in_the_wild`
   - `ix_vulnerabilities_published_at`

### Query Optimization

```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE
SELECT * FROM vulnerabilities
WHERE exploited_in_the_wild = true
ORDER BY priority_score DESC
LIMIT 20;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql://openthreat:openthreat@localhost:5432/openthreat

# Redis connection
REDIS_URL=redis://localhost:6379/0
```

## Troubleshooting

### Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Migration Issues

```bash
# Reset migrations (CAUTION: destroys data)
docker-compose down -v
docker-compose up -d postgres redis
alembic upgrade head
```

### Performance Issues

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum and analyze
VACUUM ANALYZE vulnerabilities;
```

## Security

### Production Recommendations

1. **Change default passwords** in `docker-compose.yml`
2. **Use environment variables** for sensitive data
3. **Enable SSL/TLS** for database connections
4. **Restrict network access** to database ports
5. **Regular backups** with encryption
6. **Monitor access logs**

### Password Management

```bash
# Generate secure password
openssl rand -base64 32

# Update in docker-compose.yml and .env file
```

## Monitoring

### Database Metrics

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Database size
SELECT pg_size_pretty(pg_database_size('openthreat'));
```

### Health Check

```bash
# Check database health
docker exec openthreat-db pg_isready -U openthreat
```
