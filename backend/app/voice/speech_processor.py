"""Speech-to-text and text-to-speech processing."""

import logging
import os
from typing import Optional
import whisper
from gtts import gTTS
from pydub import AudioSegment
import tempfile

logger = logging.getLogger(__name__)


class SpeechProcessor:
    """Handle speech-to-text and text-to-speech conversion."""
    
    def __init__(self):
        """Initialize speech processor."""
        self.whisper_model = None
        self._load_whisper_model()
    
    def _load_whisper_model(self) -> None:
        """Load Whisper model for speech-to-text."""
        try:
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            self.whisper_model = None
    
    def speech_to_text(self, audio_path: str) -> Optional[str]:
        """Convert speech to text using Whisper.
        
        Args:
            audio_path: Path to audio file.
            
        Returns:
            Transcribed text or None if error.
        """
        try:
            if not self.whisper_model:
                logger.error("Whisper model not loaded")
                return None
            
            # Transcribe audio
            result = self.whisper_model.transcribe(audio_path)
            text = result["text"].strip()
            
            logger.info(f"Audio transcribed successfully: {text[:50]}...")
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    def text_to_speech(
        self,
        text: str,
        language: str = "en",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """Convert text to speech using gTTS.
        
        Args:
            text: Text to convert to speech.
            language: Language code (default: English).
            output_path: Path to save audio file. If None, creates temp file.
            
        Returns:
            Path to audio file or None if error.
        """
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to file
            if not output_path:
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            tts.save(output_path)
            logger.info(f"Text converted to speech: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return None
    
    def convert_audio_format(
        self,
        input_path: str,
        output_format: str = "wav",
    ) -> Optional[str]:
        """Convert audio between formats.
        
        Args:
            input_path: Path to input audio file.
            output_format: Desired output format (default: wav).
            
        Returns:
            Path to converted audio file or None if error.
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(input_path)
            
            # Create output path
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}.{output_format}"
            
            # Export in desired format
            audio.export(output_path, format=output_format)
            logger.info(f"Audio converted to {output_format}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return None
    
    def get_audio_duration(self, audio_path: str) -> Optional[float]:
        """Get duration of audio file in seconds.
        
        Args:
            audio_path: Path to audio file.
            
        Returns:
            Duration in seconds or None if error.
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            duration_seconds = len(audio) / 1000.0
            return duration_seconds
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return None
