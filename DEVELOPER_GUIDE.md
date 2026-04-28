# 🔧 Developer Guide - H&S Layer (Local Setup)

## 🎯 Overview

H&S Layer is a **local-only** AI orchestration platform that enhances Featherless.ai API keys with:
- **Unified Memory** - Shared across all API keys for the same user
- **1,080+ Skills** - Auto-routing to specialized domain experts
- **50+ Tools** - Web search, code analysis, database queries
- **Intelligent Caching** - 40-60% cost reduction

## 🚀 Quick Start (Local Only)

### 1. First Time Setup

```bash
# Install backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Backend is configured for LOCAL ONLY (127.0.0.1)
# Check backend/.env - HOST should be 127.0.0.1
```

### 2. Start Everything

```bash
./start.sh
```

This starts:
- **Backend**: http://localhost:8000 (LOCAL ONLY - 127.0.0.1)
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### 3. Generate Your Enhanced API Key

1. **Get a Featherless API Key**
   - Go to https://featherless.ai
   - Sign up and get your API key (starts with `fl_`)

2. **Open the Frontend**
   - Navigate to http://localhost:3000
   - Click "Get Enhanced Key" or "Sign in"
   - Go through the onboarding flow

3. **Bridge Your Key**
   - Paste your Featherless key (fl_...)
   - Click "Generate Enhanced Key"
   - You'll get an Aurora key (aurora_live_...)

4. **Use Your Enhanced Key**
   - Copy the Aurora key
   - Use it in your API calls instead of the raw Featherless key

## 🔑 API Key Flow

### How Keys Work

```
Featherless Key (fl_xxx)
    ↓ [Store in backend]
    ↓ [Generate Aurora Key]
Aurora Key (aurora_live_xxx)
    ↓ [Use in API calls]
    ↓ [Backend decrypts & uses Featherless key]
    ↓ [Adds memory, skills, tools]
Enhanced Response
```

### Memory Sharing Across Keys

**All Aurora keys for the same user share memory!**

```javascript
// User creates multiple Aurora keys
const key1 = "aurora_live_ABC123...";
const key2 = "aurora_live_XYZ789...";

// Both keys share the same memory
// If you tell key1: "I prefer JSON responses"
// Then key2 will also remember this preference!
```

This is controlled by `user_id` and `memory_scope`:

```javascript
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "memory_scope": "user",  // Shared across all keys for this user
  "input": "Remember I prefer JSON"
}
```

## 📡 API Usage Examples

### 1. Basic Chat Request

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Debug my Python API performance",
    "memory_scope": "user"
  }'
```

### 2. Compare Raw vs Enhanced

```bash
curl -X POST http://localhost:8000/compare \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "What are the latest React 19 features?",
    "provider": "featherless",
    "model": "gpt-4.1-mini"
  }'
```

### 3. Store Memory

```bash
curl -X POST http://localhost:8000/v1/memory \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "text": "User prefers JSON responses",
    "kind": "preference",
    "memory_scope": "user"
  }'
```

### 4. Retrieve Memory Context

```bash
curl -X POST http://localhost:8000/v1/memory/context \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "query": "user preferences",
    "memory_scope": "user"
  }'
```

### 5. List Available Skills

```bash
curl http://localhost:8000/v1/skills
```

### 6. Invoke Specific Skill

```bash
curl -X POST http://localhost:8000/v1/skills/research \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Latest AI developments in 2025"
  }'
```

## 🧠 Memory Scopes

Control how memory is shared:

| Scope | Description | Use Case |
|-------|-------------|----------|
| `user` | Shared across all API keys for same user | Default - remembers preferences |
| `workspace` | Shared within a project/workspace | Team collaboration |
| `conversation` | Isolated per conversation | Private chats |
| `global` | Shared across all users | Public knowledge base |

Example:

```javascript
// Personal preference (shared across all your keys)
{
  "memory_scope": "user",
  "input": "I prefer TypeScript over JavaScript"
}

// Project-specific (shared in this workspace only)
{
  "memory_scope": "workspace",
  "context_key": "project-alpha",
  "input": "Our API uses REST not GraphQL"
}

// Private conversation (not shared)
{
  "memory_scope": "conversation",
  "conversation_id": "conv-123",
  "input": "Confidential: Q4 revenue is $2M"
}
```

## 🛠️ Frontend Integration

### JavaScript Example

```javascript
const API_BASE = "http://localhost:8000";
const AURORA_KEY = "aurora_live_YOUR_KEY";
const USER_ID = "00000000-0000-0000-0000-000000000001";

async function chat(message) {
  const response = await fetch(`${API_BASE}/v1/run`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${AURORA_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: USER_ID,
      input: message,
      memory_scope: "user"
    })
  });
  
  return await response.json();
}

// Usage
const result = await chat("What's the weather in Tokyo?");
console.log(result.output);
console.log("Skill used:", result.skill);
console.log("Tools used:", result.tool_calls);
```

### React Example

```jsx
import { useState } from 'react';

