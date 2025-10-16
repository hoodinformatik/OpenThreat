# 🚀 CI/CD Setup Guide

## Übersicht

OpenThreat nutzt GitHub Actions für:
- ✅ Automatische Tests bei jedem Push
- ✅ Code Quality Checks
- ✅ Security Scanning
- ✅ Automatisches Deployment

---

## 📋 Workflows

### 1. **CI Pipeline** (`ci.yml`)
Läuft bei jedem Push/PR auf `main` oder `develop`

**Was wird getestet:**
- ✅ Python Tests (pytest)
- ✅ Code Coverage (>50%)
- ✅ Linting (flake8, black, isort)
- ✅ Security Scan (Trivy)
- ✅ Docker Build

**Dauer:** ~5-10 Minuten

### 2. **Deploy Pipeline** (`deploy.yml`)
Läuft bei Push auf `main` oder manuell

**Was passiert:**
- ✅ SSH zum Server
- ✅ Git Pull
- ✅ Docker Rebuild
- ✅ Database Migration
- ✅ Health Check

**Dauer:** ~3-5 Minuten

---

## 🔧 Setup auf GitHub

### Schritt 1: Repository Secrets einrichten

Gehe zu: **Settings → Secrets and variables → Actions**

Erstelle folgende Secrets:

| Secret Name | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `SSH_PRIVATE_KEY` | Private SSH Key für Server | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_IP` | Server IP Adresse | `123.45.67.89` |
| `SERVER_USER` | SSH Username | `openthreat` |

---

### Schritt 2: SSH Key generieren

Auf deinem **lokalen Computer**:

```bash
# SSH Key generieren
ssh-keygen -t ed25519 -C "github-actions@openthreat.io" -f ~/.ssh/openthreat_deploy

# Public Key auf Server kopieren
ssh-copy-id -i ~/.ssh/openthreat_deploy.pub openthreat@your-server-ip

# Private Key anzeigen (für GitHub Secret)
cat ~/.ssh/openthreat_deploy
```

**Kopiere den gesamten Private Key** (inkl. `-----BEGIN` und `-----END`) in GitHub Secret `SSH_PRIVATE_KEY`

---

### Schritt 3: Server vorbereiten

Auf dem **Server**:

```bash
# User erstellen
sudo adduser openthreat
sudo usermod -aG docker openthreat

# Repository clonen
su - openthreat
git clone https://github.com/hoodinformatik/OpenThreat.git
cd OpenThreat

# .env erstellen
cp .env.production.example .env
nano .env  # Passwörter eintragen

