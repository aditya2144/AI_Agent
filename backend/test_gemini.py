"""Test which Gemini models are available."""
import os
from dotenv import load_dotenv
load_dotenv()

import google.genai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"API Key: {GEMINI_API_KEY[:20]}...")

client = genai.Client(api_key=GEMINI_API_KEY)

print("\nAvailable models:")
try:
    for model in client.models.list():
        print(f"  - {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTesting gemini-2.0-flash...")
try:
    from google.genai import types
    from google.genai.types import GenerateContentConfig
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[types.Content(role="user", parts=[types.Part.from_text(text="Say hello in one sentence.")])],
        config=GenerateContentConfig(max_output_tokens=100)
    )
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting gemini-1.5-flash...")
try:
    from google.genai import types
    from google.genai.types import GenerateContentConfig
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[types.Content(role="user", parts=[types.Part.from_text(text="Say hello in one sentence.")])],
        config=GenerateContentConfig(max_output_tokens=100)
    )
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
