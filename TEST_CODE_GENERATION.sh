#!/bin/bash

# Test Code Generation with Syntax Highlighting
# This tests the enhanced code generation and frontend rendering

API_BASE="http://localhost:8000"
AURORA_KEY="aurora_live_6BYZvwXhx0qmmifrwTYtUnRpLydoeSGy"
USER_ID="00000000-0000-0000-0000-000000000001"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                    🧪 Testing Code Generation & Styling                      ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Simple Python function
echo "📝 Test 1: Simple Python Function"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s -X POST "${API_BASE}/v1/chat" \
  -H "Authorization: Bearer ${AURORA_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"input\": \"Write a Python function to calculate factorial with type hints\",
    \"provider\": \"openrouter\",
    \"model\": \"openrouter/auto\"
  }")

OUTPUT=$(echo "$RESPONSE" | jq -r '.output' 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$OUTPUT" ]; then
    echo "✅ API Response received"
    
    # Check for proper code blocks
    if echo "$OUTPUT" | grep -q '```python'; then
        echo "✅ Contains proper code block opening (```python)"
    else
        echo "❌ Missing proper code block opening"
    fi
    
    if echo "$OUTPUT" | grep -q 'def.*->.*:'; then
        echo "✅ Contains type hints (-> return type)"
    else
        echo "⚠️  Missing type hints"
    fi
    
    if echo "$OUTPUT" | grep -q '"""'; then
        echo "✅ Contains docstring"
    else
        echo "⚠️  Missing docstring"
    fi
    
    # Count closing backticks
    OPEN_TICKS=$(echo "$OUTPUT" | grep -o '```' | wc -l)
    if [ $((OPEN_TICKS % 2)) -eq 0 ]; then
        echo "✅ Balanced code block markers"
    else
        echo "❌ Unbalanced code block markers"
    fi
    
    echo ""
    echo "📄 Response Preview:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$OUTPUT" | head -20
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ Failed to get response"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo ""

# Test 2: Check for meta-commentary
echo "📝 Test 2: Clean Response - No Meta-Commentary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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

if [ $? -eq 0 ] && [ ! -z "$OUTPUT2" ]; then
    echo "✅ API Response received"
    
    # Check for unwanted patterns
    if echo "$OUTPUT2" | grep -qi "as an ai"; then
        echo "⚠️  Contains 'As an AI' meta-commentary"
    else
        echo "✅ No 'As an AI' meta-commentary"
    fi
    
    if echo "$OUTPUT2" | grep -qi "i'm just a"; then
        echo "⚠️  Contains 'I'm just a' meta-commentary"
    else
        echo "✅ No 'I'm just a' meta-commentary"
    fi
    
    if echo "$OUTPUT2" | grep -qi "here's my response"; then
        echo "⚠️  Contains 'Here's my response' meta-commentary"
    else
        echo "✅ No 'Here's my response' meta-commentary"
    fi
    
    echo ""
    echo "📄 Response:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$OUTPUT2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ Failed to get response"
fi

echo ""
echo ""

# Test 3: Frontend rendering check
echo "📝 Test 3: Frontend Rendering"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)

    if echo "$FRONTEND_STATUS" = "200"; then
        echo "✅ Frontend is running on http://localhost:3000"
    
    # Check if main.js has the formatMarkdownish function
    if curl -s http://localhost:3000/main.js | grep -q "formatMarkdownish"; then
        echo "✅ formatMarkdownish function exists"
    else
        echo "❌ formatMarkdownish function missing"
    fi
    
    # Check if main.js has syntax highlighting
    if curl -s http://localhost:3000/main.js | grep -q "highlightCode"; then
        echo "✅ highlightCode function exists"
    else
        echo "❌ highlightCode function missing"
    fi
    
    # Check if CSS has syntax highlighting styles
    if curl -s http://localhost:3000/style.css | grep -q "syntax-keyword"; then
        echo "✅ Syntax highlighting CSS exists"
    else
        echo "❌ Syntax highlighting CSS missing"
    fi
else
    echo "❌ Frontend not responding - HTTP $FRONTEND_STATUS"
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
echo "3. Try: 'Write a Python function to calculate fibonacci with type hints'"
echo "4. Verify:"
echo "   ✅ Code has proper syntax highlighting with colors"
echo "   ✅ Code blocks have dark background"
echo "   ✅ Type hints are visible"
echo "   ✅ Docstrings are formatted"
echo "   ✅ Copy button works"
echo "   ✅ No meta-commentary"
echo ""
echo "💡 If you see plain text, hard refresh: Cmd+Shift+R or Ctrl+Shift+R"
echo ""
