"""
Direct audio file processor for audio files.
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import List

from ..core.interfaces import AudioExtractor
from ..core.types import Document, ProcessingConfig, ProcessingStatus


class DirectAudioExtractor(AudioExtractor):
    """Direct processor for audio files (no extraction needed)."""
    
    def __init__(self):
        """Initialize direct audio extractor."""
        self.logger = logging.getLogger(__name__)
    
    def extract_audio(self, document: Document, config: ProcessingConfig) -> Document:
        """
        Process audio file directly (copy to temp location for processing).
        
        Args:
            document: Document containing source and output paths
            config: Processing configuration
            
        Returns:
            Document with processed audio path
        """
        try:
            source_path = document.source_path
            if not os.path.exists(source_path):
                document.add_error(f"Source file does not exist: {source_path}")
                return document
            
            # Create temporary copy of audio file
            temp_dir = tempfile.mkdtemp()
            audio_filename = f"audio_{document.id}.{Path(source_path).suffix[1:]}"
            temp_audio_path = os.path.join(temp_dir, audio_filename)
            
            # Copy audio file to temp location
            shutil.copy2(source_path, temp_audio_path)
            
            # Update document with processed audio path
            document.extracted_audio_path = temp_audio_path
            document.status = ProcessingStatus.AUDIO_EXTRACTED
            
            self.logger.info(f"Audio file processed: {temp_audio_path}")
            return document
            
        except Exception as e:
            document.add_error(f"Audio processing failed: {str(e)}")
            return document
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats."""
        return [
            'wav', 'mp3', 'flac', 'm4a', 'ogg', 'aac', 'wma', 'opus',
            'aiff', 'au', 'ra', 'amr', 'ac3', 'dts'
        ]
    
    def validate_input(self, document: Document) -> bool:
        """
        Validate input document for audio processing.
        
        Args:
            document: Document to validate
            
        Returns:
            True if document is valid for processing
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
