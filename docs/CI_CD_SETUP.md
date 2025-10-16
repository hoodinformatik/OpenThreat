# 🚀 CI/CD Setup Guide

## Overview

OpenThreat uses GitHub Actions for:
- ✅ Automatic tests on every push
- ✅ Code quality checks
- ✅ Security scanning
- ✅ Automatic deployment

---

## 📋 Workflows

### 1. **CI Pipeline** (`ci.yml`)
Runs on every push/PR to `main` or `develop`

**What is tested:**
- ✅ Python tests (pytest)
- ✅ Code coverage (>50%)
- ✅ Linting (flake8, black, isort)
- ✅ Security scan (Trivy)
- ✅ Docker build

**Duration:** ~5-10 minutes

### 2. **Deploy Pipeline** (`deploy.yml`)
Runs on push to `main` or manually

**What happens:**
- ✅ SSH to server
- ✅ Git pull
- ✅ Docker rebuild
- ✅ Database migration
- ✅ Health check

**Duration:** ~3-5 minutes

---

## 🔧 Setup on GitHub

### Step 1: Configure Repository Secrets

Go to: **Settings → Secrets and variables → Actions**

Create the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SSH_PRIVATE_KEY` | Private SSH key for server | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_IP` | Server IP address | `123.45.67.89` |
| `SERVER_USER` | SSH username | `openthreat` |

---

### Step 2: Generate SSH Key

On your **local computer**:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "github-actions@openthreat.io" -f ~/.ssh/openthreat_deploy

# Copy public key to server
ssh-copy-id -i ~/.ssh/openthreat_deploy.pub openthreat@your-server-ip

# Display private key (for GitHub Secret)
cat ~/.ssh/openthreat_deploy
```

**Copy the entire private key** (including `-----BEGIN` and `-----END`) to GitHub Secret `SSH_PRIVATE_KEY`

---

### Step 3: Prepare Server

On the **server**:

```bash
# Create user
sudo adduser openthreat
sudo usermod -aG docker openthreat

# Clone repository
su - openthreat
git clone https://github.com/hoodinformatik/OpenThreat.git
cd OpenThreat

# Create .env
cp .env.production.example .env
nano .env  # Enter passwords

# First deploy (manual)
docker-compose -f docker-compose.prod.yml up -d
```

---

### Step 4: Activate GitHub Actions

1. **Push code to GitHub:**
```bash
git add .
git commit -m "feat: Add CI/CD pipeline"
git push origin main
```

2. **Workflow runs automatically**
   - Go to: **Actions** tab on GitHub
   - Watch the workflow run

3. **Badge in README** (optional):
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

## 🎯 Usage

### Automatic Deployment

**On every push to `main`:**
```bash
git add .
git commit -m "feat: New feature"
git push origin main
# → Deployment runs automatically
```

### Manual Deployment

1. Go to **Actions** tab
2. Select **Deploy to Production**
3. Click **Run workflow**
4. Select branch (e.g. `main`)
5. Click **Run workflow**

### Deployment with Tag

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
# → Deployment runs automatically
```

---

## 🛡️ Security Best Practices

### ✅ DO:
- ✅ Store secrets in GitHub Secrets
- ✅ Protect SSH keys with passphrase
- ✅ Rotate keys regularly
- ✅ Only necessary permissions

### ❌ DON'T:
- ❌ Commit secrets in code
- ❌ Share private keys
- ❌ Use root user for deployment
- ❌ Log passwords

---

## 📊 Monitoring

### GitHub Actions Logs

**Show logs:**
1. Go to **Actions** tab
2. Click on workflow run
3. Click on job
4. See detailed logs

### Server Logs

```bash
# SSH to server
ssh openthreat@your-server-ip

# Docker logs
cd OpenThreat
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

---

## 🔧 Troubleshooting

### Problem: SSH Connection Failed

**Solution:**
```bash
# On local computer
ssh -i ~/.ssh/openthreat_deploy openthreat@your-server-ip

# If this works, the key is OK
# If not, check:
chmod 600 ~/.ssh/openthreat_deploy
```

### Problem: Docker Build Failed

**Solution:**
```bash
# On server
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Problem: Health Check Failed

**Solution:**
```bash
# Check if backend is running
curl http://localhost/health

# Check Docker status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs backend
```

### Problem: Tests Fail

**Solution:**
```bash
# Test locally
pytest tests/ -v

# Specific test
pytest tests/test_api_vulnerabilities.py -v

# With coverage
pytest --cov=backend
```

---

## 🚀 Advanced: Multi-Environment

### Configure Environments

**GitHub Settings → Environments:**

1. **staging**
   - Branch: `develop`
   - URL: `https://staging.openthreat.io`

2. **production**
   - Branch: `main`
   - URL: `https://openthreat.io`
   - Protection: Require approval

### Customize Workflow

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

## 📈 Performance Optimization

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

### Before first deployment:

- [ ] GitHub Secrets configured
- [ ] SSH key on server
- [ ] Server prepared
- [ ] `.env` configured on server
- [ ] First manual deploy successful
- [ ] Health check works

### After each deployment:

- [ ] Health check passed
- [ ] Check logs
- [ ] Frontend reachable
- [ ] API works
- [ ] Database migration successful

---

## 📧 Support

For issues:
- **GitHub Issues:** https://github.com/hoodinformatik/OpenThreat/issues
- **Email:** hoodinformatik@gmail.com

---

## 🎉 Done!

**Your CI/CD pipeline is ready!**

Every push to `main` will automatically:
- ✅ Be tested
- ✅ Be scanned
- ✅ Be deployed
- ✅ Be verified

**Happy Deploying! 🚀**
