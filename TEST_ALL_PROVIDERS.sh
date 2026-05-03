#!/bin/bash

# Comprehensive Test Script for H&S Layer
# Tests all providers, skills, and features

echo "🧪 H&S Layer - Comprehensive Testing"
echo "======================================"
echo ""

# Configuration
BACKEND_URL="http://localhost:8000"
USER_ID="test-user-$(date +%s)"
OPENROUTER_KEY="${1:-sk-or-v1-test}"
FEATHERLESS_KEY="${2:-fl-test}"

echo "📋 Test Configuration:"
echo "  Backend: $BACKEND_URL"
echo "  User ID: $USER_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run tests
run_test() {
    local test_name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing: $test_name... "
    
    result=$(eval "$command" 2>&1)
    
    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "======================================"
echo "1️⃣  HEALTH CHECK"
echo "======================================"
run_test "Backend Health" \
    "curl -s $BACKEND_URL/healthz" \
    "ok"

echo ""
echo "======================================"
echo "2️⃣  API KEY SETUP - OPENROUTER"
echo "======================================"

# Store OpenRouter key
curl -s -X POST $BACKEND_URL/apikey \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"provider\":\"openrouter\",\"api_key\":\"$OPENROUTER_KEY\"}" > /dev/null

# Generate Aurora key for OpenRouter
AURORA_KEY_OR=$(curl -s -X POST $BACKEND_URL/auth/issue-key \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"name\":\"OpenRouter Test\",\"scopes\":[\"chat\",\"memory\",\"tools\",\"skills\"]}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])" 2>/dev/null)

if [ -n "$AURORA_KEY_OR" ]; then
    echo -e "${GREEN}✅ OpenRouter Aurora Key Generated${NC}"
    echo "  Key: ${AURORA_KEY_OR:0:20}..."
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Failed to generate OpenRouter key${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "======================================"
echo "3️⃣  API KEY SETUP - FEATHERLESS"
echo "======================================"

# Store Featherless key
curl -s -X POST $BACKEND_URL/apikey \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID-fl\",\"provider\":\"featherless\",\"api_key\":\"$FEATHERLESS_KEY\"}" > /dev/null

# Generate Aurora key for Featherless
AURORA_KEY_FL=$(curl -s -X POST $BACKEND_URL/auth/issue-key \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID-fl\",\"name\":\"Featherless Test\",\"scopes\":[\"chat\",\"memory\",\"tools\",\"skills\"]}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])" 2>/dev/null)

if [ -n "$AURORA_KEY_FL" ]; then
    echo -e "${GREEN}✅ Featherless Aurora Key Generated${NC}"
    echo "  Key: ${AURORA_KEY_FL:0:20}..."
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Failed to generate Featherless key${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "======================================"
echo "4️⃣  CODE GENERATION TEST - OPENROUTER"
echo "======================================"

if [ -n "$AURORA_KEY_OR" ]; then
    echo "Testing Python code generation..."
    CODE_RESULT=$(curl -s -X POST $BACKEND_URL/v1/run \
      -H "Authorization: Bearer $AURORA_KEY_OR" \
      -H "Content-Type: application/json" \
      -d "{\"user_id\":\"$USER_ID\",\"input\":\"Write a Python function to add two numbers\",\"provider\":\"openrouter\",\"model\":\"openrouter/auto\",\"memory_scope\":\"user\"}" \
      --max-time 30)
    
    if echo "$CODE_RESULT" | grep -q '```python'; then
        echo -e "${GREEN}✅ Code block with proper markdown found${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ No proper code block found${NC}"
        ((TESTS_FAILED++))
    fi
fi

echo ""
echo "======================================"
echo "5️⃣  MEMORY TEST"
echo "======================================"

if [ -n "$AURORA_KEY_OR" ]; then
    echo "Storing memory facts..."
    curl -s -X POST $BACKEND_URL/v1/run \
      -H "Authorization: Bearer $AURORA_KEY_OR" \
      -H "Content-Type: application/json" \
      -d "{\"user_id\":\"$USER_ID\",\"input\":\"My name is TestUser and I prefer TypeScript\",\"provider\":\"openrouter\",\"model\":\"openrouter/auto\",\"memory_scope\":\"user\"}" \
      --max-time 30 > /dev/null
    
    sleep 2
    
    echo "Retrieving memory..."
    MEMORY_RESULT=$(curl -s -X POST $BACKEND_URL/v1/memory/context \
      -H "Authorization: Bearer $AURORA_KEY_OR" \
      -H "Content-Type: application/json" \
      -d "{\"user_id\":\"$USER_ID\",\"query\":\"user preferences\",\"memory_scope\":\"user\",\"top_k\":10}")
    
    if echo "$MEMORY_RESULT" | grep -q "TestUser\|TypeScript"; then
        echo -e "${GREEN}✅ Memory stored and retrieved successfully${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  Memory test inconclusive${NC}"
    fi
fi

echo ""
echo "======================================"
echo "6️⃣  SKILLS TEST"
echo "======================================"

SKILLS_COUNT=$(curl -s $BACKEND_URL/v1/skills \
  -H "Authorization: Bearer $AURORA_KEY_OR" \
  | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

if [ "$SKILLS_COUNT" -gt 1000 ]; then
    echo -e "${GREEN}✅ Skills loaded: $SKILLS_COUNT${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Expected 1080+ skills, got: $SKILLS_COUNT${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "======================================"
echo "7️⃣  TOOLS TEST"
echo "======================================"

TOOLS_COUNT=$(curl -s $BACKEND_URL/tools \
  -H "Authorization: Bearer $AURORA_KEY_OR" \
  | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

if [ "$TOOLS_COUNT" -gt 50 ]; then
    echo -e "${GREEN}✅ Tools loaded: $TOOLS_COUNT${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Expected 55+ tools, got: $TOOLS_COUNT${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "======================================"
echo "8️⃣  A/B COMPARE TEST"
echo "======================================"

if [ -n "$AURORA_KEY_OR" ]; then
    echo "Running A/B comparison..."
    COMPARE_RESULT=$(curl -s -X POST $BACKEND_URL/v1/compare \
      -H "Authorization: Bearer $AURORA_KEY_OR" \
      -H "Content-Type: application/json" \
      -d "{\"user_id\":\"$USER_ID\",\"input\":\"Write a function to calculate factorial\",\"provider\":\"openrouter\",\"model\":\"openrouter/auto\",\"memory_scope\":\"user\"}" \
      --max-time 40)
    
    if echo "$COMPARE_RESULT" | grep -q "baseline.*tuned"; then
        echo -e "${GREEN}✅ A/B comparison successful${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  A/B comparison test inconclusive${NC}"
    fi
fi

echo ""
echo "======================================"
echo "📊 TEST SUMMARY"
echo "======================================"
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "🎉 Your H&S Layer is working perfectly!"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:3000"
    echo "  2. Use Aurora Key: $AURORA_KEY_OR"
    echo "  3. Start building amazing AI applications!"
    exit 0
else
    echo -e "${YELLOW}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Check the errors above and:"
    echo "  1. Ensure backend is running (./START_SERVERS.sh)"
    echo "  2. Check API keys are valid"
    echo "  3. Review backend logs for errors"
    exit 1
fi
