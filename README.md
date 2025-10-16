<div align="center">

# 🛡️ OpenThreat

**Democratizing Threat Intelligence**

A free and open-source platform for tracking CVEs and security threats

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)](https://www.postgresql.org/)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 Mission

OpenThreat makes threat intelligence accessible to everyone - from security professionals to small businesses and non-profits. We aggregate vulnerability data from trusted public sources into a clear, actionable interface.

## ✨ Features

### 📊 Data & Intelligence
- **314,000+ CVEs** from NVD, CISA KEV, and BSI CERT-Bund
- **1,436 exploited vulnerabilities** actively tracked
- **Priority scoring** algorithm (exploitation + CVSS + recency)
- **LLM-powered descriptions** for better understanding
- **German security advisories** from BSI CERT-Bund

### 🔍 Search & Discovery
- **Advanced search** with multiple filters
- **Full-text search** across all vulnerability data
- **Filter by severity**, vendor, product, CWE, CVSS score
- **Date range filtering** for recent threats

### 🚀 Integration & Automation
- **REST API** with 20+ endpoints
- **RSS/Atom feeds** for monitoring
- **Background tasks** with Celery
- **Automatic data updates** from multiple sources

### 💻 User Experience
- **Modern web interface** built with Next.js
- **Real-time statistics** dashboard
- **Detailed CVE pages** with actionable insights
- **Responsive design** for mobile and desktop

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Python 3.13+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)

### One-Command Start

**Windows:**
```bash
.\start.bat
```

**Manual Setup:**

1. **Clone the repository**
```bash
git clone https://github.com/hoodinformatik/OpenThreat.git
cd OpenThreat
```

2. **Start infrastructure**
```bash
docker-compose up -d
```

3. **Set up backend**
```bash
pip install -r requirements.txt
alembic upgrade head
python scripts/fetch_nvd_complete.py
python -m uvicorn backend.main:app --reload --port 8001
```

4. **Start frontend**
```bash
cd frontend
npm install
npm run dev
```

5. **Access the application**
- 🌐 **Frontend**: http://localhost:3000
- 📚 **API Docs**: http://localhost:8001/docs
- 🔌 **API**: http://localhost:8001

## 📊 Data Sources

We aggregate data from trusted public sources:

| Source | Description | Update Frequency |
|--------|-------------|------------------|
| [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | Known Exploited Vulnerabilities | Daily |
| [NVD](https://nvd.nist.gov/) | National Vulnerability Database | Every 2 hours |
| [BSI CERT-Bund](https://wid.cert-bund.de/) | German Security Advisories | Daily |  

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│           Frontend (Next.js 14)              │
│     Modern UI with TailwindCSS               │
│            Port 3000                         │
└────────────────┬─────────────────────────────┘
                 │ REST API
                 ▼
┌──────────────────────────────────────────────┐
│        Backend API (FastAPI)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   API    │  │  Celery  │  │   LLM    │  │
│  │Endpoints │  │  Tasks   │  │ Service  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│            Port 8001                         │
└────────────────┬─────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │    Redis     │
│   Port 5432  │  │   Port 6379  │
└──────────────┘  └──────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 📖 Documentation

- [API Documentation](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DATABASE.md)
- [BSI Integration](docs/BSI_INTEGRATION.md)
- [Security](docs/SECURITY.md)
- [Development Progress](PROGRESS.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick Links:**
- [Report a Bug](https://github.com/hoodinformatik/OpenThreat/issues/new?labels=bug)
- [Request a Feature](https://github.com/hoodinformatik/OpenThreat/issues/new?labels=enhancement)
- [View Changelog](CHANGELOG.md)

## 📧 Contact

- **Email**: hoodinformatik@gmail.com
- **GitHub**: [@hoodinformatik](https://github.com/hoodinformatik)

## 📜 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## 🌟 Star History

If you find OpenThreat useful, please consider giving it a star! ⭐

---

<div align="center">

**Made with ❤️ for the security community**

[Report Bug](https://github.com/hoodinformatik/OpenThreat/issues) • [Request Feature](https://github.com/hoodinformatik/OpenThreat/issues) • [Documentation](docs/)

</div>
