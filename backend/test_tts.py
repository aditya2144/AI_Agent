"""Test TTS endpoint."""

import requests

print("Testing TTS endpoint...")

payload = {
    "text": "Hello, I recommend the Dell XPS 15 for video editing with RTX GPU and 32GB RAM."
}

try:
    response = requests.post(
        "http://localhost:8000/api/text-to-speech",
        json=payload,
        timeout=15
    )
    
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Audio size: {len(response.content)} bytes")
    
    if response.status_code == 200:
        # Save to file
        with open("test_audio.mp3", "wb") as f:
            f.write(response.content)
        print("SUCCESS: Audio saved to test_audio.mp3")
    else:
        print(f"ERROR: {response.text}")
        
except Exception as e:
    print(f"ERROR: {e}")
