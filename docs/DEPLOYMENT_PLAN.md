# OpenThreat Deployment & CI/CD Plan

## 🎯 Ziel

Professionelles Deployment auf AWS mit:
- ✅ Automatische Deployments via CI/CD
- ✅ Saubere Entwicklungs-Workflows
- ✅ Production-ready Setup
- ✅ Monitoring & Logging
- ✅ Skalierbarkeit

---

## 📋 Deployment-Optionen (Empfehlung nach Komplexität)

### Option 1: AWS Lightsail (Einfachste) ⭐ **EMPFOHLEN FÜR START**

**Vorteile:**
- ✅ Sehr einfach zu starten
- ✅ Fester monatlicher Preis ($10-40/Monat)
- ✅ Managed Database & Container
- ✅ Automatische Backups
- ✅ Perfekt für MVP/kleine Projekte

**Nachteile:**
- ❌ Weniger Skalierbarkeit
- ❌ Weniger Kontrolle

**Kosten:** ~$20-40/Monat
- Container Service: $10/Monat (512MB RAM, 0.25 vCPU)
- Database: $15/Monat (1GB RAM)
- Storage: $5/Monat

---

### Option 2: AWS EC2 (Mittlere Komplexität) ⭐ **EMPFOHLEN FÜR WACHSTUM**

**Vorteile:**
- ✅ Volle Kontrolle
- ✅ Docker Compose einfach nutzbar
- ✅ Gute Balance zwischen Einfachheit und Flexibilität
- ✅ Einfaches Upgrade möglich

**Nachteile:**
- ❌ Manuelle Server-Verwaltung
- ❌ Selbst für Updates verantwortlich

**Kosten:** ~$30-60/Monat
- EC2 t3.medium: $30/Monat (2 vCPU, 4GB RAM)
- RDS PostgreSQL: $20/Monat (db.t3.micro)
- Storage: $10/Monat

---

### Option 3: AWS ECS + Fargate (Professionell) ⭐ **EMPFOHLEN FÜR SCALE**

**Vorteile:**
- ✅ Vollständig managed
- ✅ Auto-Scaling
- ✅ High Availability
- ✅ Production-grade

**Nachteile:**
- ❌ Komplexer Setup
- ❌ Höhere Kosten
- ❌ Mehr AWS-Kenntnisse nötig

**Kosten:** ~$80-150/Monat
- Fargate Tasks: $50/Monat
- RDS PostgreSQL: $30/Monat
- Load Balancer: $20/Monat
- ElastiCache Redis: $15/Monat

---

### Option 4: Kubernetes (EKS) (Sehr komplex)

**Nur wenn:**
- Du sehr große Skalierung brauchst (>100k users)
- Du bereits K8s-Erfahrung hast
- Du ein DevOps-Team hast

**Kosten:** $150+/Monat

---

## 🚀 Empfohlener Weg: Stufenweise Migration

### Phase 1: Start mit AWS Lightsail (Jetzt)
- Schnell live gehen
- Kosten niedrig halten
- Lernen und iterieren

### Phase 2: Migration zu EC2 (Bei Wachstum)
- Mehr Kontrolle
- Bessere Performance
- Immer noch überschaubar

### Phase 3: Migration zu ECS (Bei Scale)
- Auto-Scaling
- High Availability
- Production-grade

---

## 📦 Deployment-Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────┐
│                     AWS Cloud                            │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │              Load Balancer (ALB)               │    │
│  │         https://openthreat.yourdomain.com      │    │
│  └───────────────────┬────────────────────────────┘    │
│                      │                                   │
│         ┌────────────┴────────────┐                     │
│         ▼                         ▼                     │
│  ┌─────────────┐          ┌─────────────┐             │
│  │  Frontend   │          │  Backend    │             │
│  │  (Next.js)  │          │  (FastAPI)  │             │
│  │  Container  │          │  Container  │             │
│  └─────────────┘          └──────┬──────┘             │
│                                   │                     │
│         ┌─────────────────────────┼──────────┐         │
│         ▼                         ▼          ▼         │
│  ┌─────────────┐          ┌──────────┐  ┌──────────┐ │
│  │  Celery     │          │PostgreSQL│  │  Redis   │ │
│  │  Worker     │          │   (RDS)  │  │(ElastiC.)│ │
│  │  Container  │          └──────────┘  └──────────┘ │
│  └─────────────┘                                       │
│         │                                              │
│         ▼                                              │
│  ┌─────────────┐                                      │
│  │   Ollama    │                                      │
│  │  (Optional) │                                      │
│  └─────────────┘                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

### Workflow

```
Developer Push → GitHub → CI/CD Pipeline → AWS Deployment
     ↓              ↓            ↓              ↓
   Code         Tests       Build Docker    Deploy
  Changes      (pytest)      Images        Containers
```

