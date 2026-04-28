# 🚀 Complete Working Examples - Enhanced AI API

## ✅ System Status

**Backend:** http://localhost:8000  
**Frontend:** http://localhost:3000  
**Aurora Key:** `aurora_live_6BYZvwXhx0qmmifrwTYtUnRpLydoeSGy`  
**User ID:** `00000000-0000-0000-0000-000000000001`  
**OpenRouter Key:** `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`

---

## 📚 Table of Contents

1. [Python Examples](#python-examples)
2. [JavaScript/Node.js Examples](#javascript-examples)
3. [TypeScript Examples](#typescript-examples)
4. [cURL Examples](#curl-examples)
5. [Go Examples](#go-examples)
6. [Rust Examples](#rust-examples)
7. [Complete Projects](#complete-projects)

---

## Python Examples

### 1. Simple Chat Client

```python
#!/usr/bin/env python3
"""
Simple chat client for Enhanced AI API
Usage: python chat_client.py
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_6BYZvwXhx0qmmifrwTYtUnRpLydoeSGy"
USER_ID = "00000000-0000-0000-0000-000000000001"

class EnhancedAIClient:
    def __init__(self, api_key: str, user_id: str, base_url: str = API_BASE):
        self.api_key = api_key
        self.user_id = user_id
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, message: str, memory_scope: str = "user") -> Dict[str, Any]:
        """Send a chat message and get enhanced response"""
        response = requests.post(
            f"{self.base_url}/v1/run",
            headers=self.headers,
            json={
                "user_id": self.user_id,
                "input": message,
                "memory_scope": memory_scope,
                "provider": "openrouter",
                "model": "openrouter/auto"
            }
        )
        response.raise_for_status()
        return response.json()
    
    def compare(self, message: str) -> Dict[str, Any]:
        """Compare raw vs enhanced responses"""
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
        response.raise_for_status()
        return response.json()
    
    def store_memory(self, text: str, kind: str = "context") -> Dict[str, Any]:
        """Store a memory/fact"""
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
        response.raise_for_status()
        return response.json()
    
    def get_memory(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve memories"""
        response = requests.post(
            f"{self.base_url}/v1/memory/context",
            headers=self.headers,
            json={
                "user_id": self.user_id,
                "query": query,
                "memory_scope": "user",
                "top_k": top_k
            }
        )
        response.raise_for_status()
        return response.json()
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool"""
        response = requests.post(
            f"{self.base_url}/v1/tools/{tool_name}",
            headers=self.headers,
            json={
                "name": tool_name,
                "input": tool_input
            }
        )
        response.raise_for_status()
        return response.json()

def main():
    client = EnhancedAIClient(AURORA_KEY, USER_ID)
    
    print("🤖 Enhanced AI Chat Client")
    print("=" * 50)
    
    # Example 1: Simple chat
    print("\n1. Simple Chat:")
    result = client.chat("What is 2+2?")
    print(f"   Skill: {result['skill']}")
    print(f"   Output: {result['output'][:100]}...")
    print(f"   Tools used: {len(result['tool_calls'])}")
    
    # Example 2: Store memory
    print("\n2. Store Memory:")
    memory = client.store_memory("User prefers Python and TypeScript", "preference")
    print(f"   Stored: {memory['stored']}")
    
    # Example 3: Retrieve memory
    print("\n3. Retrieve Memory:")
    memories = client.get_memory("preferences")
    print(f"   Found {len(memories['retrieved_memories'])} memories")
    for m in memories['retrieved_memories'][:2]:
        print(f"   - {m['text']} (score: {m['score']:.2f})")
    
    # Example 4: Execute tool
    print("\n4. Execute Tool (calculator):")
    tool_result = client.execute_tool("calculator", {"expression": "42 * 7"})
    print(f"   Result: {tool_result['output']}")
    
    # Example 5: Compare
    print("\n5. Compare Raw vs Enhanced:")
    comparison = client.compare("Calculate 15 * 8")
    print(f"   Baseline: {comparison['baseline']['output'][:60]}...")
    print(f"   Tuned: {comparison['tuned']['output'][:60]}...")
    print(f"   Skill: {comparison['tuned']['skill']}")
    print(f"   Latency gap: {comparison['delta']['latency_gap_ms']}ms")

if __name__ == "__main__":
    main()
```

**Save as:** `chat_client.py`  
**Run:** `python3 chat_client.py`

---

### 2. Interactive Chat Bot

```python
#!/usr/bin/env python3
"""
Interactive chat bot with conversation history
Usage: python interactive_bot.py
"""

import requests
import sys
from datetime import datetime

API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_6BYZvwXhx0qmmifrwTYtUnRpLydoeSGy"
USER_ID = "00000000-0000-0000-0000-000000000001"

def chat(message: str) -> dict:
    response = requests.post(
        f"{API_BASE}/v1/run",
        headers={
            "Authorization": f"Bearer {AURORA_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "user_id": USER_ID,
            "input": message,
            "memory_scope": "user",
            "provider": "openrouter",
            "model": "openrouter/auto"
        }
    )
    return response.json()

def main():
    print("🤖 Enhanced AI Interactive Bot")
    print("=" * 60)
    print("Type 'exit' to quit, 'help' for commands")
    print("=" * 60)
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("\n You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("\nCommands:")
                print("  exit - Quit the bot")
                print("  help - Show this help")
                print("  history - Show conversation history")
                continue
            
            if user_input.lower() == 'history':
                print("\nConversation History:")
                for i, (q, a) in enumerate(conversation_history, 1):
                    print(f"\n{i}. You: {q}")
                    print(f"   Bot: {a[:100]}...")
                continue
            
            # Send message
            print("\n🤔 Thinking...", end="", flush=True)
            result = chat(user_input)
            print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."
            
            # Display response
            print(f"\n🤖 Bot: {result['output']}")
            
            # Show metadata
            if result['tool_calls']:
                print(f"\n   📊 Tools used: {', '.join([t['name'] for t in result['tool_calls']])}")
            if result['metrics']['memory_hits'] > 0:
                print(f"   🧠 Memory hits: {result['metrics']['memory_hits']}")
            print(f"   🎯 Skill: {result['skill']}")
            
            # Save to history
            conversation_history.append((user_input, result['output']))
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
```

**Save as:** `interactive_bot.py`  
**Run:** `python3 interactive_bot.py`

---

