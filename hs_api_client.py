#!/usr/bin/env python3
"""
H&S Layer API Client - Standalone Python Script
Usage: python3 hs_api_client.py
"""

import requests
import json

# Configuration
API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_YOUR_KEY_HERE"  # Replace with your Aurora key
USER_ID = "YOUR_DEVICE_USER_ID"  # Replace with your device user ID
OPENROUTER_KEY = "YOUR_OPENROUTER_API_KEY"  # Get from https://openrouter.ai

headers = {
    "Authorization": f"Bearer {AURORA_KEY}",
    "Content-Type": "application/json"
}

def setup_api_key():
    """Store your OpenRouter API key"""
    res = requests.post(f"{API_BASE}/apikey", headers=headers, json={
        "user_id": USER_ID,
        "provider": "openrouter",
        "api_key": OPENROUTER_KEY
    })
    print("✓ API key stored" if res.ok else f"✗ Error: {res.text}")

def chat(message):
    """Send a message and get a response with memory and tools"""
    res = requests.post(f"{API_BASE}/v1/run", headers=headers, json={
        "user_id": USER_ID,
        "input": message,
        "memory_scope": "user",
        "provider": "openrouter",
        "model": "openrouter/auto"
    })
    data = res.json()
    return {
        "response": data.get("output"),
        "skill": data.get("skill"),
        "tools": [t["name"] for t in data.get("tool_calls", [])],
        "memory_hits": data.get("metrics", {}).get("memory_hits", 0)
    }

def store_memory(text, kind="preference"):
    """Store a fact in memory"""
    res = requests.post(f"{API_BASE}/v1/memory", headers=headers, json={
        "user_id": USER_ID,
        "text": text,
        "kind": kind,
        "memory_scope": "user"
    })
    return res.json() if res.ok else None

def get_memory(query):
    """Retrieve memory context"""
    res = requests.post(f"{API_BASE}/v1/memory/context", headers=headers, json={
        "user_id": USER_ID,
        "query": query,
        "memory_scope": "user",
        "top_k": 10
    })
    return res.json() if res.ok else None

if __name__ == "__main__":
    print("🚀 H&S Layer API Client")
    print("=" * 50)
    
    # Store a memory fact
    print("\n1. Storing memory...")
    store_memory("I prefer Python over JavaScript")
    
    # Chat with memory
    print("\n2. Chatting with memory...")
    result = chat("What programming language should I use?")
    print(f"Response: {result['response'][:100]}...")
    print(f"Skill: {result['skill']}")
    print(f"Memory hits: {result['memory_hits']}")
    
    # Get memory
    print("\n3. Retrieving memory...")
    memory = get_memory("programming preferences")
    print(f"Found {len(memory['structured_memories'])} facts")
    
    print("\n✅ Done!")

