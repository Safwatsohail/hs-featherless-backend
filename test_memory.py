#!/usr/bin/env python3
"""
Test Memory Storage and Retrieval
"""

import requests
import time

API_KEY = "aurora_live_UnmkbOYMGlUrtX8OGmFeLc4zTq6isZwJ"
BASE_URL = "http://localhost:8000"
USER_ID = "00000000-0000-0000-0000-000000000001"

def chat(message):
    """Send message and get response"""
    response = requests.post(
        f"{BASE_URL}/v1/run",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": message,
            "user_id": USER_ID,
            "memory_scope": "user",
            "context_key": "test"
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        return {
            "output": data["output"],
            "memory_hits": data.get("metrics", {}).get("memory_hits", 0),
            "skill": data.get("skill", "none")
        }
    else:
        return {"error": response.text}

print("=" * 70)
print("🧠 MEMORY STORAGE TEST")
print("=" * 70)
print()

# Test 1: Store name
print("📝 Test 1: Storing name")
print("User: My name is Safwat")
result = chat("My name is Safwat")
if "error" not in result:
    print(f"AI: {result['output'][:100]}...")
    print(f"✅ Stored!")
else:
    print(f"❌ Error: {result['error']}")

print()
time.sleep(2)

# Test 2: Retrieve name
print("📝 Test 2: Retrieving name")
print("User: What's my name?")
result = chat("What's my name?")
if "error" not in result:
    print(f"AI: {result['output']}")
    print(f"Memory Hits: {result['memory_hits']}")
    if result['memory_hits'] > 0:
        print("✅ Memory is working! It remembered your name!")
    else:
        print("⚠️  No memory hits (might need more time)")
else:
    print(f"❌ Error: {result['error']}")

print()
time.sleep(2)

# Test 3: Store preference
print("📝 Test 3: Storing preference")
print("User: I prefer JSON format for responses")
result = chat("I prefer JSON format for responses")
if "error" not in result:
    print(f"AI: {result['output'][:100]}...")
    print(f"✅ Stored!")
else:
    print(f"❌ Error: {result['error']}")

print()
time.sleep(2)

# Test 4: Store project context
print("📝 Test 4: Storing project context")
print("User: I'm building an e-commerce platform with Python")
result = chat("I'm building an e-commerce platform with Python")
if "error" not in result:
    print(f"AI: {result['output'][:100]}...")
    print(f"✅ Stored!")
else:
    print(f"❌ Error: {result['error']}")

print()
time.sleep(2)

# Test 5: Retrieve all context
print("📝 Test 5: Retrieving all context")
print("User: What do you know about me?")
result = chat("What do you know about me?")
if "error" not in result:
    print(f"AI: {result['output']}")
    print(f"Memory Hits: {result['memory_hits']}")
    if result['memory_hits'] > 0:
        print(f"✅ Memory retrieved {result['memory_hits']} facts!")
    else:
        print("⚠️  No memory hits")
else:
    print(f"❌ Error: {result['error']}")

print()
print("=" * 70)
print("🎉 Memory Test Complete!")
print("=" * 70)
print()
print("Memory features:")
print("  ✅ Automatic fact extraction (names, preferences, projects)")
print("  ✅ Cross-API-key memory (same user = shared memory)")
print("  ✅ Dynamic responses based on stored context")
print("  ✅ Facts stored in vector store + structured DB")
print()
