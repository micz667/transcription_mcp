"""
Main transcription pipeline.
Orchestrates audio extraction, transcription, and formatting components.
"""

import os
import logging
import tempfile
from typing import Callable, List, Optional, Dict, Any
from pathlib import Path
import uuid

from .types import Document, ProcessingConfig, ProcessingStatus
from .interfaces import AudioExtractor, Transcriber, Formatter
from ..extractors.ffmpeg_extractor import FFmpegAudioExtractor
from ..extractors.audio_extractor import DirectAudioExtractor
from ..transcribers.whisper_transcriber import WhisperTranscriber
from ..formatters.markdown_formatter import MarkdownFormatter


class TranscribePipeline:
    """
    Main transcription pipeline.
    Implements loop-based execution model with proper exit conditions.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize transcription pipeline.
        
        Args:
            config: Processing configuration
        """
        self.config = config or ProcessingConfig()
        
        # Initialize components
        self.video_extractor: AudioExtractor = FFmpegAudioExtractor()
        self.audio_extractor: AudioExtractor = DirectAudioExtractor()
        self.transcriber: Transcriber = WhisperTranscriber()
        self.formatter: Formatter = MarkdownFormatter()
        
        # Setup logging
        self._setup_logging()
        
        # Processing state
        self.processing_queue: List[Document] = []
        self.completed_documents: List[Document] = []
        self.failed_documents: List[Document] = []
    
    def _setup_logging(self):
        """Setup logging configuration. Uses cwd or temp dir for log file to avoid
        read-only filesystem errors when run under MCP (e.g. cwd is /)."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        # Only add file handler if we can write (avoids Errno 30 on read-only fs)
        for log_dir in (os.getcwd(), tempfile.gettempdir()):
            log_path = os.path.join(log_dir, 'transcribe.log')
            try:
                fh = logging.FileHandler(log_path, encoding='utf-8')
                fh.setFormatter(logging.Formatter(log_format))
                handlers.append(fh)
                break
            except OSError:
                continue
        logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)
        self.logger = logging.getLogger(__name__)
    
    def process(
        self,
        input_path: str,
        output_path: str,
        config: Optional[ProcessingConfig] = None,
        progress_callback: Optional[Callable[[str, float, float], None]] = None,
    ) -> Document:
        """
        Process a single video file.

        Args:
            input_path: Path to input video file
            output_path: Path for output markdown file
            config: Processing configuration (uses default if None)
            progress_callback: Optional (message, progress, total) for progress reporting

        Returns:
            Document with processing results
        """
        def report(msg: str, progress: float, total: float = 4.0) -> None:
            if progress_callback:
                progress_callback(msg, progress, total)

        # Create document
        document = Document(
            id=str(uuid.uuid4()),
            source_path=input_path,
            output_path=output_path,
            config=config.to_dict() if config else self.config.to_dict()
        )

        self.logger.info(f"Starting processing: {input_path}")
        report("Starting…", 0)

        try:
            # Step 1: Audio extraction
            report("Extracting audio…", 1)
            self.logger.info("Processing audio...")
            document = self._extract_audio(document, config or self.config)

            if document.status == ProcessingStatus.FAILED:
                self.failed_documents.append(document)
                return document

            # Step 2: Transcription
            report("Transcribing with Whisper… (this may take a few minutes)", 2)
            self.logger.info("Transcribing audio...")
            document = self.transcriber.transcribe(document, config or self.config)

            if document.status == ProcessingStatus.FAILED:
                self.failed_documents.append(document)
                return document

            # Step 3: Formatting
            report("Formatting output…", 3)
            self.logger.info("Formatting output...")
            document = self.formatter.format(document, config or self.config)

            if document.status == ProcessingStatus.FAILED:
                self.failed_documents.append(document)
                return document

            # Cleanup temporary files
            self._cleanup_temp_files(document)

            self.completed_documents.append(document)
            report("Done", 4)
            self.logger.info(f"Processing completed: {output_path}")

            return document

        except Exception as e:
            document.add_error(f"Pipeline processing failed: {str(e)}")
            self.failed_documents.append(document)
            self.logger.error(f"Processing failed: {str(e)}")
            return document
    
    def process_batch(
        self,
        input_paths: List[str],
        output_dir: str,
        config: Optional[ProcessingConfig] = None,
        progress_callback: Optional[Callable[[str, float, float], None]] = None,
    ) -> List[Document]:
        """
        Process multiple video files.

        Args:
            input_paths: List of input video file paths
            output_dir: Directory for output markdown files
            config: Processing configuration (uses default if None)
            progress_callback: Optional (message, progress, total) for progress reporting

        Returns:
            List of documents with processing results
        """
        results = []

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for i, input_path in enumerate(input_paths):
            # Generate output path
            input_name = Path(input_path).stem
            output_path = os.path.join(output_dir, f"{input_name}.md")

            # Process file (pass through progress callback)
            document = self.process(input_path, output_path, config, progress_callback=progress_callback)
            results.append(document)
            
            # Log progress
            progress = (i + 1) / len(input_paths) * 100
            self.logger.info(f"Batch progress: {progress:.1f}% ({i + 1}/{len(input_paths)})")
        
        return results
    
    def _extract_audio(self, document: Document, config: ProcessingConfig) -> Document:
        """Extract audio from file, automatically detecting if it's video or audio."""
        file_path = document.source_path
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        
        # Video formats
        video_formats = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 
                        '3gp', 'ogv', 'ts', 'mts', 'm2ts', 'vob', 'asf']
        
        # Audio formats
        audio_formats = ['wav', 'mp3', 'flac', 'm4a', 'ogg', 'aac', 'wma', 'opus',
                        'aiff', 'au', 'ra', 'amr', 'ac3', 'dts']
        
        if file_ext in video_formats:
            self.logger.info("Detected video file, extracting audio...")
            return self.video_extractor.extract_audio(document, config)
        elif file_ext in audio_formats:
            self.logger.info("Detected audio file, processing directly...")
            return self.audio_extractor.extract_audio(document, config)
        else:
            document.add_error(f"Unsupported file format: {file_ext}")
            return document
    
    def _cleanup_temp_files(self, document: Document):
        """Clean up temporary files created during processing."""
        try:
            if hasattr(self.video_extractor, 'cleanup_temp_files'):
                self.video_extractor.cleanup_temp_files(document)
            if hasattr(self.audio_extractor, 'cleanup_temp_files'):
                self.audio_extractor.cleanup_temp_files(document)
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {str(e)}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'completed': len(self.completed_documents),
            'failed': len(self.failed_documents),
            'queued': len(self.processing_queue),
            'total_processing_time': sum(doc.processing_time for doc in self.completed_documents),
            'average_processing_time': sum(doc.processing_time for doc in self.completed_documents) / len(self.completed_documents) if self.completed_documents else 0
        }
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self.transcriber, 'cleanup_models'):
                self.transcriber.cleanup_models()
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {str(e)}")
