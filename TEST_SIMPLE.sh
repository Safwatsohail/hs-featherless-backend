#!/bin/bash

# Simple test for code generation

API_BASE="http://localhost:8000"
AURORA_KEY="aurora_live_6BYZvwXhx0qmmifrwTYtUnRpLydoeSGy"
USER_ID="00000000-0000-0000-0000-000000000001"

echo "Testing Code Generation..."
echo ""

# Test code generation
RESPONSE=$(curl -s -X POST "${API_BASE}/v1/chat" \
  -H "Authorization: Bearer ${AURORA_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"input\": \"Write a Python function to calculate factorial with type hints and docstring\",
    \"provider\": \"openrouter\",
    \"model\": \"openrouter/auto\"
  }")

OUTPUT=$(echo "$RESPONSE" | jq -r '.output' 2>/dev/null)

if [ ! -z "$OUTPUT" ]; then
    echo "✅ Got response from API"
    echo ""
    echo "Response:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$OUTPUT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Check for code blocks
    if echo "$OUTPUT" | grep -q '```python'; then
        echo "✅ Has proper code block"
    else
        echo "⚠️  No code block found"
    fi
    
    # Check for type hints
    if echo "$OUTPUT" | grep -q '->'; then
        echo "✅ Has type hints"
    else
        echo "⚠️  No type hints"
    fi
    
    # Check for docstring
    if echo "$OUTPUT" | grep -q '"""'; then
        echo "✅ Has docstring"
    else
        echo "⚠️  No docstring"
    fi
else
    echo "❌ Failed to get response"
    echo "$RESPONSE"
fi

echo ""
echo "✅ Test complete!"
echo ""
echo "Now open http://localhost:3000#dashboard and test in the browser!"
