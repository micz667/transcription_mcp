"""
Core types and interfaces for the transcription system.
Implements a consistent document format across all modules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json


class ProcessingStatus(Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    AUDIO_EXTRACTED = "audio_extracted"
    TRANSCRIBED = "transcribed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"


class TranscriptionModel(Enum):
    """Available transcription models."""
    WHISPER_BASE = "whisper-base"
    WHISPER_SMALL = "whisper-small"
    WHISPER_MEDIUM = "whisper-medium"
    WHISPER_LARGE = "whisper-large"
    GOOGLE_SPEECH = "google-speech"
    OPENAI_WHISPER = "openai-whisper"


@dataclass
class AudioSegment:
    """Represents a segment of audio with metadata."""
    start_time: float
    end_time: float
    duration: float
    audio_data: Optional[bytes] = None
    file_path: Optional[str] = None
    format: AudioFormat = AudioFormat.WAV
    sample_rate: int = 16000
    channels: int = 1


@dataclass
class TranscriptionSegment:
    """Represents a transcribed segment with timing information."""
    start_time: float
    end_time: float
    text: str
    confidence: float = 0.0
    speaker_id: Optional[str] = None
    language: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """
    Core document interface used throughout the system.
    Implements consistent input/output format with content and metadata.
    """
    # Content
    content: Union[str, bytes, Dict[str, Any]] = ""
    
    # Metadata
    id: str = ""
    source_path: str = ""
    output_path: str = ""
    content_type: str = ""
    format: str = ""
    
    # Processing metadata
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    
    # Audio-specific metadata
    audio_segments: List[AudioSegment] = field(default_factory=list)
    transcription_segments: List[TranscriptionSegment] = field(default_factory=list)
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for serialization."""
        return {
            "id": self.id,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "content_type": self.content_type,
            "format": self.format,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processing_time": self.processing_time,
            "config": self.config,
            "errors": self.errors,
            "warnings": self.warnings,
            "transcription_segments": [
                {
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "text": seg.text,
                    "confidence": seg.confidence,
                    "speaker_id": seg.speaker_id,
                    "language": seg.language,
                    "metadata": seg.metadata
                }
                for seg in self.transcription_segments
            ]
        }
    
    def to_json(self) -> str:
        """Convert document to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary."""
        # Convert status string back to enum
        if isinstance(data.get("status"), str):
            data["status"] = ProcessingStatus(data["status"])
        
        # Convert datetime strings back to datetime objects
        for field in ["created_at", "updated_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert transcription segments
        if "transcription_segments" in data:
            segments = []
            for seg_data in data["transcription_segments"]:
                segments.append(TranscriptionSegment(**seg_data))
            data["transcription_segments"] = segments
        
        return cls(**data)
    
    def add_error(self, error: str) -> None:
        """Add an error message to the document."""
        self.errors.append(error)
        self.status = ProcessingStatus.FAILED
        self.updated_at = datetime.now()
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message to the document."""
        self.warnings.append(warning)
        self.updated_at = datetime.now()
    
    def update_status(self, status: ProcessingStatus) -> None:
        """Update the processing status."""
        self.status = status
        self.updated_at = datetime.now()


@dataclass
class ProcessingConfig:
    """Configuration for processing pipeline."""
    # Audio extraction settings
    audio_format: AudioFormat = AudioFormat.WAV
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration: float = 30.0  # seconds
    
    # Transcription settings
    model: TranscriptionModel = TranscriptionModel.WHISPER_MEDIUM
    language: str = "auto"  # "auto" = Whisper detects; or ISO 639-1 (en, pl, etc.)
    task: str = "transcribe"  # or "translate"
    
    # Output settings
    include_timestamps: bool = True
    include_confidence: bool = True
    include_speaker_diarization: bool = False
    output_format: str = "markdown"
    
    # Processing settings
    max_workers: int = 4
    batch_size: int = 10
    timeout: float = 300.0  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "audio_format": self.audio_format.value,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_duration": self.chunk_duration,
            "model": self.model.value,
            "language": self.language,
            "task": self.task,
            "include_timestamps": self.include_timestamps,
            "include_confidence": self.include_confidence,
            "include_speaker_diarization": self.include_speaker_diarization,
            "output_format": self.output_format,
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
            "timeout": self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        """Create config from dictionary."""
        # Convert enum values back to enums
        if "audio_format" in data:
            data["audio_format"] = AudioFormat(data["audio_format"])
        if "model" in data:
            data["model"] = TranscriptionModel(data["model"])
        
        return cls(**data) 