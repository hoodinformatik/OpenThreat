# 📦 Repository Guide - Was gehört ins Git Repo?

## ✅ Was SOLLTE ins Repo (Commit & Push)

### **Dokumentation**
- ✅ `README.md` - Projekt-Übersicht
- ✅ `CONTRIBUTING.md` - Contribution Guidelines
- ✅ `CHANGELOG.md` - Version History
- ✅ `LICENSE` - Open Source Lizenz
- ✅ `docs/` - Alle Dokumentation
  - `API.md`
  - `ARCHITECTURE.md`
  - `DATABASE.md`
  - `TESTING.md`
  - `MONITORING.md`
  - `DEPLOYMENT.md`
  - `SECURITY.md`
  - `BSI_INTEGRATION.md`

### **Code**
- ✅ `backend/` - Gesamter Backend-Code
- ✅ `frontend/` - Gesamter Frontend-Code
- ✅ `tests/` - Alle Tests
- ✅ `alembic/` - Database Migrations

### **Configuration (Templates)**
- ✅ `.env.example` - Environment Template
- ✅ `.env.production.example` - Production Template
- ✅ `docker-compose.yml` - Development Setup
- ✅ `docker-compose.prod.yml` - Production Setup
- ✅ `Dockerfile.prod` - Production Dockerfile
- ✅ `pytest.ini` - Test Configuration
- ✅ `requirements.txt` - Python Dependencies
- ✅ `requirements-test.txt` - Test Dependencies
- ✅ `alembic.ini` - Database Migration Config

### **Deployment**
- ✅ `nginx/nginx.conf` - Nginx Configuration
- ✅ `deploy.sh` - Deployment Script
- ✅ `start.bat` - Windows Start Script

### **Project Management**
- ✅ `.gitignore` - Git Ignore Rules
- ✅ `PROGRESS.md` - Development Progress (optional)
- ✅ `REFACTORING_PLAN.md` - Refactoring Roadmap (optional)

---

## ❌ Was NICHT ins Repo (Niemals committen!)

### **Secrets & Credentials**
- ❌ `.env` - Echte Environment Variables
- ❌ `.env.local` - Lokale Secrets
- ❌ `.env.production` - Production Secrets
- ❌ `*_api_key.txt` - API Keys
- ❌ `*_secret.txt` - Secret Files
- ❌ `*.pem` - Private Keys
- ❌ `*.key` - SSL Keys
- ❌ `*.crt` - Certificates (außer public)

### **Runtime Data**
- ❌ `*.log` - Log Files
- ❌ `logs/` - Log Directory
- ❌ `*.db` - SQLite Databases
- ❌ `*.sqlite` - SQLite Files
- ❌ `celerybeat-schedule` - Celery Schedule
- ❌ `nvd_checkpoint.txt` - Runtime Checkpoints

### **Generated Files**
- ❌ `__pycache__/` - Python Cache
- ❌ `*.pyc` - Compiled Python
- ❌ `.pytest_cache/` - Pytest Cache
- ❌ `htmlcov/` - Coverage Reports
- ❌ `.coverage` - Coverage Data
- ❌ `frontend/.next/` - Next.js Build
- ❌ `frontend/node_modules/` - NPM Packages

### **Development**
- ❌ `.vscode/` - VS Code Settings
- ❌ `.idea/` - IntelliJ Settings
- ❌ `venv/` - Virtual Environment
- ❌ `env/` - Virtual Environment

### **Production Data**
- ❌ `nginx/ssl/` - SSL Certificates
- ❌ `nginx/cache/` - Nginx Cache
- ❌ `backups/` - Database Backups
- ❌ `*.sql.gz` - Backup Files
- ❌ `prometheus_data/` - Monitoring Data
- ❌ `grafana_data/` - Dashboard Data

### **Personal Files**
- ❌ `*.csv` - Data Files
- ❌ `*.ndjson` - Data Files
- ❌ `out/` - Output Directory
- ❌ `tmp/` - Temporary Files
- ❌ `.DS_Store` - macOS Files
- ❌ `Thumbs.db` - Windows Files

