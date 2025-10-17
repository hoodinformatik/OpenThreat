# Security Guidelines for OpenThreat

## 🔒 Sensitive Files - NEVER Commit These!

### Environment Files
- `.env` - Local development environment variables
- `.env.backup` - Backup of environment variables
- `.env.production` - Production environment variables
- `.env.local` - Local overrides
- Any file matching `*.env` (except `.env.example`)

### SSL Certificates & Keys
- `*.key` - Private keys
- `*.pem` - PEM certificates
- `*.crt` - Certificate files
- `*.cer` - Certificate files
- `*.p12`, `*.pfx` - PKCS#12 certificates
- `nginx/ssl/` - SSL certificate directory

### API Keys & Secrets
- `*_api_key.txt`
- `*_secret.txt`
- `*_token.txt`
- `*_password.txt`
- `secrets/`, `.secrets/` - Secret directories
- `credentials/`, `.credentials/` - Credential directories

### Database Files
- `*.sql` - SQL dumps (may contain sensitive data)
- `*.sql.gz` - Compressed SQL dumps
- `*.dump` - Database dumps
- `backups/` - Backup directory
- `postgres_data/` - PostgreSQL data directory

## ✅ Security Checklist

### Before Committing
- [ ] No `.env` files committed
- [ ] No SSL certificates or private keys
- [ ] No hardcoded passwords or API keys
- [ ] No database dumps or backups
- [ ] All secrets use environment variables
- [ ] `.gitignore` is up to date

### Environment Variables
All sensitive configuration should use environment variables:

```python
# ✅ GOOD
password = os.getenv("POSTGRES_PASSWORD")
api_key = os.getenv("NVD_API_KEY")

# ❌ BAD
password = "my_secret_password"
api_key = "abc123xyz789"
```

### GitHub Secrets
Store production secrets in GitHub repository settings:
- `SSH_PRIVATE_KEY` - SSH key for deployment
- `SERVER_IP` - Production server IP
- `SERVER_USER` - SSH username
- `POSTGRES_PASSWORD` - Database password

## 🔍 How to Check for Leaked Secrets

### Check Git History
```bash
# Check if sensitive files were ever committed
git log --all --full-history -- .env .env.backup nginx/ssl/

# Search for potential secrets in commit history
git log -p | grep -i "password\|secret\|api_key"
```

### Scan Current Files
```bash
# Find sensitive files not in .gitignore
find . -type f \( -name "*.key" -o -name "*.pem" -o -name ".env" \) ! -path "./.git/*"

# Check for hardcoded secrets
grep -r "password\s*=\s*['\"]" --include="*.py" backend/
```

## 🚨 If You Accidentally Commit Secrets

1. **Immediately rotate the compromised credentials**
2. **Remove from Git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push (⚠️ dangerous):**
   ```bash
   git push origin --force --all
   ```
4. **Notify team members to re-clone the repository**

## 📝 Best Practices

1. **Use `.env.example`** - Provide template without actual secrets
2. **Document required variables** - List all needed environment variables
3. **Use strong passwords** - Generate random passwords for production
4. **Rotate secrets regularly** - Change passwords and API keys periodically
5. **Limit access** - Only give production access to necessary team members
6. **Enable 2FA** - Use two-factor authentication for all services
7. **Monitor logs** - Watch for unauthorized access attempts
8. **Regular security audits** - Review access logs and permissions

## 🔐 Production Deployment

### Required Environment Variables
```bash
# Database
POSTGRES_USER=openthreat
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=openthreat

# Redis
REDIS_URL=redis://redis:6379

# NVD API (optional but recommended)
NVD_API_KEY=<your-nvd-api-key>

# Ollama LLM
OLLAMA_HOST=http://ollama:11434
LLM_MODEL=llama3.2:1b
```

### Secure Server Setup
1. Use SSH key authentication (disable password login)
2. Configure firewall (only allow ports 80, 443, 22)
3. Enable automatic security updates
4. Use SSL/TLS certificates (Let's Encrypt)
5. Regular backups (encrypted)
6. Monitor system logs

## 📞 Security Contact

If you discover a security vulnerability, please email:
**security@openthreat.com** (replace with actual email)

Do NOT create public GitHub issues for security vulnerabilities.
