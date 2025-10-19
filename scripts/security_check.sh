#!/bin/bash
# Security check script to prevent committing secrets
# Runs before each commit via pre-commit hook

set -e

echo "🔒 Running security checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for common secret patterns in staged files
SECRETS_FOUND=0

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}✓${NC} No files to check"
    exit 0
fi

echo "Checking $(echo "$STAGED_FILES" | wc -l) staged files..."

# Patterns to search for
declare -a PATTERNS=(
    "password\s*=\s*['\"][^'\"]+['\"]"
    "api_key\s*=\s*['\"][^'\"]+['\"]"
    "secret\s*=\s*['\"][^'\"]+['\"]"
    "token\s*=\s*['\"][^'\"]+['\"]"
    "private_key"
    "BEGIN RSA PRIVATE KEY"
    "BEGIN OPENSSH PRIVATE KEY"
    "AWS_SECRET_ACCESS_KEY"
    "AKIA[0-9A-Z]{16}"
    "sk_live_[0-9a-zA-Z]{24}"
    "sk_test_[0-9a-zA-Z]{24}"
    "ghp_[0-9a-zA-Z]{36}"
    "gho_[0-9a-zA-Z]{36}"
)

# Check each staged file
for file in $STAGED_FILES; do
    # Skip binary files and certain directories
    if [[ "$file" == *".git/"* ]] || \
       [[ "$file" == *"node_modules/"* ]] || \
       [[ "$file" == *".pyc" ]] || \
       [[ "$file" == *"__pycache__/"* ]] || \
       [[ "$file" == *".env.example" ]] || \
       [[ "$file" == *".env.production.example" ]]; then
        continue
    fi
    
    # Check if file exists (might be deleted)
    if [ ! -f "$file" ]; then
        continue
    fi
    
    # Check for each pattern
    for pattern in "${PATTERNS[@]}"; do
        if grep -iEq "$pattern" "$file"; then
            # Check if it's a GitHub Actions secret reference (false positive)
            if grep -q "secrets\." "$file" && [[ "$file" == *".github/workflows/"* ]]; then
                continue  # Skip GitHub Actions secret references
            fi
            
            # Check if it's in a comment or example
            if grep -E "(#.*$pattern|//.*$pattern|\.example)" "$file" > /dev/null; then
                continue  # Skip comments and example files
            fi
            
            echo -e "${RED}✗${NC} Potential secret found in: $file"
            echo -e "${YELLOW}  Pattern: $pattern${NC}"
            SECRETS_FOUND=1
        fi
    done
done

# Check for .env files (should never be committed)
if echo "$STAGED_FILES" | grep -q "^\.env$"; then
    echo -e "${RED}✗${NC} .env file should not be committed!"
    echo -e "${YELLOW}  Use .env.example instead${NC}"
    SECRETS_FOUND=1
fi

# Check for common credential files
CREDENTIAL_FILES=(".env" "credentials.json" "secrets.yaml" "secrets.yml" "id_rsa" "id_dsa" ".ssh/")
for cred_file in "${CREDENTIAL_FILES[@]}"; do
    if echo "$STAGED_FILES" | grep -q "$cred_file"; then
        echo -e "${RED}✗${NC} Credential file detected: $cred_file"
        SECRETS_FOUND=1
    fi
done

# Final result
if [ $SECRETS_FOUND -eq 1 ]; then
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ COMMIT BLOCKED: Potential secrets detected!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Please remove sensitive data before committing."
    echo "If this is a false positive, you can:"
    echo "  1. Fix the pattern to not look like a secret"
    echo "  2. Use git commit --no-verify (NOT RECOMMENDED)"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓${NC} No secrets detected"
    echo -e "${GREEN}✓${NC} Security check passed"
    exit 0
fi
