"""Speech-to-text and text-to-speech processing."""

import logging
import os
import tempfile
import threading
from typing import Optional
import whisper
import pyttsx3

logger = logging.getLogger(__name__)


class SpeechProcessor:
    """Handle speech-to-text and text-to-speech conversion."""

    def __init__(self):
        self.whisper_model = None
        self._load_whisper_model()

    def _load_whisper_model(self):
        try:
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded")
        except Exception as e:
            logger.error(f"Whisper load error: {e}")
            self.whisper_model = None

    def speech_to_text(self, audio_path: str) -> Optional[str]:
        try:
            if not self.whisper_model:
                return None
            result = self.whisper_model.transcribe(audio_path)
            return result["text"].strip()
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None

    def text_to_speech(self, text: str, output_path: Optional[str] = None) -> Optional[str]:
        try:
            if not output_path:
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                output_path = tmp.name
                tmp.close()

            result = []
            exception = []

            def run_tts():
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 150)
                    engine.setProperty('volume', 1.0)
                    voices = engine.getProperty('voices')
                    if voices:
                        engine.setProperty('voice', voices[0].id)
                    engine.save_to_file(text, output_path)
                    engine.runAndWait()
                    engine.stop()
                    result.append(True)
                except Exception as e:
                    exception.append(e)

            t = threading.Thread(target=run_tts, daemon=True)
            t.start()
            t.join(timeout=10)

            if exception:
                logger.error(f"TTS error: {exception[0]}")
                return None

            if not t.is_alive() and result:
                logger.info(f"TTS done: {output_path} ({os.path.getsize(output_path)} bytes)")
                return output_path

            logger.warning("TTS timed out")
            return None

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
