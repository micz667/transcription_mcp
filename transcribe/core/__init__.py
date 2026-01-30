"""
Core modules for the transcription pipeline.

This package contains the fundamental types, interfaces, and pipeline logic.
"""

from .types import Document, ProcessingConfig, ProcessingStatus, TranscriptionModel, AudioFormat
from .interfaces import AudioExtractor, Transcriber, Formatter
from .pipeline import TranscribePipeline

__all__ = [
    "Document",
    "ProcessingConfig", 
    "ProcessingStatus",
    "TranscriptionModel",
    "AudioFormat",
    "AudioExtractor",
    "Transcriber", 
    "Formatter",
    "TranscribePipeline"
]
