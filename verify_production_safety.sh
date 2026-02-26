#!/bin/bash

# Production Safety Verification Script
# Ensures no test-environment-specific code is being committed

echo "🔍 Verifying Production Safety..."
echo ""

FAILURES=0
WARNINGS=0

# Check for test-specific domain names in committed files
echo "📋 Checking for test-domain names (.local, localhost)..."
if git diff --staged | grep -q "bentcrankshaft\.local\|localhost:3[0-9][0-9][0-9]\|127\.0\.0\.1"; then
    echo "❌ ERROR: Found test-specific domains in staged changes!"
    git diff --staged | grep -n "bentcrankshaft\.local\|localhost"
    FAILURES=$((FAILURES + 1))
else
    echo "✅ No test domains found"
fi

# Check for docker-compose-test.yml references
echo ""
echo "📋 Checking for docker-compose-test.yml references..."
if git diff --staged | grep -q "docker-compose-test\.yml"; then
    echo "❌ ERROR: Found docker-compose-test.yml in staged changes!"
    git diff --staged | grep -n "docker-compose-test\.yml"
    FAILURES=$((FAILURES + 1))
else
    echo "✅ No docker-compose-test.yml references"
fi

# Check for test file paths
echo ""
echo "📋 Checking for test-specific paths (/root/power_equip_saas_test/)..."
if git diff --staged | grep -q "/root/power_equip_saas_test/"; then
    echo "❌ ERROR: Found test-environment paths in staged changes!"
    git diff --staged | grep -n "/root/power_equip_saas_test/"
    FAILURES=$((FAILURES + 1))
else
    echo "✅ No test paths found"
fi

# Check for test files being committed
echo ""
echo "📋 Checking for test-specific files..."
TEST_FILES=(
    "Dockerfile.nginx"
    "docker-compose-test.yml"
    "nginx_test.conf"
    "fix_admin.py"
    "fix_theme.py"
    "restore_organizations.py"
    "theme_id_1.json"
    "SETUP_COMPLETE.md"
)

for file in "${TEST_FILES[@]}"; do
    if git diff --cached --name-only | grep -q "^$file$"; then
        echo "❌ ERROR: Test file '$file' is staged for commit!"
        FAILURES=$((FAILURES + 1))
    fi
done
echo "✅ No test-specific files staged"

# Check for debug console.log statements
echo ""
echo "📋 Checking for debug console.log statements in TypeScript..."
if git diff --staged -- "*.ts" "*.tsx" | grep -q "console\.log\|console\.error\|console\.warn\|console\.debug"; then
    echo "⚠️  WARNING: Found console.log statements in TypeScript files"
    git diff --staged -- "*.ts" "*.tsx" | grep -n "console\."
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ No debug console statements"
fi

# Check for debug print statements in Python
echo ""
echo "📋 Checking for debug print statements in Python..."
if git diff --staged -- "*.py" | grep -q "print(.*DEBUG\|print(.*debug\|print(f.*\|import pdb"; then
    echo "⚠️  WARNING: Found debug print statements in Python files"
    git diff --staged -- "*.py" | grep -n "print(.*DEBUG\|print(.*debug"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ No debug print statements found"
fi

# Summary
echo ""
echo "════════════════════════════════════════"
if [ $FAILURES -eq 0 ]; then
    echo "✅ PRODUCTION SAFETY CHECK: PASSED"
    if [ $WARNINGS -eq 0 ]; then
        echo "🎉 Ready to commit!"
    else
        echo "⚠️  $WARNINGS warning(s) - review before committing"
    fi
    exit 0
else
    echo "❌ PRODUCTION SAFETY CHECK: FAILED"
    echo "🚫 $FAILURES error(s) found - DO NOT COMMIT"
    exit 1
fi
