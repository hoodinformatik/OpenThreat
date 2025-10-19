# Security Setup

OpenThreat uses automated security scanning to prevent secrets from being committed.

## Pre-commit Hooks (Recommended)

We use **pre-commit** framework with gitleaks for automated security checks.

### Quick Setup

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Done! Hooks will run automatically on commit
```

### What Gets Checked

- **Gitleaks**: Secret detection (API keys, passwords, tokens)
- **Black**: Python code formatting
- **isort**: Import sorting
- **Flake8**: Python linting
- **General**: Trailing whitespace, large files, YAML/JSON syntax

### Manual Run

Test all hooks on all files:
```bash
pre-commit run --all-files
```

### Bypass (NOT RECOMMENDED)

Skip hooks for a single commit:
```bash
SKIP=gitleaks git commit -m "message"
# or skip all hooks
git commit --no-verify
```

## Legacy: Manual Gitleaks Installation (Optional)

**macOS:**
```bash
brew install gitleaks
```

**Linux:**
```bash
# Download latest release
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz
tar -xzf gitleaks_8.18.1_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/
```

**Windows:**
```bash
# Using Scoop
scoop install gitleaks

# Or download from GitHub releases
# https://github.com/gitleaks/gitleaks/releases
```

**Verify installation:**
```bash
gitleaks version
```

### Fallback Mode

If gitleaks is not installed, the pre-commit hook will use basic pattern matching as a fallback.

## Configuration

The `.gitleaks.toml` file contains the configuration for secret detection:

- **Extends default rules** from gitleaks
- **Allowlist** for false positives (GitHub Actions secrets, test data)
- **Custom patterns** for project-specific secrets

## CI/CD Integration

Gitleaks also runs in the GitHub Actions CI pipeline:

- Scans all commits in PRs
- Blocks merging if secrets are detected
- Results appear in GitHub Security tab

## Bypassing (NOT RECOMMENDED)

If you absolutely need to bypass the check:

```bash
git commit --no-verify
```

⚠️ **WARNING:** Only use this if you're certain there are no secrets!

## What Gets Detected

- API keys and tokens
- Passwords and credentials
- Private keys (SSH, RSA, etc.)
- AWS credentials
- GitHub tokens
- Stripe keys
- Database connection strings
- And 100+ other patterns

## False Positives

If you get a false positive:

1. Add it to `.gitleaks.toml` allowlist
2. Use more specific variable names
3. Add comments explaining why it's safe

## Testing

Test the security check manually:

```bash
# Stage some files
git add .

# Run the check
./scripts/security_check.sh
```

## References

- [Gitleaks Documentation](https://github.com/gitleaks/gitleaks)
- [Gitleaks Rules](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
