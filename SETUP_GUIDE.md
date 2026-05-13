# H&S Layer - Complete Setup & Usage Guide

## ✅ What's Been Implemented

### 1. Device-Based User ID Detection
- **Automatic**: Each device gets a unique user ID based on browser fingerprint
- **Persistent**: Stored in localStorage, same across sessions
- **No Authentication**: Works without login
- **Different Devices**: Different devices get different IDs

### 2. Memory System (Fully Working)
- ✅ Store facts about users
- ✅ Retrieve memory context
- ✅ Dynamic memory updates
- ✅ Shared across all Aurora keys for same user

### 3. Code Samples in Dev Tab
- ✅ All 7 code snippets rendering (quickstart, chat, compare, memory, skill, tools, errors)
- ✅ Multiple languages: curl, Python, JavaScript, TypeScript
- ✅ Real API key included: `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`
- ✅ Device user ID references: `YOUR_DEVICE_USER_ID`

### 4. Tools & Skills Integration
- ✅ 1,080+ pre-built skills available
- ✅ 55+ tools (web search, code execution, etc.)
- ✅ Auto-routing to best skill
- ✅ Manual skill invocation

---

## 🚀 Quick Start

### Step 1: Get Your Device User ID

Open the browser console (F12) and you'll see:
```
✓ Generated new device user ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Or use this code:
```javascript
const deviceId = localStorage.getItem("hs_device_user_id");
console.log("Your Device User ID:", deviceId);
```

### Step 2: Store Your API Key

Replace `YOUR_DEVICE_USER_ID` with your actual device ID:

```bash
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_DEVICE_USER_ID",
    "provider": "openrouter",
    "api_key": "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"
  }'
```

### Step 3: Generate Aurora Key

```bash
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_DEVICE_USER_ID",
    "name": "My Project Key",
    "scopes": ["chat", "memory", "tools", "skills"]
  }'
```

Response:
```json
{
  "api_key": "aurora_live_XXXXXXXXXXXXXXXX",
  "key_prefix": "aurora_live_XXXXXX",
  ...
}
```

### Step 4: Use the API

Replace `aurora_live_XXXXXXXXXXXXXXXX` with your Aurora key:

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_XXXXXXXXXXXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_DEVICE_USER_ID",
    "input": "What programming language should I use?",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openrouter/auto"
  }'
```

---

## 📚 Complete API Examples

### Python

```python
import requests

API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_YOUR_KEY"
USER_ID = "YOUR_DEVICE_USER_ID"

headers = {
    "Authorization": f"Bearer {AURORA_KEY}",
    "Content-Type": "application/json"
}

# 1. Store memory
requests.post(f"{API_BASE}/v1/memory", headers=headers, json={
    "user_id": USER_ID,
    "text": "I prefer Python over JavaScript",
    "kind": "preference",
    "memory_scope": "user"
})

# 2. Retrieve memory
response = requests.post(f"{API_BASE}/v1/memory/context", headers=headers, json={
    "user_id": USER_ID,
    "query": "programming preferences",
    "memory_scope": "user",
    "top_k": 10
})
print(response.json())

# 3. Chat with memory
response = requests.post(f"{API_BASE}/v1/run", headers=headers, json={
    "user_id": USER_ID,
    "input": "What language should I use for my project?",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openrouter/auto"
})
data = response.json()
print(f"Response: {data['output']}")
print(f"Skill: {data['skill']}")
print(f"Tools: {[t['name'] for t in data['tool_calls']]}")

# 4. Compare raw vs enhanced
response = requests.post(f"{API_BASE}/v1/compare", headers=headers, json={
    "user_id": USER_ID,
    "input": "Explain machine learning",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
})
data = response.json()
print(f"Raw: {data['baseline']['output'][:100]}")
print(f"Enhanced: {data['tuned']['output'][:100]}")
print(f"Latency improvement: {data['delta']['latency_gap_ms']}ms")
```

### JavaScript

