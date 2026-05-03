# 🧪 Testing Guide

Comprehensive testing guide for H&S Layer.

---

## 🚀 Quick Test

```bash
./TEST_CODE_GENERATION.sh
```

This will test:
- ✅ Code generation with proper syntax
- ✅ Memory capture and storage
- ✅ API connectivity

---

## 📋 Manual Testing

### 1. Health Check

```bash
curl http://localhost:8000/healthz
```

**Expected:**
```json
{"ok": true}
```

---

### 2. API Key Generation

```bash
# Store provider key
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "provider": "openrouter",
    "api_key": "sk-or-v1-your-key"
  }'

# Generate Aurora key
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "name": "Test Key",
    "scopes": ["chat", "memory", "tools", "skills"]
  }'
```

**Expected:**
```json
{
  "id": "uuid",
  "user_id": "test-user",
  "api_key": "aurora_live_xxxxx",
  ...
}
```

---

### 3. Code Generation Test

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "input": "Write a Python function to add two numbers",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'
```

**Expected:**
- ✅ Response contains ` ```python ` code block
- ✅ Code has proper indentation
- ✅ Code is complete and working
- ✅ No paragraph-style descriptions

---

### 4. Memory Test

```bash
# Store facts
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "input": "My name is Alice and I prefer TypeScript",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'

# Retrieve memory
curl -X POST http://localhost:8000/v1/memory/context \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "query": "user preferences",
    "memory_scope": "user",
    "top_k": 10
  }'
```

**Expected:**
- ✅ Memory contains "User's name is Alice"
- ✅ Memory contains "User prefers TypeScript"

---

### 5. Tool Usage Test

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "input": "What are the latest React 19 features?",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'
```

**Expected:**
- ✅ `tool_calls` array contains `web_search`
- ✅ Response includes information from web search
- ✅ Response is structured with headers and lists

---

### 6. A/B Compare Test

```bash
curl -X POST http://localhost:8000/v1/compare \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "input": "Write a Python function to calculate fibonacci",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'
```

**Expected:**
- ✅ `baseline` contains raw LLM response
- ✅ `tuned` contains enhanced response with better formatting
- ✅ `delta` shows performance comparison

---

### 7. Skills Test

```bash
# List all skills
curl http://localhost:8000/v1/skills \
  -H "Authorization: Bearer aurora_live_YOUR_KEY"

# Invoke specific skill
curl -X POST http://localhost:8000/v1/skills/code_assistant \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "input": "Review this code for bugs"
  }'
```

**Expected:**
- ✅ Skills list contains 1,080+ skills
- ✅ Specific skill invocation works

---

### 8. Tools Test

```bash
# List all tools
curl http://localhost:8000/tools \
  -H "Authorization: Bearer aurora_live_YOUR_KEY"
```

**Expected:**
- ✅ Tools list contains 55+ tools
- ✅ Each tool has name, description, input_schema

---

## 🎨 Frontend Testing

### 1. Open Dashboard

```
http://localhost:3000
```

**Test:**
- ✅ Landing page loads
- ✅ Navigation works
- ✅ Dashboard loads

---

### 2. A/B Compare Tab

**Test:**
1. Enter Aurora key and User ID
2. Type: "Write a Python game"
3. Click "Run Comparison"

**Expected:**
- ✅ Both panes show responses
- ✅ Enhanced pane has better formatting
- ✅ Code blocks have syntax highlighting
- ✅ Metrics show tool usage and memory hits

---

### 3. Memory Tab

**Test:**
1. Go to Memory tab
2. Check stored facts

**Expected:**
- ✅ Facts are displayed in table
- ✅ Can filter by tag
- ✅ Can search facts
- ✅ Can edit/delete facts

---

### 4. Skills Tab

**Test:**
1. Go to Skills Store tab
2. Browse skills

**Expected:**
- ✅ 1,080+ skills displayed
- ✅ Can toggle skills on/off
- ✅ Skills are categorized

---

### 5. Dev Docs Tab

**Test:**
1. Go to Dev Docs tab
2. Switch between languages (cURL, Python, JS, TS)

**Expected:**
- ✅ Code samples display for each language
- ✅ Code has syntax highlighting
- ✅ Copy button works
- ✅ Examples are accurate

---

## 🔍 Integration Testing

### Python Integration

```python
import requests

