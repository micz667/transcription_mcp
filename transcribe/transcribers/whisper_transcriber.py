"""
Whisper-based speech-to-text transcriber.
"""

import os
import logging
import time
from typing import List, Optional

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

from ..core.interfaces import Transcriber
from ..core.types import Document, ProcessingConfig, ProcessingStatus, TranscriptionSegment
from ..core.types import AudioSegment


class WhisperTranscriber(Transcriber):
    """Speech-to-text transcriber using OpenAI Whisper."""
    
    def __init__(self):
        """Initialize Whisper transcriber."""
        self.logger = logging.getLogger(__name__)
        self.model = None
        self._check_whisper()
    
    def _check_whisper(self):
        """Check if Whisper is available."""
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper not available. Please install openai-whisper.")
    
    def _map_model_name(self, model_name: str) -> str:
        """Map our model names to Whisper model names."""
        # Remove 'whisper-' prefix if present
        if model_name.startswith('whisper-'):
            return model_name.replace('whisper-', '')
        return model_name

    def _get_audio_duration(self, path: str) -> Optional[float]:
        """Return audio duration in seconds, or None if unavailable."""
        if not SOUNDFILE_AVAILABLE:
            return None
        try:
            info = sf.info(path)
            return float(info.duration)
        except Exception:
            return None

    def transcribe(self, document: Document, config: ProcessingConfig) -> Document:
        """
        Transcribe audio to text using Whisper.
        
        Args:
            document: Document with extracted audio
            config: Processing configuration
            
        Returns:
            Document with transcription results
        """
        try:
            if not hasattr(document, 'extracted_audio_path') or not document.extracted_audio_path:
                document.add_error("No audio file available for transcription")
                return document
            
            if not os.path.exists(document.extracted_audio_path):
                document.add_error("Audio file does not exist")
                return document
            
            # Load model if not already loaded
            if self.model is None:
                model_name = self._map_model_name(config.model.value)
                self.logger.info(f"Loading Whisper model: {model_name}")
                start_time = time.time()
                self.model = whisper.load_model(model_name)
                load_time = time.time() - start_time
                self.logger.info(f"Model loaded in {load_time:.2f} seconds")
            
            # Get audio duration for progress and time estimates
            audio_duration_sec = self._get_audio_duration(document.extracted_audio_path)
            if audio_duration_sec is not None:
                dur_m, dur_s = int(audio_duration_sec // 60), int(audio_duration_sec % 60)
                # On CPU/FP32, transcription is often ~0.1–0.5x realtime (2–10 min per 1 min audio)
                est_min = max(1, int(audio_duration_sec / 30))  # conservative: ~30s audio per 1 min
                est_max = max(2, int(audio_duration_sec / 6))   # slower: ~6s audio per 1 min
                self.logger.info(
                    f"Transcribing {dur_m}m {dur_s}s of audio "
                    f"(estimated {est_min}–{est_max} min on CPU, progress bar below)"
                )
            else:
                self.logger.info("Starting transcription... (progress bar below)")

            start_time = time.time()
            result = self.model.transcribe(
                document.extracted_audio_path,
                language=config.language if config.language != 'auto' else None,
                task='transcribe',
                verbose=False,  # show tqdm progress bar (frames) instead of silent run
            )
            transcription_time = time.time() - start_time
            self.logger.info(f"Transcription completed in {transcription_time:.1f}s")
            
            # Convert Whisper segments to our format
            segments = []
            for segment in result['segments']:
                transcription_segment = TranscriptionSegment(
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=segment['text'].strip(),
                    confidence=segment.get('avg_logprob', 0.0),
                    language=result.get('language', config.language)
                )
                segments.append(transcription_segment)
            
            # Update document
            document.transcription_segments = segments
            document.detected_language = result.get('language', config.language)
            document.status = ProcessingStatus.TRANSCRIBED
            document.processing_time += transcription_time
            
            self.logger.info(f"Transcription completed: {len(segments)} segments")
            return document
            
        except Exception as e:
            document.add_error(f"Transcription failed: {str(e)}")
            return document
    
    def transcribe_segment(self, segment: AudioSegment, config: ProcessingConfig) -> TranscriptionSegment:
        """
        Transcribe a single audio segment.
        
        Args:
            segment: Audio segment to transcribe
            config: Processing configuration
            
        Returns:
            Transcription segment with text and timing
        """
        try:
            # Load model if not already loaded
            if self.model is None:
                model_name = self._map_model_name(config.model.value)
                self.logger.info(f"Loading Whisper model: {model_name}")
                self.model = whisper.load_model(model_name)
            
            # Determine audio source
            if segment.file_path and os.path.exists(segment.file_path):
                audio_source = segment.file_path
            elif segment.audio_data:
                # Save audio data to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=f'.{segment.format.value}', delete=False) as temp_file:
                    temp_file.write(segment.audio_data)
                    audio_source = temp_file.name
            else:
                raise ValueError("Audio segment has no valid audio source (file_path or audio_data)")
            
            # Transcribe the segment
            result = self.model.transcribe(
                audio_source,
                language=config.language if config.language != 'auto' else None,
                task='transcribe'
            )
            
            # Create transcription segment
            transcription_segment = TranscriptionSegment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=result['text'].strip(),
                confidence=0.0,  # Whisper doesn't provide segment-level confidence for full transcription
                language=result.get('language', config.language)
            )
            
            # Clean up temporary file if created
            if segment.audio_data and audio_source:
                try:
                    os.remove(audio_source)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file: {e}")
            
            return transcription_segment
            
        except Exception as e:
            self.logger.error(f"Segment transcription failed: {str(e)}")
            # Return empty transcription segment with error in metadata
            return TranscriptionSegment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text="",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            'en', 'zh', 'de', 'es', 'ru', 'ko', 'fr', 'ja', 'pt', 'tr',
            'pl', 'ca', 'nl', 'ar', 'sv', 'it', 'id', 'hi', 'fi', 'vi',
            'he', 'uk', 'el', 'ms', 'cs', 'ro', 'da', 'hu', 'ta', 'no',
            'th', 'ur', 'hr', 'bg', 'lt', 'la', 'mi', 'ml', 'cy', 'sk',
            'te', 'fa', 'lv', 'bn', 'sr', 'az', 'sl', 'kn', 'et', 'mk',
            'br', 'eu', 'is', 'hy', 'ne', 'mn', 'bs', 'kk', 'sq', 'sw',
            'gl', 'mr', 'pa', 'si', 'km', 'sn', 'yo', 'so', 'af', 'oc',
            'ka', 'be', 'tg', 'sd', 'gu', 'am', 'yi', 'lo', 'uz', 'fo',
            'ht', 'ps', 'tk', 'nn', 'mt', 'sa', 'lb', 'my', 'bo', 'tl',
            'mg', 'as', 'tt', 'haw', 'ln', 'ha', 'ba', 'jw', 'su'
        ]
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models."""
        return ['whisper-tiny', 'whisper-base', 'whisper-small', 'whisper-medium', 'whisper-large']
    
    def cleanup_models(self):
        """Clean up loaded models."""
        if self.model is not None:
            self.model = None
            self.logger.info("Whisper model unloaded")
