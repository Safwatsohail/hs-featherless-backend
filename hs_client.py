#!/usr/bin/env python3
"""H&S Layer API Client - Standalone (< 50 lines)"""
import requests, uuid

API = "http://localhost:8000"
KEY = "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"
USER = str(uuid.uuid4())

# 1. Store API key
requests.post(f"{API}/apikey", json={"user_id": USER, "provider": "openrouter", "api_key": KEY})

# 2. Generate Aurora key
r = requests.post(f"{API}/auth/issue-key", json={"user_id": USER, "name": "Client", "scopes": ["chat", "memory", "tools", "skills"]})
AURORA = r.json()["api_key"]

# 3. Send message with facts
r = requests.post(f"{API}/v1/run", headers={"Authorization": f"Bearer {AURORA}"}, json={"user_id": USER, "input": "My name is Safi and I prefer Python", "memory_scope": "user", "provider": "openrouter", "model": "openrouter/auto"})
print("✓ Chat response:", r.json()["output"][:80])

# 4. Retrieve memory
r = requests.post(f"{API}/v1/memory/context", headers={"Authorization": f"Bearer {AURORA}"}, json={"user_id": USER, "query": "name prefer", "memory_scope": "user"})
facts = r.json()["structured_memories"]
print(f"✓ Memory facts: {len(facts)}")
for fact in facts:
    if fact["kind"].startswith("fact_"):
        print(f"  - {fact['kind']}: {fact['data'].get('value', 'N/A')}")
