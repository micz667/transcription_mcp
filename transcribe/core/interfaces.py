"""
Base interfaces for modular components.
Implements clear separation of concerns with precise input/output structures.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .types import Document, ProcessingConfig, AudioSegment, TranscriptionSegment


class AudioExtractor(ABC):
    """
    Base interface for audio extraction components.
    Handles one specific responsibility: extracting audio from video files.
    """
    
    @abstractmethod
    def extract_audio(self, document: Document, config: ProcessingConfig) -> Document:
        """
        Extract audio from video file and return updated document.
        
        Args:
            document: Document containing video file information
            config: Processing configuration
            
        Returns:
            Document with extracted audio segments
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported video formats."""
        pass
    
    @abstractmethod
    def validate_input(self, document: Document) -> bool:
        """Validate input document for audio extraction."""
        pass


class Transcriber(ABC):
    """
    Base interface for transcription components.
    Handles one specific responsibility: converting speech to text.
    """
    
    @abstractmethod
    def transcribe(self, document: Document, config: ProcessingConfig) -> Document:
        """
        Transcribe audio segments to text and return updated document.
        
        Args:
            document: Document containing audio segments
            config: Processing configuration
            
        Returns:
            Document with transcription segments
        """
        pass
    
    @abstractmethod
    def transcribe_segment(self, segment: AudioSegment, config: ProcessingConfig) -> TranscriptionSegment:
        """
        Transcribe a single audio segment.
        
        Args:
            segment: Audio segment to transcribe
            config: Processing configuration
            
        Returns:
            Transcription segment with text and timing
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available transcription models."""
        pass


class Formatter(ABC):
    """
    Base interface for output formatting components.
    Handles one specific responsibility: formatting transcription to output format.
    """
    
    @abstractmethod
    def format(self, document: Document, config: ProcessingConfig) -> Document:
        """
        Format transcription segments to output format.
        
        Args:
            document: Document containing transcription segments
            config: Processing configuration
            
        Returns:
            Document with formatted content
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        pass
    
    @abstractmethod
    def validate_output(self, document: Document) -> bool:
        """Validate output document format."""
        pass


class StateManager(ABC):
    """
    Base interface for state management.
    Tracks conversation context, tasks, and actions.
    """
    
    @abstractmethod
    def save_document(self, document: Document) -> None:
        """Save document to state storage."""
        pass
    
    @abstractmethod
    def load_document(self, document_id: str) -> Optional[Document]:
        """Load document from state storage."""
        pass
    
    @abstractmethod
    def update_document_status(self, document_id: str, status: str) -> None:
        """Update document processing status."""
        pass
    
    @abstractmethod
    def get_processing_queue(self) -> List[Document]:
        """Get list of documents in processing queue."""
        pass
    
    @abstractmethod
    def cleanup_old_documents(self, max_age_hours: int = 24) -> None:
        """Clean up old documents from storage."""
        pass


class ErrorHandler(ABC):
    """
    Base interface for error handling components.
    Implements proper error handling with informative feedback.
    """
    
    @abstractmethod
    def handle_error(self, document: Document, error: Exception, context: str) -> Document:
        """
        Handle processing error and return updated document.
        
        Args:
            document: Document that encountered error
            error: Exception that occurred
            context: Context where error occurred
            
        Returns:
            Document with error information
        """
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: str, metadata: Dict[str, Any]) -> None:
        """Log error for monitoring and debugging."""
        pass
    
    @abstractmethod
    def get_error_summary(self, document_id: str) -> Dict[str, Any]:
        """Get error summary for document."""
        pass


class RateLimiter(ABC):
    """
    Base interface for rate limiting components.
    Implements proper rate limiting and cost control mechanisms.
    """
    
    @abstractmethod
    def check_rate_limit(self, operation: str, user_id: Optional[str] = None) -> bool:
        """Check if operation is allowed under rate limits."""
        pass
    
    @abstractmethod
    def record_operation(self, operation: str, cost: float, user_id: Optional[str] = None) -> None:
        """Record operation for cost tracking."""
        pass
    
    @abstractmethod
    def get_usage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage statistics."""
        pass
    
    @abstractmethod
    def reset_limits(self, user_id: Optional[str] = None) -> None:
        """Reset rate limits for user."""
        pass


class MemorySystem(ABC):
    """
    Base interface for memory system components.
    Builds flexible memory system with both short-term and long-term storage.
    """
    
    @abstractmethod
    def store_short_term(self, key: str, data: Any, ttl_seconds: int = 3600) -> None:
        """Store data in short-term memory."""
        pass
    
    @abstractmethod
    def retrieve_short_term(self, key: str) -> Optional[Any]:
        """Retrieve data from short-term memory."""
        pass
    
    @abstractmethod
    def store_long_term(self, key: str, data: Any) -> None:
        """Store data in long-term memory."""
        pass
    
    @abstractmethod
    def retrieve_long_term(self, key: str) -> Optional[Any]:
        """Retrieve data from long-term memory."""
        pass
    
    @abstractmethod
    def search_memory(self, query: str, memory_type: str = "long_term") -> List[Any]:
        """Search memory for relevant information."""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> None:
        """Clean up expired short-term memory entries."""
        pass 