### Branches & Environments

```
main (production)     → Deploys to: production.openthreat.com
├── staging           → Deploys to: staging.openthreat.com
└── develop           → Deploys to: dev.openthreat.com (optional)
```

### Pipeline Steps

**1. On Push to `develop`:**
- ✅ Run linting (flake8, eslint)
- ✅ Run tests (pytest, jest)
- ✅ Build Docker images
- ✅ Deploy to dev environment

**2. On Pull Request to `staging`:**
- ✅ Run all tests
- ✅ Code review required
- ✅ Preview deployment

**3. On Merge to `staging`:**
- ✅ Deploy to staging
- ✅ Run integration tests
- ✅ Manual approval required for production

**4. On Merge to `main`:**
- ✅ Deploy to production
- ✅ Run smoke tests
- ✅ Automatic rollback on failure

---

## 🐳 Docker Setup

### Production Docker Compose

```yaml
version: '3.8'

services:
  frontend:
    image: ghcr.io/yourusername/openthreat-frontend:latest
    environment:
      - NEXT_PUBLIC_API_URL=https://api.openthreat.com
    restart: always
    
  backend:
    image: ghcr.io/yourusername/openthreat-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - NVD_API_KEY=${NVD_API_KEY}
    restart: always
    
  celery-worker:
    image: ghcr.io/yourusername/openthreat-backend:latest
    command: celery -A backend.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    restart: always
    
  celery-beat:
    image: ghcr.io/yourusername/openthreat-backend:latest
    command: celery -A backend.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    restart: always
```

---

## 🔐 Secrets Management

### Development (Local)
```
.env (gitignored)
```

### Staging/Production (AWS)
```
AWS Secrets Manager
├── openthreat/staging/database-url
├── openthreat/staging/nvd-api-key
├── openthreat/staging/redis-url
└── openthreat/production/...
```

### GitHub Actions
```
GitHub Secrets
├── AWS_ACCESS_KEY_ID
├── AWS_SECRET_ACCESS_KEY
├── DOCKER_USERNAME
└── DOCKER_PASSWORD
```

---

## 📊 Monitoring & Logging

### Application Monitoring

**Option 1: AWS CloudWatch (Einfach)**
- Logs von allen Containern
- Metriken (CPU, RAM, Network)
- Alarms bei Fehlern

**Option 2: Datadog/New Relic (Professionell)**
- APM (Application Performance Monitoring)
- Distributed Tracing
- Custom Dashboards

### Error Tracking

**Sentry**
- Automatic error capture
- Stack traces
- User impact tracking
- Slack/Email notifications

### Uptime Monitoring

**UptimeRobot / Pingdom**
- Check every 5 minutes
- Alert on downtime
- Status page

---

## 💰 Kosten-Übersicht

### Lightsail Setup (Empfohlen für Start)

| Service | Specs | Kosten/Monat |
|---------|-------|--------------|
| Container Service | 512MB RAM, 0.25 vCPU | $10 |
| Managed Database | PostgreSQL, 1GB RAM | $15 |
| Storage | 20GB SSD | $5 |
| **Total** | | **~$30/Monat** |

### EC2 Setup (Bei Wachstum)

| Service | Specs | Kosten/Monat |
|---------|-------|--------------|
| EC2 Instance | t3.medium (2 vCPU, 4GB) | $30 |
| RDS PostgreSQL | db.t3.micro | $20 |
| ElastiCache Redis | cache.t3.micro | $15 |
| Storage | 50GB SSD | $5 |
| **Total** | | **~$70/Monat** |

### ECS Setup (Production Scale)

| Service | Specs | Kosten/Monat |
|---------|-------|--------------|
| Fargate Tasks | 4 tasks @ 0.5 vCPU, 1GB | $50 |
| RDS PostgreSQL | db.t3.small | $30 |
| ElastiCache Redis | cache.t3.small | $25 |
| Application Load Balancer | | $20 |
| CloudWatch Logs | 10GB/month | $5 |
| **Total** | | **~$130/Monat** |

---

## 🛠️ Implementierungs-Schritte

### Phase 1: Vorbereitung (1-2 Tage)

**1.1 Docker Production Setup**
- [ ] Dockerfile für Frontend optimieren
- [ ] Dockerfile für Backend optimieren
- [ ] docker-compose.prod.yml erstellen
- [ ] Health checks implementieren

**1.2 Environment Management**
- [ ] .env.example aktualisieren
- [ ] Secrets dokumentieren
- [ ] Environment validation

**1.3 Testing**
- [ ] Unit tests für kritische Funktionen
- [ ] Integration tests
- [ ] E2E tests (optional)

---

### Phase 2: CI/CD Setup (1 Tag)

