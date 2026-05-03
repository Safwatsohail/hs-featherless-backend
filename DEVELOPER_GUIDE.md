# 👨‍💻 Developer Guide

Complete guide to integrating H&S Layer into your applications.

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
3. [Code Examples](#code-examples)
4. [Memory System](#memory-system)
5. [Skills & Tools](#skills--tools)
6. [Best Practices](#best-practices)

---

## 🔐 Authentication

### Step 1: Store Provider API Key

```bash
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id",
    "provider": "openrouter",
    "api_key": "sk-or-v1-your-key"
  }'
```

**Supported Providers:**
- `openrouter` - Access to 200+ models
- `featherless` - Fast, affordable inference

### Step 2: Generate Aurora Enhanced Key

```bash
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id",
    "name": "My App Key",
    "scopes": ["chat", "memory", "tools", "skills"]
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "your-user-id",
  "name": "My App Key",
  "key_prefix": "aurora_live_xxxxx",
  "scopes": ["chat", "memory", "tools", "skills"],
  "is_active": true,
  "api_key": "aurora_live_xxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

---

## 🌐 API Endpoints

### POST /v1/run - Enhanced Chat

**Request:**
```json
{
  "user_id": "your-user-id",
  "input": "Write a Python function to calculate fibonacci",
  "provider": "openrouter",
  "model": "openrouter/auto",
  "memory_scope": "user"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "skill": "code_assistant",
  "output": "```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```",
  "tool_calls": [],
  "tool_results": [],
  "provider": "openrouter",
  "model": "openrouter/auto",
  "metrics": {
    "memory_hits": 2,
    "tool_count": 0,
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 80,
      "total_tokens": 230
    }
  }
}
```

### POST /v1/compare - A/B Compare

Compare raw vs enhanced responses:

```json
{
  "user_id": "your-user-id",
  "input": "What are the latest React 19 features?",
  "provider": "openrouter",
  "model": "openrouter/auto",
  "memory_scope": "user"
}
```

**Response:**
```json
{
  "baseline": {
    "output": "Raw LLM response...",
    "metrics": {
      "latency_ms": 2500,
      "usage": {...}
    }
  },
  "tuned": {
    "output": "Enhanced response with tools and memory...",
    "skill": "frontend_expert",
    "tool_calls": [{"name": "web_search", "input": {...}}],
    "metrics": {
      "latency_ms": 3200,
      "memory_hits": 3,
      "tool_count": 1,
      "usage": {...}
    }
  },
  "delta": {
    "latency_gap_ms": 700,
    "accuracy_gap": 0.85
  }
}
```

### POST /v1/memory - Store Memory

```json
{
  "user_id": "your-user-id",
  "text": "User prefers TypeScript over JavaScript",
  "kind": "preference",
  "memory_scope": "user"
}
```

### POST /v1/memory/context - Retrieve Memory

```json
{
  "user_id": "your-user-id",
  "query": "language preferences",
  "memory_scope": "user",
  "top_k": 10
}
```

**Response:**
```json
{
  "retrieved_memories": [
    {
      "text": "User prefers TypeScript over JavaScript",
      "score": 0.92,
      "metadata": {
        "type": "fact",
        "fact_type": "preference"
      }
    }
  ],
  "structured_memories": [...]
}
```

---

## 💻 Code Examples

### Python

```python
import requests

class HSLayer:
    def __init__(self, aurora_key, user_id, base_url="http://localhost:8000"):
        self.aurora_key = aurora_key
        self.user_id = user_id
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {aurora_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, message, provider="openrouter", model="openrouter/auto"):
        """Send enhanced chat request"""
        response = requests.post(
            f"{self.base_url}/v1/run",
            headers=self.headers,
            json={
                "user_id": self.user_id,
                "input": message,
                "provider": provider,
                "model": model,
                "memory_scope": "user"
            }
        )
        return response.json()
    
    def compare(self, message):
        """Compare raw vs enhanced"""
        response = requests.post(
            f"{self.base_url}/v1/compare",
            headers=self.headers,
            json={
                "user_id": self.user_id,
                "input": message,
                "provider": "openrouter",
                "model": "openrouter/auto",
                "memory_scope": "user"
            }
        )
        return response.json()
    
    def store_memory(self, text, kind="context"):
        """Store a memory fact"""
        response = requests.post(
            f"{self.base_url}/v1/memory",
            headers=self.headers,
            json={
                "user_id": self.user_id,
                "text": text,
                "kind": kind,
                "memory_scope": "user"
            }
        )
        return response.json()
    
    def get_memory(self, query):
        """Retrieve memory context"""
        response = requests.post(
            f"{self.base_url}/v1/memory/context",
            headers=self.headers,
            json={
                "user_id": self.user_id,
                "query": query,
                "memory_scope": "user",
                "top_k": 10
            }
        )
        return response.json()

# Usage
hs = HSLayer(
    aurora_key="aurora_live_YOUR_KEY",
    user_id="your-user-id"
)

# Chat
result = hs.chat("Write a Python function to add two numbers")
print(result["output"])
print(f"Skill: {result['skill']}")

# Store memory
hs.store_memory("User prefers TypeScript", kind="preference")

# Compare
comparison = hs.compare("What are the latest React 19 features?")
print("Raw:", comparison["baseline"]["output"][:100])
print("Enhanced:", comparison["tuned"]["output"][:100])
```

### JavaScript/TypeScript

```typescript
class HSLayer {
    constructor(
        private auroraKey: string,
        private userId: string,
        private baseUrl: string = "http://localhost:8000"
    ) {}

    async chat(message: string, provider = "openrouter", model = "openrouter/auto") {
        const response = await fetch(`${this.baseUrl}/v1/run`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${this.auroraKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: this.userId,
                input: message,
                provider,
                model,
                memory_scope: "user"
            })
        });
        return await response.json();
    }

    async compare(message: string) {
        const response = await fetch(`${this.baseUrl}/v1/compare`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${this.auroraKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: this.userId,
                input: message,
                provider: "openrouter",
                model: "openrouter/auto",
                memory_scope: "user"
            })
        });
        return await response.json();
    }

    async storeMemory(text: string, kind = "context") {
        const response = await fetch(`${this.baseUrl}/v1/memory`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${this.auroraKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: this.userId,
                text,
                kind,
                memory_scope: "user"
            })
        });
        return await response.json();
    }
}

