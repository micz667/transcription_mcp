#!/usr/bin/env python3
"""
Basic usage example for the transcription pipeline.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import TranscribePipeline
from core.types import ProcessingConfig


def main():
    """Example of basic transcription usage."""
    
    # Example video file (replace with your actual file)
    input_file = "example_video.mp4"
    output_file = "transcript.md"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("Please place a video file named 'example_video.mp4' in the examples directory")
        return
    
    # Create custom configuration
    config = ProcessingConfig(
        language="en",
        model="whisper-medium",
        audio_format="wav",
        sample_rate=16000,
        chunk_duration=30.0,
        include_timestamps=True,
        include_confidence=True,
        max_workers=2,
        timeout=300.0
    )
    
    # Create pipeline
    pipeline = TranscribePipeline(config)
    
    try:
        print(f"🎬 Starting transcription of: {input_file}")
        print(f"📝 Output will be saved to: {output_file}")
        print(f"🔧 Using model: {config.model.value}")
        print(f"🌍 Language: {config.language}")
        print("⏳ Processing...")
        
        # Process the video
        result = pipeline.process(input_file, output_file, config)
        
        if result.status.value == "completed":
            print(f"✅ Transcription completed successfully!")
            print(f"📄 Output saved to: {output_file}")
            print(f"⏱️  Processing time: {result.processing_time:.2f} seconds")
            print(f"📊 Segments transcribed: {len(result.transcription_segments)}")
        else:
            print(f"❌ Transcription failed!")
            print(f"🚨 Errors: {result.errors}")
            
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
    
    finally:
        # Cleanup
        pipeline.cleanup()


if __name__ == "__main__":
    main() 