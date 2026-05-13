# Security Pre-Push Checklist (PowerShell Version)
# Run this before pushing to GitHub: .\pre_push_security_check.ps1

Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🔒 SECURITY PRE-PUSH CHECKLIST" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$FAIL_COUNT = 0
$WARN_COUNT = 0

# Helper function for output
function Write-Pass($message) {
    Write-Host "✅ PASS: $message" -ForegroundColor Green
}

function Write-Fail($message) {
    Write-Host "❌ FAIL: $message" -ForegroundColor Red
}

function Write-Warning($message) {
    Write-Host "⚠️  WARNING: $message" -ForegroundColor Yellow
}

# Check 1: .env staged?
Write-Host "[1/7] Checking if .env is staged for commit..."
$staged = git diff --cached --name-only 2>$null | Where-Object { $_ -eq '.env' }
if ($staged) {
    Write-Fail ".env is staged for commit!"
    Write-Host "Run: git reset .env" -ForegroundColor Yellow
    $FAIL_COUNT++
} else {
    Write-Pass ".env is NOT staged"
}
Write-Host ""

# Check 2: .env in .gitignore?
Write-Host "[2/7] Checking if .env is in .gitignore..."
$inGitIgnore = (Get-Content .gitignore -ErrorAction SilentlyContinue) | Select-String "^\.env$"
if ($inGitIgnore) {
    Write-Pass ".env is in .gitignore"
} else {
    Write-Warning ".env might not be in .gitignore"
    $WARN_COUNT++
}
Write-Host ""

# Check 3: Hardcoded passwords?
Write-Host "[3/7] Checking for hardcoded passwords in staged files..."
$passwords = git diff --cached 2>$null | Select-String -Pattern "password\s*=\s*['\"]" | Where-Object { $_ -notmatch "your_password|YOUR_PASSWORD|example|test" }
if ($passwords) {
    Write-Fail "Hardcoded password found in staged files!"
    Write-Host $passwords -ForegroundColor Red
    $FAIL_COUNT++
} else {
    Write-Pass "No hardcoded passwords found"
}
Write-Host ""

# Check 4: Hardcoded API keys?
Write-Host "[4/7] Checking for hardcoded API keys in staged files..."
$apikeys = git diff --cached 2>$null | Select-String -Pattern "api.?key\s*=\s*['\"]" | Where-Object { $_ -notmatch "your_api_key|YOUR_API_KEY|example" }
if ($apikeys) {
    Write-Fail "Hardcoded API key found!"
    Write-Host $apikeys -ForegroundColor Red
    $FAIL_COUNT++
} else {
    Write-Pass "No hardcoded API keys found"
}
Write-Host ""

# Check 5: Secrets/tokens?
Write-Host "[5/7] Checking for secrets or tokens in staged files..."
$secrets = git diff --cached 2>$null | Select-String -Pattern "secret.?key.*=|token.*=|private.?key.*=" | Where-Object { $_ -notmatch "test|example|your_" }
if ($secrets) {
    Write-Fail "Potential secret/token found!"
    Write-Host $secrets -ForegroundColor Red
    $FAIL_COUNT++
} else {
    Write-Pass "No secrets/tokens found"
}
Write-Host ""

# Check 6: .env in git history?
Write-Host "[6/7] Checking git history for .env file..."
$envHistory = git log --all --full-history -- ".env" 2>$null | Select-String "commit"
if ($envHistory) {
    Write-Warning ".env found in git history"
    Write-Host "This means credentials may have been committed before" -ForegroundColor Yellow
    Write-Host "Consider: git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all" -ForegroundColor Yellow
    $WARN_COUNT++
} else {
    Write-Pass ".env not in git history"
}
Write-Host ""

# Check 7: Git status
Write-Host "[7/7] Checking git status..."
$gitStatus = git status --short 2>$null | Select-String "\.env"
if ($gitStatus) {
    Write-Fail ".env appears in git status"
    Write-Host $gitStatus -ForegroundColor Red
    $FAIL_COUNT++
} else {
    Write-Pass ".env does NOT appear in git status"
}
Write-Host ""

# Summary
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($FAIL_COUNT -eq 0) {
    Write-Host "✅ ALL CRITICAL CHECKS PASSED!" -ForegroundColor Green
    if ($WARN_COUNT -eq 0) {
        Write-Host "Safe to push to GitHub 🚀" -ForegroundColor Green
    } else {
        Write-Host "⚠️  $WARN_COUNT warning(s) found - review before pushing" -ForegroundColor Yellow
    }
    exit 0
} else {
    Write-Host "❌ $FAIL_COUNT CRITICAL ISSUE(S) FOUND!" -ForegroundColor Red
    Write-Host "DO NOT PUSH - Fix issues first" -ForegroundColor Red
    exit 1
}
