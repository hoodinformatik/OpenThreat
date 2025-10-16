# 📦 Repository Guide - What Belongs in Git?

## ✅ What SHOULD be in the Repo (Commit & Push)

### **Documentation**
- ✅ `README.md` - Project overview
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `CHANGELOG.md` - Version history
- ✅ `LICENSE` - Open source license
- ✅ `docs/` - All documentation
  - `API.md`
  - `ARCHITECTURE.md`
  - `DATABASE.md`
  - `TESTING.md`
  - `MONITORING.md`
  - `DEPLOYMENT.md`
  - `SECURITY.md`
  - `BSI_INTEGRATION.md`

### **Code**
- ✅ `backend/` - All backend code
- ✅ `frontend/` - All frontend code
- ✅ `tests/` - All tests
- ✅ `alembic/` - Database migrations

### **Configuration (Templates)**
- ✅ `.env.example` - Environment template
- ✅ `.env.production.example` - Production template
- ✅ `docker-compose.yml` - Development setup
- ✅ `docker-compose.prod.yml` - Production setup
- ✅ `Dockerfile.prod` - Production Dockerfile
- ✅ `pytest.ini` - Test configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `requirements-test.txt` - Test dependencies
- ✅ `alembic.ini` - Database migration config

### **Deployment**
- ✅ `nginx/nginx.conf` - Nginx configuration
- ✅ `deploy.sh` - Deployment script
- ✅ `start.bat` - Windows start script

### **Project Management**
- ✅ `.gitignore` - Git ignore rules
- ✅ `PROGRESS.md` - Development progress (optional)
- ✅ `REFACTORING_PLAN.md` - Refactoring roadmap (optional)

---

## ❌ What NOT to Put in Repo (Never Commit!)

### **Secrets & Credentials**
- ❌ `.env` - Real environment variables
- ❌ `.env.local` - Local secrets
- ❌ `.env.production` - Production secrets
- ❌ `*_api_key.txt` - API keys
- ❌ `*_secret.txt` - Secret files
- ❌ `*.pem` - Private keys
- ❌ `*.key` - SSL keys
- ❌ `*.crt` - Certificates (except public)

### **Runtime Data**
- ❌ `*.log` - Log files
- ❌ `logs/` - Log directory
- ❌ `*.db` - SQLite databases
- ❌ `*.sqlite` - SQLite files
- ❌ `celerybeat-schedule` - Celery schedule
- ❌ `nvd_checkpoint.txt` - Runtime checkpoints

### **Generated Files**
- ❌ `__pycache__/` - Python cache
- ❌ `*.pyc` - Compiled Python
- ❌ `.pytest_cache/` - Pytest cache
- ❌ `htmlcov/` - Coverage reports
- ❌ `.coverage` - Coverage data
- ❌ `frontend/.next/` - Next.js build
- ❌ `frontend/node_modules/` - NPM packages

### **Development**
- ❌ `.vscode/` - VS Code settings
- ❌ `.idea/` - IntelliJ settings
- ❌ `venv/` - Virtual environment
- ❌ `env/` - Virtual environment

### **Production Data**
- ❌ `nginx/ssl/` - SSL certificates
- ❌ `nginx/cache/` - Nginx cache
- ❌ `backups/` - Database backups
- ❌ `*.sql.gz` - Backup files
- ❌ `prometheus_data/` - Monitoring data
- ❌ `grafana_data/` - Dashboard data

### **Personal Files**
- ❌ `*.csv` - Data files
- ❌ `*.ndjson` - Data files
- ❌ `out/` - Output directory
- ❌ `tmp/` - Temporary files
- ❌ `.DS_Store` - macOS files
- ❌ `Thumbs.db` - Windows files

---

## 🔍 Check Before Commit

### **Checklist:**
```bash
# 1. No secrets in code?
git diff | grep -i "password\|secret\|api_key\|token"

# 2. .gitignore up to date?
git status

# 3. Only relevant files?
git add -p  # Interactive add

# 4. Meaningful commit message?
git commit -m "feat: Add production deployment configuration"
```

---

## 📋 Recommended Commit Structure

### **Commit Message Format:**
```
<type>: <subject>

<body>

<footer>
```

### **Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance

### **Examples:**
```bash
git commit -m "feat: Add Redis-based rate limiting"
git commit -m "docs: Update deployment guide with Hetzner setup"
git commit -m "fix: Resolve datetime parsing in test fixtures"
git commit -m "test: Add 64 comprehensive API tests"
git commit -m "chore: Update .gitignore for production files"
```

---

## 🚨 Important Rules

### **NEVER commit:**
1. ❌ Passwords or API keys
2. ❌ Private SSL certificates
3. ❌ Production database dumps
4. ❌ User data or PII
5. ❌ Large binary files (>10MB)

### **ALWAYS commit:**
1. ✅ Code changes
2. ✅ Documentation updates
3. ✅ Configuration templates
4. ✅ Test files
5. ✅ Migration scripts

---

## 🔐 Secrets Management

### **For Development:**
```bash
# .env.example (in repo)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
API_KEY=your_api_key_here

# .env (NOT in repo)
DATABASE_URL=postgresql://real_user:real_pass@localhost:5432/openthreat
API_KEY=sk-1234567890abcdef
```

### **For Production:**
```bash
# Secrets in environment variables (server)
export DATABASE_URL="postgresql://..."
export API_KEY="sk-..."

# Or Docker secrets
docker secret create db_password /path/to/password.txt
```

---

## 📊 Repository Structure (Clean)

```
OpenThreat/
├── .github/              # GitHub Actions (optional)
├── backend/              # Backend code
├── frontend/             # Frontend code
├── tests/                # Tests
├── docs/                 # Documentation
├── alembic/              # Migrations
├── nginx/
│   └── nginx.conf        # Nginx config
├── .env.example          # Template
├── .gitignore            # Ignore rules
├── docker-compose.yml    # Dev setup
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
# What will be committed?
git status

# Show diff
git diff

# Only specific files
git add backend/main.py
git add docs/DEPLOYMENT.md

# Commit
git commit -m "feat: Add deployment configuration"

# Push
git push origin main
```

### **Remove secrets from history:**
```bash
# If accidentally committed
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (CAUTION!)
git push origin --force --all
```

---

## 🎯 Best Practices

1. **Small, focused commits**
   - One feature/fix per commit
   - Clear commit messages

2. **Branch strategy**
   - `main` - Production
   - `develop` - Development
   - `feature/*` - Features
   - `fix/*` - Bug fixes

3. **Pull requests**
   - Code review before merge
   - Tests must pass
   - Documentation updated

4. **Tags for releases**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

---

## 📧 Questions?

If unsure:
- Check `.gitignore`
- Ask in team
- Better not commit than leak secrets!

**Email:** hoodinformatik@gmail.com
**GitHub:** https://github.com/hoodinformatik/OpenThreat
