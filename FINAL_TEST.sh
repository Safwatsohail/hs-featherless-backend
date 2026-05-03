#!/bin/bash

# Final comprehensive test for code generation and tool usage

API_BASE="http://localhost:8000"
AURORA_KEY="aurora_live_6BYZvwXhx0qmmifrwTYtUnRpLydoeSGy"
USER_ID="00000000-0000-0000-0000-000000000001"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                    🧪 FINAL TEST - Code Generation & Tools                   ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 3

# Test 1: Code Generation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Test 1: Code Generation - Like Claude"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Prompt: Write a Python function to calculate fibonacci with type hints and docstring"
echo ""

RESPONSE=$(curl -s -X POST "${API_BASE}/v1/chat" \
  -H "Authorization: Bearer ${AURORA_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"input\": \"Write a Python function to calculate fibonacci with type hints and docstring\",
    \"provider\": \"openrouter\",
    \"model\": \"openrouter/auto\"
  }")

OUTPUT=$(echo "$RESPONSE" | jq -r '.output' 2>/dev/null)
SKILL=$(echo "$RESPONSE" | jq -r '.skill' 2>/dev/null)
TOOLS=$(echo "$RESPONSE" | jq -r '.tool_calls | length' 2>/dev/null)

if [ ! -z "$OUTPUT" ] && [ "$OUTPUT" != "null" ]; then
    echo "✅ Got response from API"
    echo "📊 Skill used: $SKILL"
    echo "🔧 Tools used: $TOOLS"
    echo ""
    echo "📄 Response:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$OUTPUT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Validation checks
    echo "🔍 Validation:"
    
    if echo "$OUTPUT" | grep -q '```python'; then
        echo "  ✅ Has proper code block (```python)"
    else
        echo "  ❌ Missing proper code block"
    fi
    
    if echo "$OUTPUT" | grep -q '"""'; then
        echo "  ✅ Has docstring"
    else
        echo "  ⚠️  Missing docstring"
    fi
    
    if echo "$OUTPUT" | grep -q 'def.*int.*->.*int'; then
        echo "  ✅ Has type hints"
    else
        echo "  ⚠️  Missing type hints"
    fi
    
    if echo "$OUTPUT" | grep -qi "as an ai\|i'm just\|here's my response"; then
        echo "  ⚠️  Contains meta-commentary"
    else
        echo "  ✅ No meta-commentary"
    fi
    
    BACKTICKS=$(echo "$OUTPUT" | grep -o '```' | wc -l | tr -d ' ')
    if [ $((BACKTICKS % 2)) -eq 0 ]; then
        echo "  ✅ Balanced code blocks"
    else
        echo "  ❌ Unbalanced code blocks"
    fi
else
    echo "❌ Failed to get response"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo ""

# Test 2: Simple greeting (no code)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Test 2: Simple Greeting - Clean Response"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Prompt: hi"
echo ""

RESPONSE2=$(curl -s -X POST "${API_BASE}/v1/chat" \
  -H "Authorization: Bearer ${AURORA_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"input\": \"hi\",
    \"provider\": \"openrouter\",
    \"model\": \"openrouter/auto\"
  }")

OUTPUT2=$(echo "$RESPONSE2" | jq -r '.output' 2>/dev/null)

if [ ! -z "$OUTPUT2" ] && [ "$OUTPUT2" != "null" ]; then
    echo "✅ Got response"
    echo ""
    echo "📄 Response:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$OUTPUT2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "🔍 Validation:"
    if echo "$OUTPUT2" | grep -qi "as an ai\|i'm just\|here's my response"; then
        echo "  ⚠️  Contains meta-commentary"
    else
        echo "  ✅ No meta-commentary"
    fi
    
    if [ ${#OUTPUT2} -lt 500 ]; then
        echo "  ✅ Concise response"
    else
        echo "  ⚠️  Response is too long"
    fi
else
    echo "❌ Failed to get response"
fi

echo ""
echo ""

# Test 3: Memory test
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Test 3: Memory System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Prompt: My name is Alex and I prefer TypeScript"
echo ""

RESPONSE3=$(curl -s -X POST "${API_BASE}/v1/chat" \
  -H "Authorization: Bearer ${AURORA_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"input\": \"My name is Alex and I prefer TypeScript\",
    \"provider\": \"openrouter\",
    \"model\": \"openrouter/auto\"
  }")

OUTPUT3=$(echo "$RESPONSE3" | jq -r '.output' 2>/dev/null)
MEMORY_HITS=$(echo "$RESPONSE3" | jq -r '.memory_hits' 2>/dev/null)

if [ ! -z "$OUTPUT3" ] && [ "$OUTPUT3" != "null" ]; then
    echo "✅ Got response"
    echo "📊 Memory hits: $MEMORY_HITS"
    echo ""
    echo "📄 Response:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$OUTPUT3"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "🔍 Validation:"
    if echo "$OUTPUT3" | grep -qi "alex"; then
        echo "  ✅ Acknowledged name"
    else
        echo "  ⚠️  Didn't acknowledge name"
    fi
    
    if echo "$OUTPUT3" | grep -qi "typescript"; then
        echo "  ✅ Acknowledged preference"
    else
        echo "  ⚠️  Didn't acknowledge preference"
    fi
else
    echo "❌ Failed to get response"
fi

echo ""
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                              ✅ TESTS COMPLETE                               ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "1. Open http://localhost:3000#dashboard in your browser"
echo "2. Go to 'A/B Chat' tab"
echo "3. Test these prompts:"
echo ""
echo "   📝 Code Generation:"
echo "      'Write a Python function to sort a list with type hints'"
echo ""
echo "   🧠 Memory Test:"
echo "      'My name is John and I work at Google'"
echo "      Then: 'What do you know about me?'"
echo ""
echo "   🔧 Tool Usage:"
echo "      'What are the latest React 19 features?'"
echo ""
echo "4. Verify:"
echo "   ✅ Code has syntax highlighting with colors"
echo "   ✅ Code blocks have dark background"
echo "   ✅ Type hints visible"
echo "   ✅ Docstrings formatted"
echo "   ✅ No meta-commentary"
echo "   ✅ Tool usage shown if tools used"
echo ""
echo "💡 Hard refresh if needed: Cmd+Shift+R or Ctrl+Shift+R"
echo ""
