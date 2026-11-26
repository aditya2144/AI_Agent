"""Test pyttsx3 TTS."""
import pyttsx3
import tempfile
import os

print("Testing pyttsx3...")

try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    
    # Save to file
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    output_path = temp_file.name
    temp_file.close()
    
    engine.save_to_file("Hello, I am your TechStore sales agent. How can I help you today?", output_path)
    engine.runAndWait()
    
    size = os.path.getsize(output_path)
    print(f"SUCCESS: Audio saved to {output_path} ({size} bytes)")
    os.remove(output_path)
    
except Exception as e:
    print(f"ERROR: {e}")
