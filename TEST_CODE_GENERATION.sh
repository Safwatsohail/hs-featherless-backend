#!/bin/bash

# Test Code Generation with H&S Layer
# This script tests if the API generates proper code with syntax highlighting

echo "🧪 Testing H&S Layer Code Generation"
echo "======================================"
echo ""

AURORA_KEY="aurora_live_KEt1b2Y--l2QJjNb7lmK2XfokgKx4pfu"
USER_ID="00000000-0000-0000-0000-000000000001"

echo "📝 Test 1: Simple Python Function"
echo "Request: Write a Python function to add two numbers"
echo ""

curl -X POST http://localhost:8000/v1/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AURORA_KEY" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"input\": \"Write a Python function to add two numbers\",
    \"provider\": \"openrouter\",
    \"model\": \"openrouter/auto\",
    \"memory_scope\": \"user\"
  }" 2>&1 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    output = data.get('output', '')
    print('Response:')
    print(output)
    print('')
    if '```python' in output or '```' in output:
        print('✅ PASS: Code block found with proper markdown formatting')
    else:
        print('❌ FAIL: No code block found - code might be in paragraph form')
except Exception as e:
    print(f'❌ ERROR: {e}')
"

echo ""
echo "======================================"
echo "📝 Test 2: Memory Capture"
echo "Request: My name is John Smith and I prefer TypeScript"
echo ""

curl -X POST http://localhost:8000/v1/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AURORA_KEY" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"input\": \"My name is John Smith and I prefer TypeScript\",
    \"provider\": \"openrouter\",
    \"model\": \"openrouter/auto\",
    \"memory_scope\": \"user\"
  }" 2>&1 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('✅ Memory test completed')
    print('Check memory tab in frontend to verify facts were captured')
except Exception as e:
    print(f'❌ ERROR: {e}')
"

echo ""
echo "======================================"
echo "✅ Tests Complete!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Go to Dashboard → Compare tab"
echo "3. Enter Aurora Key: $AURORA_KEY"
echo "4. Enter User ID: $USER_ID"
echo "5. Ask: 'Write a Python game'"
echo "6. Verify code appears with proper syntax highlighting"