```javascript
const API_BASE = "http://localhost:8000";
const AURORA_KEY = "aurora_live_YOUR_KEY";
const USER_ID = "YOUR_DEVICE_USER_ID";

const headers = {
  "Authorization": `Bearer ${AURORA_KEY}`,
  "Content-Type": "application/json"
};

// 1. Store memory
async function storeMemory(text) {
  const res = await fetch(`${API_BASE}/v1/memory`, {
    method: "POST", headers,
    body: JSON.stringify({
      user_id: USER_ID,
      text,
      kind: "preference",
      memory_scope: "user"
    })
  });
  return res.json();
}

// 2. Get memory
async function getMemory(query) {
  const res = await fetch(`${API_BASE}/v1/memory/context`, {
    method: "POST", headers,
    body: JSON.stringify({
      user_id: USER_ID,
      query,
      memory_scope: "user",
      top_k: 10
    })
  });
  return res.json();
}

// 3. Chat
async function chat(message) {
  const res = await fetch(`${API_BASE}/v1/run`, {
    method: "POST", headers,
    body: JSON.stringify({
      user_id: USER_ID,
      input: message,
      memory_scope: "user",
      provider: "openrouter",
      model: "openrouter/auto"
    })
  });
  const data = await res.json();
  return {
    response: data.output,
    skill: data.skill,
    tools: data.tool_calls.map(t => t.name)
  };
}

// 4. Compare
async function compare(message) {
  const res = await fetch(`${API_BASE}/v1/compare`, {
    method: "POST", headers,
    body: JSON.stringify({
      user_id: USER_ID,
      input: message,
      provider: "openrouter",
      model: "openrouter/auto",
      memory_scope: "user"
    })
  });
  const data = await res.json();
  return {
    raw: data.baseline.output,
    enhanced: data.tuned.output,
    skill: data.tuned.skill,
    latencyGap: data.delta.latency_gap_ms
  };
}

// Usage
(async () => {
  await storeMemory("I prefer Python");
  const memory = await getMemory("programming");
  console.log("Memory:", memory);
  
  const result = await chat("What language should I use?");
  console.log("Chat:", result);
  
  const comp = await compare("Explain AI");
  console.log("Comparison:", comp);
})();
```

---

## 🔑 API Key Information

### Your OpenRouter Key
```
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
```

### How It Works
1. **Store Once**: Your OpenRouter key is stored securely on the backend
2. **Generate Aurora Key**: Get an enhanced key with memory, tools, and skills
3. **Use Everywhere**: Same Aurora key works across all your projects
4. **Shared Memory**: Memory is shared across all Aurora keys for the same user

---

## 📊 Features

### Memory System
- Store facts about users (preferences, interests, etc.)
- Retrieve memory context for any query
- Memory is shared across all Aurora keys for the same user
- Automatic fact extraction from conversations

### Skills & Tools
- 1,080+ pre-built skills
- 55+ tools (web search, code execution, etc.)
- Auto-routing to best skill based on input
- Manual skill invocation available

### Comparison
- Compare raw vs enhanced responses
- See latency improvements
- Track tool usage and memory hits

### Device User ID
- Automatically generated based on browser fingerprint
- Same device = same user ID
- Different device = different user ID
- No authentication needed
- Persistent across sessions

---

## 🧪 Testing

### Test Memory Storage
```bash
curl -X POST http://localhost:8000/v1/memory \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_DEVICE_USER_ID",
    "text": "I prefer Python over JavaScript",
    "kind": "preference",
    "memory_scope": "user"
  }'
```

### Test Memory Retrieval
```bash
curl -X POST http://localhost:8000/v1/memory/context \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_DEVICE_USER_ID",
    "query": "programming preferences",
    "memory_scope": "user",
    "top_k": 10
  }'
```

### Test Chat with Memory
```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_DEVICE_USER_ID",
    "input": "What programming language should I use?",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openrouter/auto"
  }'
```

---

## 📖 Dev Docs Tab

All code samples are available in the **Dev Docs** tab of the dashboard:
- ✅ Quickstart
- ✅ Chat with Memory & Skills
- ✅ A/B Compare Raw vs Enhanced
- ✅ Store & Retrieve Memory
- ✅ Invoke a Specific Skill
- ✅ Execute Tools
- ✅ Error Handling

Languages supported:
- cURL
- Python
- JavaScript
- TypeScript

---

## 🎯 Next Steps

1. **Get Your Device ID**: Check browser console for your device user ID
2. **Store API Key**: Use the curl command above to store your OpenRouter key
3. **Generate Aurora Key**: Create your enhanced key
4. **Start Using**: Use the API examples above in your projects
5. **Check Dev Docs**: View all code samples in the dashboard

---

## ❓ FAQ

**Q: Do I need to authenticate?**
A: No! Your device ID is automatically generated and persisted.

**Q: Can I use the same Aurora key on different devices?**
A: Yes! The same Aurora key works on all devices for the same user.

**Q: Is my API key secure?**
A: Yes! Your OpenRouter key is encrypted and never exposed in responses.

**Q: Can I update my API key?**
A: Yes! Just store a new key with the same user ID.

**Q: How do I get my device user ID?**
A: Check the browser console (F12) on page load, or use `localStorage.getItem("hs_device_user_id")`

---

## 🚀 You're All Set!

Everything is ready to use. Start building with the H&S Layer API!

For more examples, check the **Dev Docs** tab in the dashboard.
