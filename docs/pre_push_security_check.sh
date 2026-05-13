#!/bin/bash
# Security Pre-Push Checklist
# Run this before pushing to GitHub: bash pre_push_security_check.sh

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🔒 SECURITY PRE-PUSH CHECKLIST"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

FAIL_COUNT=0
WARN_COUNT=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "[1/7] Checking if .env is staged for commit..."
if git diff --cached --name-only | grep -q "^\.env$"; then
    echo -e "${RED}❌ FAIL: .env is staged for commit!${NC}"
    echo "Run: git reset .env"
    ((FAIL_COUNT++))
else
    echo -e "${GREEN}✅ PASS: .env is NOT staged${NC}"
fi
echo ""

echo "[2/7] Checking if .env is in .gitignore..."
if grep -q "^\.env$" .gitignore; then
    echo -e "${GREEN}✅ PASS: .env is in .gitignore${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING: .env might not be in .gitignore${NC}"
    ((WARN_COUNT++))
fi
echo ""

echo "[3/7] Checking for hardcoded passwords in staged files..."
if git diff --cached | grep -i "password\s*=\s*['\"][^'\"]*['\"]" | grep -v "your_password\|YOUR_PASSWORD\|example\|test"; then
    echo -e "${RED}❌ FAIL: Hardcoded password found in staged files!${NC}"
    ((FAIL_COUNT++))
else
    echo -e "${GREEN}✅ PASS: No hardcoded passwords found${NC}"
fi
echo ""

echo "[4/7] Checking for hardcoded API keys in staged files..."
if git diff --cached | grep -iE "api.?key\s*=\s*['\"][^'\"]*sk_" | grep -v "your_api_key\|YOUR_API_KEY\|example"; then
    echo -e "${RED}❌ FAIL: Hardcoded API key found!${NC}"
    ((FAIL_COUNT++))
else
    echo -e "${GREEN}✅ PASS: No hardcoded API keys found${NC}"
fi
echo ""

echo "[5/7] Checking for secrets or tokens in staged files..."
if git diff --cached | grep -iE "secret.?key.*=|token.*=|private.?key.*=" | grep -v "test\|example\|your_"; then
    echo -e "${RED}❌ FAIL: Potential secret/token found!${NC}"
    ((FAIL_COUNT++))
else
    echo -e "${GREEN}✅ PASS: No secrets/tokens found${NC}"
fi
echo ""

echo "[6/7] Checking git history for .env file..."
if git log --all --full-history -- ".env" 2>/dev/null | grep -q "commit"; then
    echo -e "${YELLOW}⚠️  WARNING: .env found in git history${NC}"
    echo "This means credentials may have been committed before"
    echo "Consider: git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all"
    ((WARN_COUNT++))
else
    echo -e "${GREEN}✅ PASS: .env not in git history${NC}"
fi
echo ""

echo "[7/7] Checking git status..."
if git status --short | grep -q "\.env"; then
    echo -e "${RED}❌ FAIL: .env appears in git status${NC}"
    ((FAIL_COUNT++))
else
    echo -e "${GREEN}✅ PASS: .env does NOT appear in git status${NC}"
fi
echo ""

echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CRITICAL CHECKS PASSED!${NC}"
    if [ $WARN_COUNT -eq 0 ]; then
        echo "Safe to push to GitHub 🚀"
    else
        echo "⚠️  ${WARN_COUNT} warning(s) found - review before pushing"
    fi
    exit 0
else
    echo -e "${RED}❌ ${FAIL_COUNT} CRITICAL ISSUE(S) FOUND!${NC}"
    echo "DO NOT PUSH - Fix issues first"
    exit 1
fi
