# Data Sample Connectors

This directory contains connectors to fetch threat intelligence data from various open sources.

## Available Connectors

### CVE Sources

#### 1. **CISA KEV** (`cisa_kev.py`)
Fetches the CISA Known Exploited Vulnerabilities catalog.
- **Source**: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **Data**: Vulnerabilities actively exploited in the wild
- **Update Frequency**: Daily

```bash
python cisa_kev.py
```

#### 2. **NVD Recent** (`nvd_recent.py`)
Fetches recently modified CVEs from NVD (last 7 days).
- **Source**: NVD API 2.0
- **Data**: Recently updated vulnerabilities
- **Rate Limit**: Use `NVD_API_KEY` env variable for higher limits

```bash
# Without API key (rate limited)
python nvd_recent.py

# With API key (recommended)
export NVD_API_KEY="your-api-key"
python nvd_recent.py
```

#### 3. **NVD CVE** (`nvd_cve.py`) ✨ NEW
Comprehensive CVE data from NVD with full metadata.
- **Source**: NVD API 2.0
- **Data**: Complete CVE information including CVSS, CWE, CPE, references
- **Features**: Search by date range, CVE ID, or keyword

```bash
# Last 7 days (default)
python nvd_cve.py

# Last 30 days
python nvd_cve.py --days 30

# Specific CVE
python nvd_cve.py --cve CVE-2024-1234

# Keyword search
python nvd_cve.py --keyword "apache"
```

#### 4. **EU CVE Search** (`eu_cve.py`) ✨ NEW
European CVE data from CVE Search (CIRCL).
- **Source**: https://cve.circl.lu/api/
- **Data**: CVE data with European context and alternative metadata
- **Features**: Search by CVE ID, vendor, or recent CVEs

```bash
# Last 30 recent CVEs (default)
python eu_cve.py

# Last 100 CVEs
python eu_cve.py --limit 100

# Specific CVE
python eu_cve.py --cve CVE-2024-1234

# Search by vendor
python eu_cve.py --vendor microsoft --limit 50
```

### Threat Intelligence

#### 5. **MITRE ATT&CK** (`mitre_attack_enterprise.py`)
Fetches MITRE ATT&CK Enterprise framework data.
- **Source**: https://attack.mitre.org/
- **Data**: Tactics, techniques, and procedures (TTPs)

```bash
python mitre_attack_enterprise.py
```

#### 6. **URLhaus** (`urlhaus_recent.py`)
Fetches recent malicious URLs from abuse.ch URLhaus.
- **Source**: https://urlhaus.abuse.ch/
- **Data**: Malicious URLs and IOCs
- **Status**: Currently disabled (needs fixing)

```bash
# python urlhaus_recent.py  # Currently disabled
```

## Deduplication

The `deduplicator.py` module merges CVE records from multiple sources to avoid duplicates.

### Features
- Groups records by CVE ID
- Merges data from all sources with priority: CISA > NVD CVE > NVD Recent > EU CVE
- Combines unique values (references, products, CWEs)
- Preserves exploitation status from any source

### Usage

```bash
# Deduplicate all CVE sources
python deduplicator.py

# Custom input directory
python deduplicator.py --input-dir ./out

# Custom output file
python deduplicator.py --output ./deduplicated.ndjson

# Specific patterns only
python deduplicator.py --patterns cisa_kev nvd_cve
```

## Run All Connectors

Use `run_all.py` to execute all connectors and perform deduplication:

```bash
python run_all.py
```

This will:
1. Run all enabled connectors
2. Save output to `out/` directory with timestamps
3. Automatically deduplicate CVE records
4. Generate `out/deduplicated_cves.ndjson`

## Output Format

All connectors output **NDJSON** (newline-delimited JSON) format:
- One JSON object per line
- UTF-8 encoded
- Timestamped filenames: `{source}-{YYYYMMDD-HHMMSS}.ndjson`

### Example Output Structure

```json
{
  "source": "nvd_cve",
  "cve_id": "CVE-2024-1234",
  "description": "A vulnerability in...",
  "cvss_score": 9.8,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "severity": "CRITICAL",
  "published": "2024-01-15T10:00:00Z",
  "last_modified": "2024-01-20T15:30:00Z",
  "vendors": ["apache", "microsoft"],
  "products": ["http_server", "windows"],
  "affected_products": ["apache:http_server:2.4.57", "microsoft:windows:10"],
  "cwe_ids": ["CWE-79", "CWE-89"],
  "references": [
    {"url": "https://...", "type": "patch"}
  ],
  "exploited_in_the_wild": true
}
```

## API Keys & Rate Limits

### NVD API Key (Recommended)
Without an API key, NVD API is limited to 5 requests per 30 seconds.

Get a free API key: https://nvd.nist.gov/developers/request-an-api-key

```bash
# Set environment variable
export NVD_API_KEY="your-api-key-here"

# Or in PowerShell
$env:NVD_API_KEY="your-api-key-here"
```

## Dependencies

```bash
pip install -r ../requirements.txt
```

Required packages:
- `requests` - HTTP client
- `pydantic` - Data validation

## Next Steps

After running connectors, use the normalizer to convert data to unified models:

```bash
cd ../normalizer
python runner.py
```

## Troubleshooting

### Rate Limiting
If you see rate limit errors from NVD:
1. Set `NVD_API_KEY` environment variable
2. Reduce the date range (`--days` parameter)
3. Add delays between requests

### Network Errors
- Check your internet connection
- Some APIs may be temporarily unavailable
- Retry after a few minutes

### Empty Results
- Check if the API is accessible
- Verify date ranges are valid
- Some sources may have no recent data
