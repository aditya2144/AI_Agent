"""Test voice and chat functionality."""

import requests
import json

# Test 1: Chat endpoint
print("=" * 60)
print("TEST 1: Chat Endpoint")
print("=" * 60)

test_message = "Hello, what laptops do you have for video editing?"
payload = {
    "customer_id": 1,
    "customer_name": "Test Customer",
    "message": test_message,
    "conversation_history": []
}

try:
    response = requests.post(
        "http://localhost:8000/api/chat",
        json=payload,
        timeout=30
    )
    print(f"✓ Status: {response.status_code}")
    result = response.json()
    print(f"✓ Response: {result['response'][:100]}...")
except requests.exceptions.Timeout:
    print(f"✗ Timeout: Request took too long (>30s)")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Text-to-Speech endpoint
print("\n" + "=" * 60)
print("TEST 2: Text-to-Speech Endpoint")
print("=" * 60)

tts_payload = {
    "text": "Hello, I recommend the Dell XPS 15 for video editing."
}

try:
    response = requests.post(
        "http://localhost:8000/api/text-to-speech",
        json=tts_payload,
        timeout=10
    )
    print(f"✓ Status: {response.status_code}")
    print(f"✓ Audio size: {len(response.content)} bytes")
    
    # Save to file
    with open("test_response.mp3", "wb") as f:
        f.write(response.content)
    print(f"✓ Saved to test_response.mp3")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Health check
print("\n" + "=" * 60)
print("TEST 3: Health Check")
print("=" * 60)

try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"✓ Status: {response.status_code}")
    health = response.json()
    print(f"✓ Status: {health['status']}")
    print(f"✓ Agents ready:")
    for agent, ready in health['agents_ready'].items():
        print(f"  - {agent}: {ready}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
