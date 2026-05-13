# H&S Layer - Example Project

This is a complete working example of how to use the H&S Layer API with your own project.

## Setup

### 1. Store Your API Key

First, store your OpenRouter API key with the system:

```bash
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-device-user-id",
    "provider": "openrouter",
    "api_key": "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"
  }'
```

### 2. Generate Your Aurora Enhanced Key

```bash
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-device-user-id",
    "name": "My Project Key",
    "scopes": ["chat", "memory", "tools", "skills"]
  }'
```

This returns your Aurora key like: `aurora_live_XXXXXXXXXXXXXXXX`

## Usage Examples

### Python Example

```python
import requests
import json

API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_YOUR_KEY_HERE"
USER_ID = "your-device-user-id"

headers = {
    "Authorization": f"Bearer {AURORA_KEY}",
    "Content-Type": "application/json"
}

# 1. Store a memory fact
def store_memory(text, kind="preference"):
    response = requests.post(
        f"{API_BASE}/v1/memory",
        headers=headers,
        json={
            "user_id": USER_ID,
            "text": text,
            "kind": kind,
            "memory_scope": "user"
        }
    )
    return response.json()

# 2. Retrieve memory context
def get_memory(query):
    response = requests.post(
        f"{API_BASE}/v1/memory/context",
        headers=headers,
        json={
            "user_id": USER_ID,
            "query": query,
            "memory_scope": "user",
            "top_k": 10
        }
    )
    return response.json()

# 3. Run enhanced chat with memory and tools
def chat(message):
    response = requests.post(
        f"{API_BASE}/v1/run",
        headers=headers,
        json={
            "user_id": USER_ID,
            "input": message,
            "memory_scope": "user",
            "provider": "openrouter",
            "model": "openrouter/auto"
        }
    )
    data = response.json()
    return {
        "response": data.get("output"),
        "skill": data.get("skill"),
        "tools_used": [t["name"] for t in data.get("tool_calls", [])],
        "memory_hits": data.get("metrics", {}).get("memory_hits", 0)
    }

# 4. Compare raw vs enhanced
def compare(message):
    response = requests.post(
        f"{API_BASE}/v1/compare",
        headers=headers,
        json={
            "user_id": USER_ID,
            "input": message,
            "provider": "openrouter",
            "model": "openrouter/auto",
            "memory_scope": "user"
        }
    )
    data = response.json()
    return {
        "raw": data["baseline"]["output"],
        "enhanced": data["tuned"]["output"],
        "skill_used": data["tuned"]["skill"],
        "latency_improvement": data["delta"]["latency_gap_ms"]
    }

# Example usage
if __name__ == "__main__":
    # Store some facts
    print("Storing facts...")
    store_memory("I prefer Python over JavaScript")
    store_memory("I'm interested in machine learning")
    
    # Retrieve memory
    print("\nRetrieving memory...")
    memory = get_memory("programming preferences")
    print(f"Found {len(memory['structured_memories'])} facts")
    
    # Chat with memory
    print("\nChatting with memory...")
    result = chat("What programming language should I use for my project?")
    print(f"Response: {result['response']}")
    print(f"Skill: {result['skill']}")
    print(f"Tools: {result['tools_used']}")
    print(f"Memory hits: {result['memory_hits']}")
    
    # Compare
    print("\nComparing raw vs enhanced...")
    comparison = compare("Explain machine learning")
    print(f"Raw: {comparison['raw'][:100]}...")
    print(f"Enhanced: {comparison['enhanced'][:100]}...")
    print(f"Skill: {comparison['skill_used']}")
```

### JavaScript Example

```javascript
const API_BASE = "http://localhost:8000";
const AURORA_KEY = "aurora_live_YOUR_KEY_HERE";
const USER_ID = "your-device-user-id";

const headers = {
  "Authorization": `Bearer ${AURORA_KEY}`,
  "Content-Type": "application/json"
};

// 1. Store memory
async function storeMemory(text, kind = "preference") {
  const res = await fetch(`${API_BASE}/v1/memory`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      user_id: USER_ID,
      text,
      kind,
      memory_scope: "user"
    })
  });
  return res.json();
}

// 2. Get memory context
async function getMemory(query) {
  const res = await fetch(`${API_BASE}/v1/memory/context`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      user_id: USER_ID,
      query,
      memory_scope: "user",
      top_k: 10
    })
  });
  return res.json();
}

// 3. Chat with memory
async function chat(message) {
  const res = await fetch(`${API_BASE}/v1/run`, {
    method: "POST",
    headers,
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
    tools: data.tool_calls.map(t => t.name),
    memoryHits: data.metrics.memory_hits
  };
}

// 4. Compare raw vs enhanced
async function compare(message) {
  const res = await fetch(`${API_BASE}/v1/compare`, {
    method: "POST",
    headers,
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

// Example usage
(async () => {
  // Store facts
  console.log("Storing facts...");
  await storeMemory("I prefer Python over JavaScript");
  await storeMemory("I'm interested in machine learning");
  
  // Get memory
  console.log("\nRetrieving memory...");
  const memory = await getMemory("programming preferences");
  console.log(`Found ${memory.structured_memories.length} facts`);
  
  // Chat
  console.log("\nChatting...");
  const result = await chat("What programming language should I use?");
  console.log(`Response: ${result.response}`);
  console.log(`Skill: ${result.skill}`);
  console.log(`Tools: ${result.tools.join(", ")}`);
  
  // Compare
  console.log("\nComparing...");
  const comp = await compare("Explain machine learning");
  console.log(`Raw: ${comp.raw.slice(0, 100)}...`);
  console.log(`Enhanced: ${comp.enhanced.slice(0, 100)}...`);
})();
```

### cURL Examples

```bash
# Store memory
curl -X POST http://localhost:8000/v1/memory \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-device-user-id",
    "text": "I prefer Python over JavaScript",
    "kind": "preference",
    "memory_scope": "user"
  }'

# Get memory
curl -X POST http://localhost:8000/v1/memory/context \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-device-user-id",
    "query": "programming preferences",
    "memory_scope": "user",
    "top_k": 10
  }'

# Chat with memory
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-device-user-id",
    "input": "What programming language should I use?",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openrouter/auto"
  }'

# Compare raw vs enhanced
curl -X POST http://localhost:8000/v1/compare \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-device-user-id",
    "input": "Explain machine learning",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'
```

## Features

### Memory System
- ✅ Store facts about users (preferences, interests, etc.)
- ✅ Retrieve memory context for any query
- ✅ Memory is shared across all Aurora keys for the same user
- ✅ Automatic fact extraction from conversations

### Skills & Tools
- ✅ 1,080+ pre-built skills
- ✅ 55+ tools (web search, code execution, etc.)
- ✅ Auto-routing to best skill based on input
- ✅ Manual skill invocation available

### Comparison
- ✅ Compare raw vs enhanced responses
- ✅ See latency improvements
- ✅ Track tool usage and memory hits

## Device User ID

Your device user ID is automatically generated based on:
- Browser user agent
- Language settings
- Timezone
- Screen resolution
- CPU cores

This ensures:
- Same device = same user ID
- Different device = different user ID
- No authentication needed
- Persistent across sessions

## API Key Management

Your OpenRouter API key is:
- Encrypted and stored securely
- Never exposed in responses
- Shared across all Aurora keys for the same user
- Can be updated anytime

## Next Steps

1. Replace `aurora_live_YOUR_KEY_HERE` with your actual Aurora key
2. Replace `your-device-user-id` with your device user ID (shown in browser console)
3. Run the examples above
4. Check the Dev Docs tab in the dashboard for more examples

Happy coding! 🚀
