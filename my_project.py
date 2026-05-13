#!/usr/bin/env python3
"""
H&S Layer - External Project Example
Use your Aurora key from the dashboard to call the API
"""
import requests

# Get these from the H&S Layer dashboard
API_BASE = "http://localhost:8000"
AURORA_KEY = "aurora_live_YOUR_KEY_HERE"  # Generate in dashboard
USER_ID = "YOUR_DEVICE_USER_ID"  # From browser console

headers = {"Authorization": f"Bearer {AURORA_KEY}", "Content-Type": "application/json"}

# 1. Chat with memory and tools
print("🚀 Sending message...")
r = requests.post(f"{API_BASE}/v1/run", headers=headers, json={
    "user_id": USER_ID,
    "input": "My name is Safi. What programming language should I learn?",
    "memory_scope": "user",
    "provider": "openrouter",
    "model": "openrouter/auto"
})
data = r.json()
print(f"✓ Response: {data['output'][:150]}...")
print(f"✓ Skill: {data['skill']}")
print(f"✓ Memory hits: {data['metrics']['memory_hits']}")

# 2. Get stored facts
print("\n📚 Retrieving memory...")
r = requests.post(f"{API_BASE}/v1/memory/context", headers=headers, json={
    "user_id": USER_ID,
    "query": "name preferences",
    "memory_scope": "user"
})
facts = r.json()["structured_memories"]
print(f"✓ Found {len(facts)} facts")
for fact in facts:
    if fact["kind"].startswith("fact_"):
        print(f"  - {fact['kind']}: {fact['data'].get('value')}")

print("\n✅ Done!")