**2.1 GitHub Actions**
- [ ] Workflow für Tests erstellen
- [ ] Workflow für Docker Build
- [ ] Workflow für Deployment
- [ ] Branch protection rules

**2.2 Container Registry**
- [ ] GitHub Container Registry setup
- [ ] Image tagging strategy
- [ ] Cleanup policy

---

### Phase 3: AWS Setup (2-3 Tage)

**3.1 AWS Account Setup**
- [ ] AWS Account erstellen
- [ ] IAM User für Deployment
- [ ] Budget Alerts einrichten

**3.2 Infrastructure (Lightsail)**
- [ ] Container Service erstellen
- [ ] Managed Database erstellen
- [ ] Redis setup (oder ElastiCache)
- [ ] Domain & SSL konfigurieren

**3.3 Deployment**
- [ ] Erste manuelle Deployment
- [ ] Environment variables setzen
- [ ] Database migrations
- [ ] Smoke tests

---

### Phase 4: Monitoring (1 Tag)

**4.1 Logging**
- [ ] CloudWatch Logs setup
- [ ] Log aggregation
- [ ] Log retention policy

**4.2 Monitoring**
- [ ] CloudWatch Dashboards
- [ ] Alarms für Fehler
- [ ] Alarms für Performance

**4.3 Error Tracking**
- [ ] Sentry integration
- [ ] Slack notifications

---

### Phase 5: Documentation (1 Tag)

- [ ] Deployment runbook
- [ ] Rollback procedure
- [ ] Troubleshooting guide
- [ ] Architecture diagrams

---

## 📝 Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/new-data-source

# 2. Develop & test locally
npm run dev  # Frontend
python -m uvicorn backend.main:app --reload  # Backend

# 3. Run tests
pytest
npm test

# 4. Commit & push
git add .
git commit -m "feat: add new data source"
git push origin feature/new-data-source

# 5. Create Pull Request
# → CI runs automatically
# → Deploy to preview environment

# 6. Code review & merge
# → Auto-deploy to staging

# 7. Test on staging
# → Manual approval

# 8. Merge to main
# → Auto-deploy to production
```

---

## 🚨 Rollback Strategy

### Automatic Rollback

```yaml
# In GitHub Actions
- name: Deploy
  run: deploy.sh
  
- name: Health Check
  run: |
    sleep 30
    curl -f https://api.openthreat.com/health || exit 1
    
- name: Rollback on Failure
  if: failure()
  run: rollback.sh
```

### Manual Rollback

```bash
# Rollback to previous version
aws ecs update-service \
  --cluster openthreat \
  --service backend \
  --task-definition backend:previous

# Or via Docker
docker-compose pull  # Get previous images
docker-compose up -d
```

---

## 📚 Nächste Schritte

### Sofort (Diese Woche)

1. **Docker Production Setup erstellen**
   - Dockerfiles optimieren
   - docker-compose.prod.yml
   - Health checks

2. **GitHub Actions CI/CD**
   - Basic pipeline
   - Tests automatisieren
   - Docker build

3. **AWS Account Setup**
   - Account erstellen
   - Budget alerts
   - IAM users

### Kurzfristig (Nächste 2 Wochen)

4. **AWS Lightsail Deployment**
   - Container Service
   - Database
   - Domain setup

5. **Monitoring Setup**
   - CloudWatch
   - Sentry
   - Uptime monitoring

### Mittelfristig (Nächster Monat)

6. **Production Hardening**
   - Security audit
   - Performance optimization
   - Backup strategy

7. **Documentation**
   - Deployment runbook
   - Troubleshooting guide
   - Architecture docs

---

## 🎓 Lernressourcen

### AWS
- [AWS Lightsail Containers](https://aws.amazon.com/lightsail/features/containers/)
- [AWS ECS Tutorial](https://docs.aws.amazon.com/ecs/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

### CI/CD
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Monitoring
- [CloudWatch Docs](https://docs.aws.amazon.com/cloudwatch/)
- [Sentry Docs](https://docs.sentry.io/)

---

## ❓ FAQ

**Q: Kann ich erst mal kostenlos testen?**
A: Ja! AWS Free Tier gibt dir 12 Monate kostenlos für viele Services.

**Q: Wie lange dauert das Setup?**
A: Mit Lightsail: ~1 Tag. Mit ECS: ~3-5 Tage.

**Q: Brauche ich AWS-Erfahrung?**
A: Für Lightsail: Nein. Für ECS: Ja, hilfreich.

**Q: Was wenn etwas schief geht?**
A: Automatic rollback + Monitoring alerts + Backup strategy.

**Q: Kann ich später upgraden?**
A: Ja! Von Lightsail → EC2 → ECS ist möglich.

---

**Nächster Schritt: Soll ich anfangen die Docker Production Files zu erstellen?** 🚀
