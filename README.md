# OpenThreat - Public Threat Intelligence Dashboard

**Mission**  
Democratize Threat Intelligence.  
We are building a **free and open-source platform** that aggregates *Indicators of Compromise (IOCs)*, *exploited vulnerabilities*, and *threat data* into a **clear and accessible interface**.  
Not just for security professionals but also for **SMBs, NGOs, and the public**.

## ✨ Features

- ✅ **3,209 CVEs** tracked from multiple sources
- ✅ **1,436 exploited vulnerabilities** (CISA KEV)
- ✅ **Priority scoring** (exploitation + CVSS + recency)
- ✅ **Advanced search** with multiple filters
- ✅ **REST API** with 20+ endpoints
- ✅ **RSS/Atom feeds** for monitoring
- ✅ **Modern web interface** with real-time data
- ✅ **PostgreSQL database** with full-text search

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Python 3.13+
- Node.js 18+

### 1. Start Infrastructure
```bash
docker-compose up -d postgres redis
```

### 2. Set up Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Collect data
python Data_Sample_Connectors/run_all.py

# Load into database
python -m backend.ingestion Data_Sample_Connectors/out/deduplicated_cves.ndjson initial_load

# Start API
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Access
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8001/docs
- **API**: http://localhost:8001

## 📊 Data Sources

- [CISA Known Exploited Vulnerabilities (KEV)](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)  
- [NVD CVE Database](https://nvd.nist.gov/)  
- [CVE Search (CIRCL)](https://cve.circl.lu/)
- [MITRE ATT&CK](https://attack.mitre.org/)  

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  Next.js 14, TailwindCSS
│  (Port 3000)│
└──────┬──────┘
       │
       │ REST API
       │
┌──────▼──────┐
│  FastAPI    │  Python 3.13, SQLAlchemy
│  (Port 8001)│
└──────┬──────┘
       │
       ├─────────────┐
       │             │
┌──────▼──────┐ ┌───▼────┐
│ PostgreSQL  │ │ Redis  │
│  (Port 5432)│ │ (6379) │
└─────────────┘ └────────┘
```

## 📖 Documentation

- [API Documentation](API.md)
- [Database Schema](DATABASE.md)
- [Development Progress](PROGRESS.md)
- [TODO List](TODO.md)



## Contribution Guide

1. Forks & PRs welcome!  
2. Use Issues for feature requests & bug reports.  
3. Only ingest **public and legally open data sources**.  
4. Do **not** store PII or illegal leak data.  

## Vision

This project aims to make **threat intelligence accessible for everyone**.  
A transparent, open, and free dashboard that helps organizations; no matter the size, to understand risks and react faster.
