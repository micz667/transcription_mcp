"""
Movie Audio Transcription Tool

A modular system for extracting audio from movies and transcribing it to markdown files.
"""

__version__ = "1.0.0"
__author__ = "Movie Audio Transcription Tool"

from .core.pipeline import TranscribePipeline
from .core.types import Document, ProcessingConfig, ProcessingStatus

__all__ = [
    "TranscribePipeline",
    "Document", 
    "ProcessingConfig",
    "ProcessingStatus"
]
