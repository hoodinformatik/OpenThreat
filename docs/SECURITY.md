# Security Guidelines

## API Keys and Secrets

### ⚠️ NEVER commit sensitive data to Git!

### Protected Files (already in .gitignore):
- `.env` - Your personal environment variables
- `.env.local` - Local overrides
- `*_api_key.txt` - Any API key files
- `*_secret.txt` - Any secret files
- `nvd_checkpoint.txt` - Progress tracking (may contain timestamps)

### Safe Files (can be committed):
- `.env.example` - Template without real values
- Documentation files
- Configuration templates

---

## Setting Up Your API Keys

### 1. Copy the example file:
```bash
cp .env.example .env
```

### 2. Edit `.env` with your real values:
```bash
# Open in your editor
code .env
# or
notepad .env
```

### 3. Add your NVD API Key:
```env
NVD_API_KEY=your-actual-api-key-here
```

### 4. Verify it's ignored by Git:
```bash
git status
# .env should NOT appear in the list
```

---

## Available API Keys

### NVD API Key (Recommended)
- **Get it:** https://nvd.nist.gov/developers/request-an-api-key
- **Free:** Yes
- **Rate Limit:** 50 requests/minute (vs 10 without key)
- **Required:** No, but highly recommended for bulk imports
- **Environment Variable:** `NVD_API_KEY`

### VulnCheck API Key (Optional)
- **Get it:** https://vulncheck.com/
- **Free Tier:** Yes (limited)
- **Purpose:** Enhanced exploitation intelligence
- **Environment Variable:** `VULNCHECK_API_KEY`

### GitHub Token (Optional)
- **Get it:** https://github.com/settings/tokens
- **Free:** Yes
- **Purpose:** GitHub Security Advisories
- **Permissions:** `public_repo` (read-only)
- **Environment Variable:** `GITHUB_TOKEN`

---

## Checking for Leaked Secrets

### Before committing:
```bash
# Check what will be committed
git status

# View changes
git diff

# Make sure .env is NOT listed
```

### If you accidentally committed a secret:

1. **Immediately revoke the API key** at the provider
2. **Remove from Git history:**
   ```bash
   # Remove file from Git but keep locally
   git rm --cached .env
   
   # Commit the removal
   git commit -m "Remove accidentally committed .env file"
   
   # If already pushed, you need to rewrite history (dangerous!)
   # Contact your team first!
   ```

3. **Generate a new API key**
4. **Update your `.env` file**

---

## Best Practices

### ✅ DO:
- Use `.env` files for local development
- Use environment variables in production
- Use different keys for dev/staging/production
- Rotate API keys regularly
- Keep `.env.example` updated (without real values)
- Document required environment variables

### ❌ DON'T:
- Commit `.env` files to Git
- Share API keys in chat/email
- Hardcode secrets in source code
- Use production keys in development
- Store secrets in documentation
- Push secrets to public repositories

---

## Production Deployment

### Use environment variables, not .env files:

**Docker:**
```bash
docker run -e NVD_API_KEY=your-key openthreat
```

**Docker Compose:**
```yaml
environment:
  - NVD_API_KEY=${NVD_API_KEY}
```

**Kubernetes:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: openthreat-secrets
type: Opaque
data:
  nvd-api-key: <base64-encoded-key>
```

**Cloud Platforms:**
- AWS: Use AWS Secrets Manager or Parameter Store
- Azure: Use Azure Key Vault
- GCP: Use Secret Manager
- Heroku: Use Config Vars
- Vercel: Use Environment Variables

---

## Verifying Security

### Check .gitignore is working:
```bash
# This should show .env is ignored
git check-ignore -v .env

# Output should be:
# .gitignore:27:.env    .env
```

### Scan for secrets (optional):
```bash
# Install gitleaks (optional)
# https://github.com/gitleaks/gitleaks

gitleaks detect --source . --verbose
```

---

## Emergency Response

### If you leaked a secret:

1. **Revoke immediately** - Don't wait!
2. **Remove from Git history** - Use `git filter-branch` or BFG Repo-Cleaner
3. **Generate new secrets** - Update all systems
4. **Notify team** - If applicable
5. **Review access logs** - Check for unauthorized use
6. **Update documentation** - Prevent future incidents

---

## Questions?

If you're unsure about security:
1. Check this document
2. Review `.gitignore`
3. Test with `git status` before committing
4. When in doubt, ask!

**Remember: It's easier to prevent leaks than to fix them!**
