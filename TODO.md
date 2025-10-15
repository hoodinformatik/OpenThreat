# Development Plan & TODOs

## Phase 0 — Repo Setup
- [✅] LICENSE (Apache-2.0 or AGPLv3)  
- [ ] GitHub Actions
- [ ] Docker Compose (db, api, frontend, worker, scheduler)

## Phase 1 — Data Aggregation
- [✅] CISA KEV Connector  
- [✅] NVD Connector (incremental updates)  
- [ CVE Connector
- [✅] MITRE ATT&CK Connector  
- [ ] abuse.ch URLhaus Connector  
- [ ] Pydantic Schemas: Vulnerability, IOC, Technique  
- [ ] Deduplication & normalization logic

## Phase 2 — Database & Updates
- [ ] DB schema (tables: vulnerabilities, iocs, ingestion_runs)  
- [ ] Alembic migrations  
- [ ] Indices for search (GIN/Trigram)  
- [ ] Scheduler: 2h updates (Celery/cron)  
- [ ] Monitoring & health endpoints

## Phase 3 — Prioritization & Explanations
- [ ] Priority score formula (exploited, CVSS, recency)  
- [ ] Plain-language templates (What it means, What to do)  
- [ ] Localization (de/en)

## Phase 4 — API (FastAPI)
- [ ] Endpoints: `/vulnerabilities`, `/iocs`, `/attck`, `/search`, `/stats`  
- [ ] RSS/Atom Feeds  
- [ ] Pagination, CORS, rate-limiting  
- [ ] OpenAPI Docs + tests

## Phase 5 — Frontend (Next.js)
- [ ] Dashboard: KPIs, Top Exploited  
- [ ] Vulnerabilities list & detail views  
- [ ] IOC list & detail views  
- [ ] ATT&CK browser (basic)  
- [ ] Search & filter UI  
- [ ] About/Methodology/Legal pages

---

## Definition of Done (MVP)
- [ ] All 4 data sources ingest successfully (daily at minimum)  
- [ ] DB populated with consistent schema & indices  
- [ ] Priority score available in API  
- [ ] RSS/Atom feeds for Top Exploited available  
- [ ] Frontend with list + detail + search  
- [ ] Documentation: README, architecture diagram, API reference  


