# 🔧 OpenThreat Refactoring Plan

**Ziel:** Professionelles, produktionsreifes Open-Source-Projekt

---

## 📋 Phase 1: Dateien aufräumen

### ❌ Zu entfernen:

#### Root-Level Dateien:
- [ ] `celerybeat-schedule` - Runtime-Datei (gehört in .gitignore)
- [ ] `nvd_fetch.log` - Log-Datei (gehört in .gitignore)
- [ ] `known_exploited_vulnerabilities.csv` - Daten-Datei (gehört in .gitignore)
- [ ] `start-*.bat` - Alle BAT-Dateien (durch ein einziges `start.bat` ersetzen)
- [ ] `stop.bat` - In neues Start-Script integrieren

#### Alte Dokumentation (Root):
- [ ] `API.md` → verschieben nach `docs/`
- [ ] `DATABASE.md` → verschieben nach `docs/`
- [ ] `CELERY.md` → verschieben nach `docs/`
- [ ] `LLM.md` → verschieben nach `docs/`
- [ ] `QUICKSTART.md` → mit README.md mergen
- [ ] `QUICKSTART_LLM.md` → mit docs/LLM.md mergen
- [ ] `TODO.md` → GitHub Issues verwenden stattdessen

#### Alte Connectors:
- [ ] `Data_Sample_Connectors/` - Komplett entfernen (veraltet)
- [ ] `ingestion/` - Prüfen ob noch verwendet
- [ ] `normalizer/` - Prüfen ob noch verwendet

#### Scripts aufräumen:
- [ ] `scripts/setup_sqlite.py` - SQLite nicht mehr verwendet
- [ ] `scripts/query_db.py` - Nur für Development, dokumentieren

---

## 📁 Phase 2: Neue Struktur

```
OpenThreat/
├── .github/
│   ├── workflows/           # CI/CD
│   └── ISSUE_TEMPLATE/      # Issue Templates
├── backend/
│   ├── api/                 # API Endpoints
│   ├── models/              # Database Models
│   ├── services/            # Business Logic
│   ├── tasks/               # Celery Tasks
│   └── utils/               # Utilities
├── frontend/
│   ├── app/                 # Next.js Pages
│   ├── components/          # React Components
│   └── lib/                 # Utilities
├── docs/
│   ├── API.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md        # NEU
│   ├── DEVELOPMENT.md       # NEU
│   ├── ARCHITECTURE.md      # NEU
│   └── CONTRIBUTING.md      # NEU
├── scripts/
│   ├── fetch_nvd_complete.py
│   ├── fetch_bsi_cert.py
│   └── setup_db.py
├── tests/                   # NEU - Unit Tests
│   ├── backend/
│   └── frontend/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.prod.yml  # NEU
├── LICENSE
├── README.md
└── requirements.txt
```

---

## 🔧 Phase 3: Code-Optimierungen

### Backend:

#### 1. Models optimieren
- [ ] Indizes überprüfen und optimieren
- [ ] Relationships cleanup
- [ ] Constraints hinzufügen

#### 2. API Endpoints
- [ ] Konsistente Error Responses
- [ ] Rate Limiting hinzufügen
- [ ] API Versioning sauber implementieren
- [ ] OpenAPI/Swagger Docs verbessern

#### 3. Services
- [ ] Error Handling standardisieren
- [ ] Logging verbessern
- [ ] Retry-Logic für externe APIs
- [ ] Caching optimieren

#### 4. Tasks (Celery)
- [ ] Task-Namen standardisieren
- [ ] Error Handling verbessern
- [ ] Monitoring hinzufügen
- [ ] Dead Letter Queue

### Frontend:

#### 1. Components
- [ ] Unused Components entfernen
- [ ] Component Library dokumentieren
- [ ] Loading States standardisieren
- [ ] Error Boundaries hinzufügen

#### 2. API Client
- [ ] Error Handling verbessern
- [ ] Retry-Logic
- [ ] Request Cancellation
- [ ] Type Safety überprüfen

#### 3. Performance
- [ ] Code Splitting
- [ ] Image Optimization
- [ ] Bundle Size analysieren

---

## 🔒 Phase 4: Security & Best Practices

### Security:
- [ ] Environment Variables Review
- [ ] SQL Injection Prevention (bereits durch SQLAlchemy)
- [ ] XSS Prevention (bereits durch React)
- [ ] CORS Configuration überprüfen
- [ ] Rate Limiting
- [ ] Input Validation

### Best Practices:
- [ ] Logging Strategy
- [ ] Error Handling Strategy
- [ ] Testing Strategy
- [ ] Monitoring Strategy

---

## 📚 Phase 5: Dokumentation

### Neue Dokumentation:
- [ ] `CONTRIBUTING.md` - Contribution Guidelines
- [ ] `ARCHITECTURE.md` - System Architecture
- [ ] `DEPLOYMENT.md` - Production Deployment
- [ ] `DEVELOPMENT.md` - Development Setup
- [ ] `CHANGELOG.md` - Version History

### Verbesserte Dokumentation:
- [ ] README.md - Professioneller, kürzer
- [ ] API.md - OpenAPI/Swagger Integration
- [ ] DATABASE.md - ER-Diagramm hinzufügen

---

## 🐳 Phase 6: Deployment

### Docker:
- [ ] Multi-stage Builds
- [ ] Production Dockerfile
- [ ] docker-compose.prod.yml
- [ ] Health Checks
- [ ] Resource Limits

### CI/CD:
- [ ] GitHub Actions Workflows
  - [ ] Tests
  - [ ] Linting
  - [ ] Build
  - [ ] Deploy

---

## 🧪 Phase 7: Testing

### Backend Tests:
- [ ] Unit Tests für Services
- [ ] Integration Tests für API
- [ ] Database Tests

### Frontend Tests:
- [ ] Component Tests
- [ ] Integration Tests
- [ ] E2E Tests (optional)

---

## 📊 Phase 8: Monitoring & Observability

### Logging:
- [ ] Structured Logging
- [ ] Log Levels korrekt
- [ ] Sensitive Data Filtering

### Metrics:
- [ ] API Response Times
- [ ] Database Query Performance
- [ ] Celery Task Metrics

### Health Checks:
- [ ] Database Health
- [ ] Redis Health
- [ ] External API Health

---

## 🎯 Prioritäten

### 🔴 Kritisch (Sofort):
1. Runtime-Dateien aus Git entfernen
2. Alte Connectors entfernen
3. Dokumentation aufräumen
4. .gitignore aktualisieren

### 🟡 Wichtig (Diese Woche):
5. Code-Optimierungen
6. Error Handling
7. Logging verbessern
8. Tests hinzufügen

### 🟢 Nice-to-have (Später):
9. CI/CD Pipeline
10. Monitoring
11. Performance Optimierung

---

## 📝 Nächste Schritte

1. **Backup erstellen** (Git commit)
2. **Phase 1 durchführen** (Dateien aufräumen)
3. **Phase 2 durchführen** (Struktur)
4. **Phase 3 durchführen** (Code)
5. **Testen**
6. **Dokumentieren**

---

**Geschätzte Zeit:** 2-3 Tage
**Risiko:** Mittel (Breaking Changes möglich)
**Benefit:** Professionelles, wartbares Projekt