# Erster Deploy (manuell)
docker-compose -f docker-compose.prod.yml up -d
```

---

### Schritt 4: GitHub Actions aktivieren

1. **Push Code zu GitHub:**
```bash
git add .
git commit -m "feat: Add CI/CD pipeline"
git push origin main
```

2. **Workflow läuft automatisch**
   - Gehe zu: **Actions** Tab auf GitHub
   - Sieh den Workflow laufen

3. **Badge im README** (optional):
```markdown
![CI/CD](https://github.com/hoodinformatik/OpenThreat/workflows/CI%2FCD%20Pipeline/badge.svg)
```

---

## 🔍 Workflow Details

### CI Pipeline (ci.yml)

```yaml
jobs:
  test:
    - Setup Python 3.13
    - Install dependencies
    - Run flake8, black, isort
    - Run pytest with coverage
    - Upload to Codecov
  
  security:
    - Run Trivy security scan
    - Upload to GitHub Security
  
  build:
    - Build Docker images
    - Cache layers
```

### Deploy Pipeline (deploy.yml)

```yaml
jobs:
  deploy:
    - SSH to server
    - Git pull
    - Docker compose down
    - Docker compose build
    - Docker compose up
    - Run migrations
    - Health check
```

---

## 🎯 Verwendung

### Automatisches Deployment

**Bei jedem Push auf `main`:**
```bash
git add .
git commit -m "feat: New feature"
git push origin main
# → Deployment läuft automatisch
```

### Manuelles Deployment

1. Gehe zu **Actions** Tab
2. Wähle **Deploy to Production**
3. Klicke **Run workflow**
4. Wähle Branch (z.B. `main`)
5. Klicke **Run workflow**

### Deployment mit Tag

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
# → Deployment läuft automatisch
```

---

## 🛡️ Security Best Practices

### ✅ DO:
- ✅ Secrets in GitHub Secrets speichern
- ✅ SSH Keys mit Passphrase schützen
- ✅ Regelmäßig Keys rotieren
- ✅ Nur notwendige Permissions

### ❌ DON'T:
- ❌ Secrets im Code committen
- ❌ Private Keys teilen
- ❌ Root User für Deployment
- ❌ Passwörter in Logs

---

## 📊 Monitoring

### GitHub Actions Logs

**Logs anzeigen:**
1. Gehe zu **Actions** Tab
2. Klicke auf Workflow Run
3. Klicke auf Job
4. Sieh detaillierte Logs

### Server Logs

```bash
# SSH zum Server
ssh openthreat@your-server-ip

# Docker Logs
cd OpenThreat
docker-compose -f docker-compose.prod.yml logs -f

# Nur Backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Letzte 100 Zeilen
docker-compose -f docker-compose.prod.yml logs --tail=100
```

---

## 🔧 Troubleshooting

### Problem: SSH Connection Failed

**Lösung:**
```bash
# Auf lokalem Computer
ssh -i ~/.ssh/openthreat_deploy openthreat@your-server-ip

# Wenn das funktioniert, ist der Key OK
# Wenn nicht, prüfe:
chmod 600 ~/.ssh/openthreat_deploy
```

### Problem: Docker Build Failed

**Lösung:**
```bash
# Auf Server
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Problem: Health Check Failed

**Lösung:**
```bash
# Prüfe ob Backend läuft
curl http://localhost/health

# Prüfe Docker Status
docker-compose -f docker-compose.prod.yml ps

# Prüfe Logs
docker-compose -f docker-compose.prod.yml logs backend
```

### Problem: Tests schlagen fehl

**Lösung:**
```bash
# Lokal testen
pytest tests/ -v

# Bestimmten Test
pytest tests/test_api_vulnerabilities.py -v

# Mit Coverage
pytest --cov=backend
```

---

## 🚀 Advanced: Multi-Environment

### Environments einrichten

**GitHub Settings → Environments:**

1. **staging**
   - Branch: `develop`
   - URL: `https://staging.openthreat.io`

2. **production**
   - Branch: `main`
   - URL: `https://openthreat.io`
   - Protection: Require approval

### Workflow anpassen

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    environment: staging
    # ...

  deploy-production:
    if: github.ref == 'refs/heads/main'
    environment: production
    # ...
```

---

## 📈 Performance Optimierung

### Docker Layer Caching

```yaml
- name: Build backend
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Parallel Jobs

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: [3.11, 3.12, 3.13]
```

---

## ✅ Checklist

### Vor dem ersten Deployment:

- [ ] GitHub Secrets eingerichtet
- [ ] SSH Key auf Server
- [ ] Server vorbereitet
- [ ] `.env` auf Server konfiguriert
- [ ] Erster manueller Deploy erfolgreich
- [ ] Health Check funktioniert

### Nach jedem Deployment:

- [ ] Health Check passed
- [ ] Logs prüfen
- [ ] Frontend erreichbar
- [ ] API funktioniert
- [ ] Database Migration erfolgreich

---

## 📧 Support

Bei Problemen:
- **GitHub Issues:** https://github.com/hoodinformatik/OpenThreat/issues
- **Email:** hoodinformatik@gmail.com

---

## 🎉 Fertig!

**Dein CI/CD Pipeline ist bereit!**

Jeder Push auf `main` wird automatisch:
- ✅ Getestet
- ✅ Gescannt
- ✅ Deployed
- ✅ Verifiziert

**Happy Deploying! 🚀**
