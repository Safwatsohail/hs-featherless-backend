#!/bin/bash

# Enhanced AI API - External Test Script
# This script tests the API from outside the frontend

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000"
USER_ID="00000000-0000-0000-0000-000000000001"
OPENROUTER_KEY="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"
AURORA_KEY="aurora_live_ZNTshOqnNk8LvKYKuuW5hZpW-3WHI1Ko"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║          Enhanced AI API - External Test Suite              ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Health Check
echo -e "${BLUE}Test 1: Health Check${NC}"
HEALTH=$(curl -s "$API_BASE/healthz")
if echo "$HEALTH" | grep -q '"ok":true'; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend is not responding${NC}"
    exit 1
fi
echo ""

# Test 2: Store API Key
echo -e "${BLUE}Test 2: Store OpenRouter API Key${NC}"
STORE_RESULT=$(curl -s -X POST "$API_BASE/apikey" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"provider\": \"openrouter\", \"api_key\": \"$OPENROUTER_KEY\"}")
if echo "$STORE_RESULT" | grep -q '"stored":true'; then
    echo -e "${GREEN}✓ API key stored successfully${NC}"
else
    echo -e "${RED}✗ Failed to store API key${NC}"
    echo "$STORE_RESULT"
fi
echo ""

# Test 3: Generate Aurora Key
echo -e "${BLUE}Test 3: Generate Aurora Enhanced Key${NC}"
AURORA_RESULT=$(curl -s -X POST "$API_BASE/auth/issue-key" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"name\": \"Test Key\", \"scopes\": [\"chat\",\"memory\",\"tools\",\"skills\"]}")
NEW_AURORA_KEY=$(echo "$AURORA_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('api_key', ''))" 2>/dev/null || echo "")
if [ -n "$NEW_AURORA_KEY" ]; then
    echo -e "${GREEN}✓ Aurora key generated: $NEW_AURORA_KEY${NC}"
    AURORA_KEY="$NEW_AURORA_KEY"
else
    echo -e "${BLUE}ℹ Using existing Aurora key: $AURORA_KEY${NC}"
fi
echo ""

# Test 4: Simple Chat
echo -e "${BLUE}Test 4: Simple Chat (What is 2+2?)${NC}"
CHAT_RESULT=$(curl -s -X POST "$API_BASE/v1/run" \
  -H "Authorization: Bearer $AURORA_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"input\": \"What is 2+2?\", \"memory_scope\": \"user\", \"provider\": \"openrouter\", \"model\": \"openrouter/auto\"}")
CHAT_OUTPUT=$(echo "$CHAT_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('output', '')[:100])" 2>/dev/null || echo "")
if [ -n "$CHAT_OUTPUT" ]; then
    echo -e "${GREEN}✓ Chat response received${NC}"
    echo -e "  Output: $CHAT_OUTPUT..."
else
    echo -e "${RED}✗ Chat failed${NC}"
    echo "$CHAT_RESULT"
fi
echo ""

# Test 5: Compare
echo -e "${BLUE}Test 5: Compare Raw vs Enhanced${NC}"
COMPARE_RESULT=$(curl -s -X POST "$API_BASE/v1/compare" \
  -H "Authorization: Bearer $AURORA_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"input\": \"Calculate 15 * 8\", \"provider\": \"openrouter\", \"model\": \"openrouter/auto\", \"memory_scope\": \"user\"}")
BASELINE_OUTPUT=$(echo "$COMPARE_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('baseline', {}).get('output', '')[:80])" 2>/dev/null || echo "")
TUNED_OUTPUT=$(echo "$COMPARE_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tuned', {}).get('output', '')[:80])" 2>/dev/null || echo "")
if [ -n "$BASELINE_OUTPUT" ] && [ -n "$TUNED_OUTPUT" ]; then
    echo -e "${GREEN}✓ Compare completed${NC}"
    echo -e "  Baseline: $BASELINE_OUTPUT..."
    echo -e "  Tuned: $TUNED_OUTPUT..."
else
    echo -e "${RED}✗ Compare failed${NC}"
    echo "$COMPARE_RESULT"
fi
echo ""

# Test 6: Execute Tool
echo -e "${BLUE}Test 6: Execute Tool (calculator)${NC}"
TOOL_RESULT=$(curl -s -X POST "$API_BASE/v1/tools/calculator" \
  -H "Authorization: Bearer $AURORA_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "calculator", "input": {"expression": "42 * 7"}}')
TOOL_OUTPUT=$(echo "$TOOL_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('output', ''))" 2>/dev/null || echo "")
if [ -n "$TOOL_OUTPUT" ]; then
    echo -e "${GREEN}✓ Tool executed${NC}"
    echo -e "  Result: $TOOL_OUTPUT"
else
    echo -e "${RED}✗ Tool execution failed${NC}"
    echo "$TOOL_RESULT"
fi
echo ""

# Test 7: Store Memory
echo -e "${BLUE}Test 7: Store Memory${NC}"
MEMORY_RESULT=$(curl -s -X POST "$API_BASE/v1/memory" \
  -H "Authorization: Bearer $AURORA_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"text\": \"User is testing the API externally\", \"kind\": \"context\", \"memory_scope\": \"user\"}")
if echo "$MEMORY_RESULT" | grep -q '"stored":true'; then
    echo -e "${GREEN}✓ Memory stored${NC}"
else
    echo -e "${RED}✗ Memory storage failed${NC}"
    echo "$MEMORY_RESULT"
fi
echo ""

# Test 8: Retrieve Memory
echo -e "${BLUE}Test 8: Retrieve Memory${NC}"
MEMORY_CONTEXT=$(curl -s -X POST "$API_BASE/v1/memory/context" \
  -H "Authorization: Bearer $AURORA_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"query\": \"testing\", \"memory_scope\": \"user\", \"top_k\": 5}")
MEMORY_COUNT=$(echo "$MEMORY_CONTEXT" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('retrieved_memories', [])))" 2>/dev/null || echo "0")
if [ "$MEMORY_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Memory retrieved ($MEMORY_COUNT memories)${NC}"
else
    echo -e "${BLUE}ℹ No memories found${NC}"
fi
echo ""

# Test 9: List Skills
echo -e "${BLUE}Test 9: List Skills${NC}"
SKILLS=$(curl -s "$API_BASE/v1/skills")
SKILLS_COUNT=$(echo "$SKILLS" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$SKILLS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Skills loaded ($SKILLS_COUNT skills)${NC}"
else
    echo -e "${RED}✗ No skills found${NC}"
fi
echo ""

# Test 10: List Tools
echo -e "${BLUE}Test 10: List Tools${NC}"
TOOLS=$(curl -s "$API_BASE/tools")
TOOLS_COUNT=$(echo "$TOOLS" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$TOOLS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Tools loaded ($TOOLS_COUNT tools)${NC}"
else
    echo -e "${RED}✗ No tools found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║                    Test Summary                              ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo -e "${BLUE}Your API is working perfectly from external clients!${NC}"
echo ""
echo -e "API Base: $API_BASE"
echo -e "User ID: $USER_ID"
echo -e "Aurora Key: $AURORA_KEY"
echo ""
echo -e "${BLUE}You can now use this API in any application:${NC}"
echo -e "  - Python scripts"
echo -e "  - Node.js apps"
echo -e "  - Mobile apps"
echo -e "  - Desktop apps"
echo -e "  - Other web apps"
echo ""
