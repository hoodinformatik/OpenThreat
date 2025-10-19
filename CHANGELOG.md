# Changelog

All notable changes to OpenThreat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **CISA KEV integration** via NVD API for tracking exploited vulnerabilities
  - Automatic daily updates at 09:00 UTC via Celery Beat
  - 1,442+ actively exploited CVEs tracked
  - Priority score boost for exploited vulnerabilities
  - New service: `backend/services/cisa_kev_service.py`
  - New task: `fetch_cisa_kev_task` in `backend/tasks/data_tasks.py`
  - Setup documentation: `docs/KEV_SETUP.md`
- BSI CERT-Bund integration for German security advisories
- LLM-powered vulnerability descriptions
- Priority scoring system
- Advanced search with multiple filters
- RSS/Atom feeds for monitoring
- Celery background tasks for data processing
- BSI advisories page in frontend

### Changed
- **Fixed stats API bug**: `exploited_vulnerabilities` now correctly counts exploited CVEs
  - Changed from `func.count().filter()` to `func.sum(case())` in SQLAlchemy
  - Stats endpoint now shows accurate exploitation data
- Migrated from old Data_Sample_Connectors to new service architecture
- Improved API documentation
- Updated frontend with modern UI components
- Consolidated startup scripts

### Removed
- Old connector scripts (Data_Sample_Connectors/)
- SQLite support (PostgreSQL only)
- Redundant documentation files from root
- Unused batch files

## [0.1.0] - 2025-10-16

### Added
- Initial release
- PostgreSQL database with 314,000+ CVEs
- FastAPI backend with REST API
- Next.js frontend with TailwindCSS
- CISA KEV integration
- NVD CVE database integration
- Docker Compose setup
- Basic search and filtering
- CVE detail pages
- Dashboard with statistics

### Security
- Environment variable configuration
- CORS protection
- SQL injection prevention via SQLAlchemy
- XSS prevention via React

---

## Version History

- **0.1.0** - Initial public release
- **Unreleased** - Current development version

---

## Upgrade Guide

### From 0.1.0 to Unreleased

1. **Database Migration**
```bash
alembic upgrade head
```

2. **Update Dependencies**
```bash
pip install -r requirements.txt
cd frontend && npm install
```

3. **Environment Variables**
Check `.env.example` for new required variables.

4. **Restart Services**
```bash
docker-compose down
docker-compose up -d
```

---

## Breaking Changes

### Unreleased
- Removed `Data_Sample_Connectors/` - Use new service architecture
- Removed SQLite support - PostgreSQL required
- Changed API endpoint structure for BSI integration

---

## Deprecations

### Unreleased
- Old connector scripts will be removed in next major version
- Legacy API endpoints (v1) will be deprecated

---

## Contributors

Thank you to all contributors who have helped make OpenThreat better!

- [@hoodinformatik](https://github.com/hoodinformatik) - Project Lead

---

For more details, see the [GitHub Releases](https://github.com/hoodinformatik/OpenThreat/releases) page.
