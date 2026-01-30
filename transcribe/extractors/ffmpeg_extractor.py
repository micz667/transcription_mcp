"""
FFmpeg-based audio extractor for video files.
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Optional

from ..core.interfaces import AudioExtractor
from ..core.types import Document, ProcessingConfig, ProcessingStatus


class FFmpegAudioExtractor(AudioExtractor):
    """Audio extractor using FFmpeg for video files."""
    
    def __init__(self):
        """Initialize FFmpeg extractor."""
        self.logger = logging.getLogger(__name__)
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise RuntimeError("FFmpeg not found or not working properly")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def extract_audio(self, document: Document, config: ProcessingConfig) -> Document:
        """
        Extract audio from video file.
        
        Args:
            document: Document containing source and output paths
            config: Processing configuration
            
        Returns:
            Document with extracted audio path
        """
        try:
            source_path = document.source_path
            if not os.path.exists(source_path):
                document.add_error(f"Source file does not exist: {source_path}")
                return document
            
            # Create temporary audio file
            temp_dir = tempfile.mkdtemp()
            audio_filename = f"extracted_audio_{document.id}.{config.audio_format.value}"
            temp_audio_path = os.path.join(temp_dir, audio_filename)
            
            # FFmpeg command to extract audio
            cmd = [
                'ffmpeg', '-i', source_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Audio codec
                '-ar', str(config.sample_rate),  # Sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                temp_audio_path
            ]
            
            self.logger.info(f"Extracting audio with command: {' '.join(cmd)}")
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.timeout)
            
            if result.returncode != 0:
                document.add_error(f"FFmpeg extraction failed: {result.stderr}")
                return document
            
            if not os.path.exists(temp_audio_path):
                document.add_error("Audio extraction failed - output file not created")
                return document
            
            # Update document with extracted audio path
            document.extracted_audio_path = temp_audio_path
            document.status = ProcessingStatus.AUDIO_EXTRACTED
            
            self.logger.info(f"Audio extracted successfully: {temp_audio_path}")
            return document
            
        except subprocess.TimeoutExpired:
            document.add_error("Audio extraction timed out")
            return document
        except Exception as e:
            document.add_error(f"Audio extraction failed: {str(e)}")
            return document
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported video formats."""
        return [
            'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v',
            '3gp', 'ogv', 'ts', 'mts', 'm2ts', 'vob', 'asf'
        ]
    
    def validate_input(self, document: Document) -> bool:
        """
        Validate input document for audio extraction.
        
        Args:
            document: Document to validate
            
        Returns:
            True if document is valid for extraction
        """
        if not document.source_path:
            self.logger.error("Document has no source path")
            return False
        
        if not os.path.exists(document.source_path):
            self.logger.error(f"Source file does not exist: {document.source_path}")
            return False
        
        # Check if file format is supported
        file_ext = Path(document.source_path).suffix.lower().lstrip('.')
        if file_ext not in self.get_supported_formats():
            self.logger.error(f"Unsupported format: {file_ext}")
            return False
        
        return True
    
    def cleanup_temp_files(self, document: Document):
        """Clean up temporary files."""
        if hasattr(document, 'extracted_audio_path') and document.extracted_audio_path:
            try:
                if os.path.exists(document.extracted_audio_path):
                    os.remove(document.extracted_audio_path)
                    # Remove parent directory if empty
                    temp_dir = os.path.dirname(document.extracted_audio_path)
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup temp files: {str(e)}")
