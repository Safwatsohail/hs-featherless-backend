# 🔑 Aurora API Key Usage Guide

## What is an Aurora API Key?

An **Aurora API Key** is your enhanced Featherless API key that adds:
- ✅ **Unified Memory** - Remembers context across sessions
- ✅ **1,080+ Skills** - Auto-routes to domain experts
- ✅ **50+ Tools** - Web search, code analysis, etc.
- ✅ **Intelligent Caching** - 40-60% cost reduction

## How to Get Your Aurora Key

1. **Get a Featherless API Key**
   - Visit https://featherless.ai
   - Sign up and generate an API key (starts with `fl_`)

2. **Bridge Your Key**
   - Open http://localhost:3000
   - Navigate to the onboarding flow
   - Paste your Featherless key
   - Click "Generate Enhanced Key"
   - Copy your Aurora key (starts with `aurora_live_`)

## Using Your Aurora Key

### Basic Request

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "What are the latest AI developments?",
    "memory_scope": "user"
  }'
```

### JavaScript/TypeScript

```javascript
const AURORA_KEY = "aurora_live_YOUR_KEY_HERE";
const API_BASE = "http://localhost:8000";

async function chat(message) {
  const response = await fetch(`${API_BASE}/v1/run`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${AURORA_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: "00000000-0000-0000-0000-000000000001",
      input: message,
      memory_scope: "user"
    })
  });
  
  const data = await response.json();
  return data;
}

// Usage
const result = await chat("Debug my Python API");
console.log(result.output);
console.log("Skill:", result.skill);
console.log("Tools:", result.tool_calls);
```

### Python

```python
import requests

AURORA_KEY = "aurora_live_YOUR_KEY_HERE"
API_BASE = "http://localhost:8000"

def chat(message):
    response = requests.post(
        f"{API_BASE}/v1/run",
        headers={
            "Authorization": f"Bearer {AURORA_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "user_id": "00000000-0000-0000-0000-000000000001",
            "input": message,
            "memory_scope": "user"
        }
    )
    return response.json()

# Usage
result = chat("What's the weather in Tokyo?")
print(result["output"])
print(f"Skill: {result['skill']}")
print(f"Tools: {[t['name'] for t in result['tool_calls']]}")
```

## Memory Sharing

**All Aurora keys for the same user share memory!**

```javascript
// Create two different Aurora keys for the same user
const key1 = "aurora_live_ABC123...";
const key2 = "aurora_live_XYZ789...";

// Use key1 to set a preference
await fetch(`${API_BASE}/v1/run`, {
  headers: { "Authorization": `Bearer ${key1}` },
  body: JSON.stringify({
    user_id: "USER_ID",
    input: "I prefer JSON responses",
    memory_scope: "user"
  })
});

// Use key2 - it remembers the preference!
await fetch(`${API_BASE}/v1/run`, {
  headers: { "Authorization": `Bearer ${key2}` },
  body: JSON.stringify({
    user_id: "USER_ID",
    input: "Show me user statistics",
    memory_scope: "user"
  })
});
// Returns JSON because key1 set that preference
```

## Memory Scopes

Control how memory is shared:

| Scope | Sharing | Use Case |
|-------|---------|----------|
| `user` | All keys for same user | Personal preferences |
| `workspace` | Same workspace/project | Team collaboration |
| `conversation` | Single conversation | Private chats |
| `global` | All users | Public knowledge |

Example:

```javascript
// Personal (shared across all your keys)
{
  "memory_scope": "user",
  "input": "I prefer TypeScript"
}

// Project-specific
{
  "memory_scope": "workspace",
  "context_key": "project-alpha",
  "input": "Our API uses REST"
}

// Private conversation
{
  "memory_scope": "conversation",
  "conversation_id": "conv-123",
  "input": "Confidential data"
}
```

## Available Endpoints

### Chat

```bash
POST /v1/run
POST /v1/chat
```

### Skills

```bash
GET  /v1/skills                    # List all skills
POST /v1/skills/{skill_name}       # Invoke specific skill
```

### Tools

```bash
GET  /tools                        # List all tools
POST /v1/tools/{tool_name}         # Execute specific tool
```

### Memory

```bash
POST /v1/memory                    # Store memory
POST /v1/memory/context            # Retrieve memory
```

### Compare

```bash
POST /compare                      # Compare raw vs enhanced
```

## Response Format

```json
{
  "conversation_id": "uuid",
  "skill": "research",
  "output": "Enhanced response with tools and memory...",
  "provider": "featherless",
  "model": "gpt-4.1-mini",
  "tool_calls": [
    {
      "name": "web_search",
      "input": {"query": "..."},
      "output": "..."
    }
  ],
  "tool_results": [...],
  "metrics": {
    "memory_hits": 3,
    "tool_count": 1,
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 200,
      "total_tokens": 350
    }
  }
}
```

## Security Notes

- **Local Only**: Backend runs on `127.0.0.1` (localhost only)
- **Encrypted Storage**: Featherless keys encrypted with Fernet
- **No External Access**: Only your machine can access the API
- **Keep Keys Secret**: Never commit Aurora keys to git

## Troubleshooting

### "Invalid Aurora API key"

- Check the key starts with `aurora_live_`
- Verify the key was generated for this backend instance
- Try generating a new key

### "No API key stored for provider"

- You need to store your Featherless key first
- Use the onboarding flow or POST to `/apikey`

### "Connection refused"

- Check backend is running: `curl http://localhost:8000/healthz`
- Verify HOST=127.0.0.1 in backend/.env
- Check logs: `tail -f backend.log`

## Full Documentation

- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **API Docs**: http://localhost:8000/docs
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