function ChatComponent() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState(null);
  
  const sendMessage = async () => {
    const res = await fetch('http://localhost:8000/v1/run', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer aurora_live_YOUR_KEY',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: '00000000-0000-0000-0000-000000000001',
        input: message,
        memory_scope: 'user'
      })
    });
    
    const data = await res.json();
    setResponse(data);
  };
  
  return (
    <div>
      <input 
        value={message} 
        onChange={(e) => setMessage(e.target.value)} 
      />
      <button onClick={sendMessage}>Send</button>
      {response && (
        <div>
          <p>{response.output}</p>
          <small>Skill: {response.skill}</small>
        </div>
      )}
    </div>
  );
}
```

## 🔒 Security (Local Only)

### Current Setup

- **Backend**: Bound to `127.0.0.1` (localhost only)
- **Frontend**: Served on `localhost:3000`
- **Database**: Local SQLite file
- **API Keys**: Encrypted with Fernet (MASTER_KEY)

### Why Local Only?

1. **No external access** - Only your machine can access the API
2. **No HTTPS needed** - Local traffic is secure
3. **Fast development** - No network latency
4. **Privacy** - Your data never leaves your machine

### If You Need Remote Access

**DON'T** change `HOST=0.0.0.0` without proper security:

1. Add authentication middleware
2. Use HTTPS with valid certificates
3. Add rate limiting
4. Use environment-specific API keys
5. Deploy behind a reverse proxy (nginx)

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (localhost:3000)             │
│  - Landing page                                          │
│  - API key bridge                                        │
│  - Dashboard (compare, memory, skills, tools)            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP (localhost only)
┌────────────────────▼────────────────────────────────────┐
│              Backend API (localhost:8000)                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  API Gateway (FastAPI)                           │   │
│  │  - CORS enabled for localhost:3000               │   │
│  │  - Aurora key authentication                     │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  Orchestrator                                     │   │
│  │  - Skill selection (1,080+ skills)               │   │
│  │  - Tool planning (50+ tools)                     │   │
│  │  - Memory retrieval                              │   │
│  │  - LLM routing                                   │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌─────────┬────────┴────────┬──────────┬──────────┐   │
│  │         │                 │          │          │   │
│  ▼         ▼                 ▼          ▼          ▼   │
│ Skills   Tools            Memory      Cache      LLM   │
│ Engine   Engine           Engine      Layer    Client  │
│  │         │                 │          │          │   │
│  │         │                 │          │          │   │
│  ▼         ▼                 ▼          ▼          ▼   │
│ SQLite  Sandbox         Vector Store  Redis   Featherless│
│  DB     (Python/Bash)   (In-Memory)  (Optional)  API   │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8000/healthz
# Should return: {"ok": true}
```

### Create Test User & Key

```bash
# 1. Store Featherless API key
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "provider": "featherless",
    "api_key": "fl_YOUR_FEATHERLESS_KEY"
  }'

# 2. Generate Aurora key
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "name": "Test Key",
    "scopes": ["chat", "memory", "tools", "skills"]
  }'

# Copy the returned aurora_live_... key
```

### Test Memory Sharing

```bash
# Create first Aurora key
KEY1=$(curl -s -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "name": "Key 1",
    "scopes": ["chat"]
  }' | jq -r '.api_key')

# Create second Aurora key (same user)
KEY2=$(curl -s -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "name": "Key 2",
    "scopes": ["chat"]
  }' | jq -r '.api_key')

# Use KEY1 to store a preference
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer $KEY1" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "I prefer JSON responses",
    "memory_scope": "user"
  }'

# Use KEY2 to ask a question (should remember preference!)
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer $KEY2" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Show me user statistics",
    "memory_scope": "user"
  }'
# Should return JSON format because KEY1 set that preference!
```

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# Check logs
tail -f backend.log

# Verify .env file
cat backend/.env | grep HOST
# Should show: HOST=127.0.0.1
```

### Frontend Can't Connect

```bash
# Check backend is running
curl http://localhost:8000/healthz

# Check CORS is enabled
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:8000/v1/run

# Check frontend API_BASE
# Open frontend/main.js and verify:
# const API_BASE = "http://localhost:8000";
```

### Skills Not Loading

```bash
# Check skills endpoint
curl http://localhost:8000/v1/skills

# Should return array of 1,080+ skills
# If empty, check backend logs for initialization errors
```

### Memory Not Persisting

```bash
# Check database file exists
ls -la ai_orchestrator.db

# Check vector store
# In backend/.env, verify:
# VECTOR_BACKEND=memory

# Test memory storage
curl -X POST http://localhost:8000/v1/memory \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "text": "Test memory",
    "kind": "test",
    "memory_scope": "user"
  }'
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Production Deployment**: [PRODUCTION_READY.md](PRODUCTION_READY.md)
- **Competitive Advantages**: [COMPETITIVE_ADVANTAGES.md](COMPETITIVE_ADVANTAGES.md)

## 🎉 Summary

Your H&S Layer is now running **locally only** on your machine:

✅ Backend: http://localhost:8000 (127.0.0.1 only)  
✅ Frontend: http://localhost:3000  
✅ API keys stored encrypted  
✅ Memory shared across all Aurora keys for same user  
✅ 1,080+ skills loaded  
✅ 50+ tools available  
✅ Ready to enhance your Featherless API!

**Next Steps:**
1. Open http://localhost:3000
2. Bridge your Featherless key
3. Get your Aurora enhanced key
4. Start building with memory, skills, and tools!