// Usage
const hs = new HSLayer("aurora_live_YOUR_KEY", "your-user-id");

const result = await hs.chat("Write a TypeScript function to add numbers");
console.log(result.output);
console.log("Skill:", result.skill);
```

---

## 🧠 Memory System

### Memory Scopes

- **user** - Shared across all conversations for a user
- **workspace** - Shared within a workspace/project
- **conversation** - Isolated per conversation
- **global** - Shared across all users

### Automatic Fact Extraction

The system automatically extracts and stores:

- ✅ Names: "My name is John"
- ✅ Preferences: "I prefer TypeScript"
- ✅ Projects: "I'm building a SaaS product"
- ✅ Technologies: "I use React and Node.js"
- ✅ Goals: "I want to learn machine learning"
- ✅ Experience: "I have 5 years of experience"
- ✅ Location: "I'm from San Francisco"
- ✅ Company: "I work at Google"

### Memory Retrieval

- Retrieves top 10 most relevant memories
- Filters by score > 0.5
- Uses vector similarity search
- Fast (<50ms)

---

## 🎯 Skills & Tools

### Skills (1,080+)

Skills are automatically selected based on user intent:

- **Backend:** backend_debug, api_design, database_optimize
- **Frontend:** frontend_design, react_expert, css_master
- **ML:** ml_model_training, data_analysis, deep_learning
- **Security:** security_audit, penetration_testing, encryption
- **DevOps:** ci_cd_setup, kubernetes_deploy, monitoring

### Tools (55+)

Tools are automatically used when beneficial:

- **web_search** - Search the web for latest information
- **code_exec** - Execute Python/JavaScript code
- **math_exec** - Perform calculations
- **file_read** - Read file contents
- **image_analyze** - Analyze images
- **api_call** - Call external APIs
- **sql_exec** - Execute SQL queries
- **bash** - Run shell commands

---

## ✅ Best Practices

### 1. Use Descriptive User IDs

```python
# Good
user_id = "user_john_smith_12345"

# Bad
user_id = "123"
```

### 2. Set Appropriate Memory Scope

```python
# For personal preferences
memory_scope = "user"

# For project-specific context
memory_scope = "workspace"

# For isolated conversations
memory_scope = "conversation"
```

### 3. Handle Errors Gracefully

```python
try:
    result = hs.chat("Write a function")
    print(result["output"])
except requests.exceptions.RequestException as e:
    print(f"API Error: {e}")
except KeyError as e:
    print(f"Unexpected response format: {e}")
```

### 4. Use Specific Prompts

```python
# Good
"Write a Python function to calculate fibonacci numbers recursively"

# Bad
"Write code"
```

### 5. Store Important Context

```python
# Store user preferences
hs.store_memory("User prefers TypeScript", kind="preference")

# Store project context
hs.store_memory("Working on e-commerce platform", kind="project")

# Store technical details
hs.store_memory("Using React 18 and Next.js 14", kind="technology")
```

---

## 🚀 Next Steps

- **[Testing Guide](TESTING_GUIDE.md)** - Test your integration
- **[API Reference](http://localhost:8000/docs)** - Full API documentation
- **[Frontend Guide](FRONTEND_INTEGRATION_GUIDE.md)** - Integrate with frontend

---

**Happy coding with H&S Layer! 🎉**