---

## 🔍 Vor dem Commit prüfen

### **Checklist:**
```bash
# 1. Keine Secrets im Code?
git diff | grep -i "password\|secret\|api_key\|token"

# 2. .gitignore aktuell?
git status

# 3. Nur relevante Dateien?
git add -p  # Interaktiv hinzufügen

# 4. Sinnvolle Commit Message?
git commit -m "feat: Add production deployment configuration"
```

---

## 📋 Empfohlene Commit-Struktur

### **Commit Message Format:**
```
<type>: <subject>

<body>

<footer>
```

### **Types:**
- `feat:` - Neues Feature
- `fix:` - Bug Fix
- `docs:` - Dokumentation
- `style:` - Formatierung
- `refactor:` - Code Refactoring
- `test:` - Tests
- `chore:` - Maintenance

### **Beispiele:**
```bash
git commit -m "feat: Add Redis-based rate limiting"
git commit -m "docs: Update deployment guide with Hetzner setup"
git commit -m "fix: Resolve datetime parsing in test fixtures"
git commit -m "test: Add 64 comprehensive API tests"
git commit -m "chore: Update .gitignore for production files"
```

---

## 🚨 Wichtige Regeln

### **NIEMALS committen:**
1. ❌ Passwörter oder API Keys
2. ❌ Private SSL Certificates
3. ❌ Production Database Dumps
4. ❌ User Data oder PII
5. ❌ Large Binary Files (>10MB)

### **IMMER committen:**
1. ✅ Code Changes
2. ✅ Documentation Updates
3. ✅ Configuration Templates
4. ✅ Test Files
5. ✅ Migration Scripts

---

## 🔐 Secrets Management

### **Für Development:**
```bash
# .env.example (im Repo)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
API_KEY=your_api_key_here

# .env (NICHT im Repo)
DATABASE_URL=postgresql://real_user:real_pass@localhost:5432/openthreat
API_KEY=sk-1234567890abcdef
```

### **Für Production:**
```bash
# Secrets in Environment Variables (Server)
export DATABASE_URL="postgresql://..."
export API_KEY="sk-..."

# Oder Docker Secrets
docker secret create db_password /path/to/password.txt
```

---

## 📊 Repository Struktur (Clean)

```
OpenThreat/
├── .github/              # GitHub Actions (optional)
├── backend/              # Backend Code
├── frontend/             # Frontend Code
├── tests/                # Tests
├── docs/                 # Documentation
├── alembic/              # Migrations
├── nginx/
│   └── nginx.conf        # Nginx Config
├── .env.example          # Template
├── .gitignore            # Ignore Rules
├── docker-compose.yml    # Dev Setup
├── docker-compose.prod.yml
├── Dockerfile.prod
├── requirements.txt
├── pytest.ini
├── deploy.sh
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

---

## ✅ Quick Commands

### **Check before commit:**
```bash
# Was wird committed?
git status

# Diff anzeigen
git diff

# Nur bestimmte Dateien
git add backend/main.py
git add docs/DEPLOYMENT.md

# Commit
git commit -m "feat: Add deployment configuration"

# Push
git push origin main
```

### **Secrets aus History entfernen:**
```bash
# Falls versehentlich committed
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (VORSICHT!)
git push origin --force --all
```

---

## 🎯 Best Practices

1. **Kleine, fokussierte Commits**
   - Ein Feature/Fix pro Commit
   - Klare Commit Messages

2. **Branch Strategy**
   - `main` - Production
   - `develop` - Development
   - `feature/*` - Features
   - `fix/*` - Bug Fixes

3. **Pull Requests**
   - Code Review vor Merge
   - Tests müssen passen
   - Documentation aktualisiert

4. **Tags für Releases**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

---

## 📧 Fragen?

Bei Unsicherheiten:
- Prüfe `.gitignore`
- Frage im Team
- Lieber nicht committen als Secrets leaken!

**Email:** hoodinformatik@gmail.com
**GitHub:** https://github.com/hoodinformatik/OpenThreat
