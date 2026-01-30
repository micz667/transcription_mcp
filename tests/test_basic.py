"""
Basic tests for the transcription system.
"""

import pytest
import os
import tempfile
from pathlib import Path

# Add transcribe package to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from transcribe.core.types import Document, ProcessingConfig, ProcessingStatus
from transcribe.core.interfaces import AudioExtractor, Transcriber, Formatter
from transcribe.extractors.ffmpeg_extractor import FFmpegAudioExtractor
from transcribe.transcribers.whisper_transcriber import WhisperTranscriber
from transcribe.formatters.markdown_formatter import MarkdownFormatter


class TestBasicFunctionality:
    """Test basic functionality of the transcription system."""
    
    def test_document_creation(self):
        """Test document creation and serialization."""
        doc = Document(
            id="test-123",
            source_path="/path/to/video.mp4",
            output_path="/path/to/output.md"
        )
        
        assert doc.id == "test-123"
        assert doc.source_path == "/path/to/video.mp4"
        assert doc.status == ProcessingStatus.PENDING
        
        # Test serialization
        doc_dict = doc.to_dict()
        assert doc_dict["id"] == "test-123"
        assert doc_dict["source_path"] == "/path/to/video.mp4"
    
    def test_processing_config(self):
        """Test processing configuration."""
        config = ProcessingConfig(
            language="en",
            model="whisper-medium",
            audio_format="wav",
            sample_rate=16000
        )
        
        assert config.language == "en"
        assert config.model.value == "whisper-medium"
        assert config.audio_format.value == "wav"
        assert config.sample_rate == 16000
        
        # Test serialization
        config_dict = config.to_dict()
        assert config_dict["language"] == "en"
        assert config_dict["model"] == "whisper-medium"
    
    def test_ffmpeg_extractor_initialization(self):
        """Test FFmpeg extractor initialization."""
        try:
            extractor = FFmpegAudioExtractor()
            assert extractor is not None
            assert len(extractor.get_supported_formats()) > 0
        except RuntimeError as e:
            if "FFmpeg not found" in str(e):
                pytest.skip("FFmpeg not available")
            else:
                raise
    
    def test_whisper_transcriber_initialization(self):
        """Test Whisper transcriber initialization."""
        try:
            transcriber = WhisperTranscriber()
            assert transcriber is not None
            assert len(transcriber.get_supported_languages()) > 0
            assert len(transcriber.get_available_models()) > 0
        except RuntimeError as e:
            if "Whisper not available" in str(e):
                pytest.skip("Whisper not available")
            else:
                raise
    
    def test_markdown_formatter_initialization(self):
        """Test markdown formatter initialization."""
        formatter = MarkdownFormatter()
        assert formatter is not None
        assert len(formatter.get_supported_formats()) > 0
        assert len(formatter.get_available_templates()) > 0
    
    def test_document_error_handling(self):
        """Test document error handling."""
        doc = Document()
        
        # Add error
        doc.add_error("Test error")
        assert len(doc.errors) == 1
        assert doc.errors[0] == "Test error"
        assert doc.status == ProcessingStatus.FAILED
        
        # Add warning
        doc.add_warning("Test warning")
        assert len(doc.warnings) == 1
        assert doc.warnings[0] == "Test warning"
    
    def test_file_validation(self):
        """Test file validation utilities."""
        from transcribe.utils.file_utils import validate_video_file, get_video_files
        
        # Test with non-existent file
        is_valid, error = validate_video_file("/non/existent/file.mp4")
        assert not is_valid
        assert "does not exist" in error
        
        # Test with existing directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a fake video file
            fake_video = os.path.join(temp_dir, "test.mp4")
            with open(fake_video, 'w') as f:
                f.write("fake video content")
            
            # Test validation
            is_valid, error = validate_video_file(fake_video)
            # Should fail because it's not a real video file
            assert not is_valid
    
    def test_markdown_template_generation(self):
        """Test markdown template generation."""
        formatter = MarkdownFormatter()
        
        # Test default template
        template = formatter.templates['default']
        assert '{title}' in template
        assert '{segments}' in template
        assert '{source_file}' in template
        
        # Test minimal template
        minimal_template = formatter.templates['minimal']
        assert '{title}' in minimal_template
        assert '{segments}' in minimal_template
        assert len(minimal_template) < len(template)  # Should be shorter


if __name__ == "__main__":
    pytest.main([__file__]) 