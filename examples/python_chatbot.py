#!/usr/bin/env python3
"""
Enhanced AI API - Python Chatbot Example
A simple command-line chatbot using the Enhanced AI API
"""

import requests
import json
from typing import Optional

# Configuration
API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_ZNTshOqnNk8LvKYKuuW5hZpW-3WHI1Ko"
USER_ID = "00000000-0000-0000-0000-000000000001"


class EnhancedAIClient:
    """Client for the Enhanced AI API"""
    
    def __init__(self, api_base: str, aurora_key: str, user_id: str):
        self.api_base = api_base
        self.aurora_key = aurora_key
        self.user_id = user_id
        self.headers = {
            "Authorization": f"Bearer {aurora_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, message: str, conversation_id: Optional[str] = None) -> dict:
        """Send a chat message and get a response"""
        payload = {
            "user_id": self.user_id,
            "input": message,
            "memory_scope": "user",
            "provider": "openrouter",
            "model": "openrouter/auto"
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        response = requests.post(
            f"{self.api_base}/v1/run",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def compare(self, message: str) -> dict:
        """Compare raw vs enhanced responses"""
        payload = {
            "user_id": self.user_id,
            "input": message,
            "provider": "openrouter",
            "model": "openrouter/auto",
            "memory_scope": "user"
        }
        
        response = requests.post(
            f"{self.api_base}/v1/compare",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Execute a specific tool"""
        payload = {
            "name": tool_name,
            "input": tool_input
        }
        
        response = requests.post(
            f"{self.api_base}/v1/tools/{tool_name}",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def store_memory(self, text: str, kind: str = "context") -> dict:
        """Store a memory"""
        payload = {
            "user_id": self.user_id,
            "text": text,
            "kind": kind,
            "memory_scope": "user"
        }
        
        response = requests.post(
            f"{self.api_base}/v1/memory",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()


def main():
    """Main chatbot loop"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║          Enhanced AI API - Python Chatbot                    ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("Type 'quit' to exit, 'compare <message>' to compare responses")
    print("Type 'tool <name> <input>' to execute a tool")
    print("Type 'remember <text>' to store a memory")
    print()
    
    client = EnhancedAIClient(API_BASE, AURORA_KEY, USER_ID)
    conversation_id = None
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            # Handle special commands
            if user_input.startswith('compare '):
                message = user_input[8:]
                print("\n🔄 Comparing raw vs enhanced...\n")
                result = client.compare(message)
                print(f"📊 Baseline (raw):")
                print(f"   {result['baseline']['output'][:200]}...")
                print(f"   Latency: {result['baseline']['metrics']['latency_ms']}ms")
                print()
                print(f"✨ Enhanced (tuned):")
                print(f"   {result['tuned']['output'][:200]}...")
                print(f"   Skill: {result['tuned']['skill']}")
                print(f"   Tools: {result['tuned']['metrics']['tool_count']}")
                print(f"   Memory hits: {result['tuned']['metrics']['memory_hits']}")
                print(f"   Latency: {result['tuned']['metrics']['latency_ms']}ms")
                print()
                continue
            
            if user_input.startswith('tool '):
                parts = user_input[5:].split(' ', 1)
                if len(parts) == 2:
                    tool_name, tool_input_str = parts
                    try:
                        tool_input = json.loads(tool_input_str)
                        result = client.execute_tool(tool_name, tool_input)
                        print(f"\n🛠️ Tool result: {result['output']}\n")
                    except json.JSONDecodeError:
                        print("❌ Invalid JSON input")
                else:
                    print("❌ Usage: tool <name> <json_input>")
                continue
            
            if user_input.startswith('remember '):
                text = user_input[9:]
                client.store_memory(text)
                print("✅ Memory stored\n")
                continue
            
            # Regular chat
            result = client.chat(user_input, conversation_id)
            conversation_id = result['conversation_id']
            
            print(f"\nAI ({result['skill']}): {result['output']}")
            
            # Show tool usage if any
            if result['tool_calls']:
                print(f"\n🛠️ Tools used: {', '.join([t['name'] for t in result['tool_calls']])}")
            
            # Show memory hits
            if result['metrics']['memory_hits'] > 0:
                print(f"🧠 Memory hits: {result['metrics']['memory_hits']}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
