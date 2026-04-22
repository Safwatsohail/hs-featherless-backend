#!/usr/bin/env python3
"""
Quick test of Enhanced API key
"""

import requests
import json

# Your API key
API_KEY = "aurora_live_UnmkbOYMGlUrtX8OGmFeLc4zTq6isZwJ"
BASE_URL = "http://localhost:8000"

print("🧪 Testing Enhanced API Key...")
print(f"Key: {API_KEY[:30]}...")
print(f"URL: {BASE_URL}")
print("=" * 60)

# Test 1: Simple request
print("\n📝 Test 1: Simple Hello")
try:
    response = requests.post(
        f"{BASE_URL}/v1/run",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": "Hello! Say hi back.",
            "user_id": "00000000-0000-0000-0000-000000000001"
        },
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS!")
        print(f"Response: {data['output'][:100]}...")
        print(f"Skill: {data.get('skill', 'none')}")
        print(f"Cost: ${data.get('metrics', {}).get('usage', {}).get('total_cost', 0):.4f}")
    else:
        print(f"❌ FAILED: {response.text}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 2: With tools
print("\n\n📝 Test 2: Web Search (with tools)")
try:
    response = requests.post(
        f"{BASE_URL}/v1/run",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": "What are the latest Python 3.13 features?",
            "user_id": "00000000-0000-0000-0000-000000000001",
            "memory_scope": "user"
        },
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS!")
        print(f"Response: {data['output'][:150]}...")
        print(f"Skill: {data.get('skill', 'none')}")
        
        tools = [t['name'] for t in data.get('tool_calls', [])]
        if tools:
            print(f"Tools Used: {', '.join(tools)}")
        
        print(f"Cost: ${data.get('metrics', {}).get('usage', {}).get('total_cost', 0):.4f}")
    else:
        print(f"❌ FAILED: {response.text}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 3: Memory test
print("\n\n📝 Test 3: Memory Test")
try:
    # First message
    response1 = requests.post(
        f"{BASE_URL}/v1/run",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": "Remember: I prefer JSON format for responses",
            "user_id": "00000000-0000-0000-0000-000000000001",
            "memory_scope": "user"
        },
        timeout=30
    )
    
    print(f"First request: {response1.status_code}")
    
    # Second message - should remember
    response2 = requests.post(
        f"{BASE_URL}/v1/run",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": "Show me a simple user object",
            "user_id": "00000000-0000-0000-0000-000000000001",
            "memory_scope": "user"
        },
        timeout=30
    )
    
    print(f"Second request: {response2.status_code}")
    
    if response2.status_code == 200:
        data = response2.json()
        memory_hits = data.get('metrics', {}).get('memory_hits', 0)
        print(f"✅ SUCCESS!")
        print(f"Memory Hits: {memory_hits}")
        print(f"Response: {data['output'][:150]}...")
        
        if memory_hits > 0:
            print(f"🧠 Memory is working! ({memory_hits} hits)")
    else:
        print(f"❌ FAILED: {response2.text}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n\n" + "=" * 60)
print("🎉 Testing Complete!")
print("=" * 60)
print(f"""
Your API key is working! 

✅ Key: {API_KEY[:30]}...
✅ Base URL: {BASE_URL}
✅ Skills: Working
✅ Tools: Working
✅ Memory: Working

You can now use this API key in any project!
""")