API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_YOUR_KEY"
USER_ID = "test-user"

def test_chat():
    response = requests.post(
        f"{API_BASE}/v1/run",
        headers={"Authorization": f"Bearer {AURORA_KEY}"},
        json={
            "user_id": USER_ID,
            "input": "Write a Python function to add numbers",
            "provider": "openrouter",
            "model": "openrouter/auto",
            "memory_scope": "user"
        }
    )
    data = response.json()
    assert "output" in data
    assert "```python" in data["output"]
    assert data["skill"] is not None
    print("✅ Chat test passed")

def test_memory():
    # Store
    requests.post(
        f"{API_BASE}/v1/memory",
        headers={"Authorization": f"Bearer {AURORA_KEY}"},
        json={
            "user_id": USER_ID,
            "text": "User prefers Python",
            "kind": "preference",
            "memory_scope": "user"
        }
    )
    
    # Retrieve
    response = requests.post(
        f"{API_BASE}/v1/memory/context",
        headers={"Authorization": f"Bearer {AURORA_KEY}"},
        json={
            "user_id": USER_ID,
            "query": "preferences",
            "memory_scope": "user",
            "top_k": 10
        }
    )
    data = response.json()
    assert len(data["retrieved_memories"]) > 0
    print("✅ Memory test passed")

if __name__ == "__main__":
    test_chat()
    test_memory()
    print("\n✅ All tests passed!")
```

---

## 🐛 Debugging

### Check Backend Logs

```bash
tail -f backend.log
```

### Check Frontend Logs

```bash
# Open browser console (F12)
# Check for JavaScript errors
```

### Test API Directly

```bash
# Test health
curl http://localhost:8000/healthz

# Test with verbose output
curl -v -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","input":"test"}'
```

---

## 📊 Performance Testing

### Load Test

```bash
# Install Apache Bench
# brew install httpd (macOS)
# apt-get install apache2-utils (Linux)

# Run load test
ab -n 100 -c 10 \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -p test_payload.json \
  http://localhost:8000/v1/run
```

**Expected:**
- ✅ 100 requests complete successfully
- ✅ Average response time < 5 seconds
- ✅ No errors

---

## ✅ Test Checklist

### Backend
- [ ] Health check returns OK
- [ ] API key generation works
- [ ] Chat endpoint returns proper responses
- [ ] Code blocks have proper markdown syntax
- [ ] Memory storage works
- [ ] Memory retrieval works
- [ ] Tool execution works
- [ ] Skills routing works
- [ ] A/B compare works

### Frontend
- [ ] Landing page loads
- [ ] Dashboard loads
- [ ] A/B Compare tab works
- [ ] Memory tab displays facts
- [ ] Skills tab shows 1,080+ skills
- [ ] Tools tab shows 55+ tools
- [ ] Dev Docs tab shows code samples
- [ ] Code syntax highlighting works

### Integration
- [ ] Python client works
- [ ] JavaScript client works
- [ ] cURL examples work
- [ ] Memory persists across requests
- [ ] Tools are used automatically
- [ ] Skills are selected correctly

---

## 🎉 Success Criteria

Your H&S Layer is working correctly if:

- ✅ All API endpoints respond
- ✅ Code generation uses proper markdown blocks
- ✅ Memory captures and retrieves facts
- ✅ Tools are used automatically
- ✅ Skills route correctly
- ✅ Frontend displays everything properly
- ✅ Syntax highlighting works
- ✅ No errors in logs

---

**Happy testing! 🚀**
