#!/usr/bin/env python3
"""
YouTube Video Downloader with Subtitle Extraction

This script downloads YouTube videos and extracts their subtitles,
then optionally processes them through the transcription pipeline.

Run from repo root: python examples/youtube_downloader.py <url> [options]
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure repo root is on path (parent of examples/)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from transcribe.extractors.youtube_extractor import YouTubeExtractor
from transcribe.core.pipeline import TranscribePipeline
from transcribe.core.types import ProcessingConfig, TranscriptionModel, AudioFormat


def main():
    """Main function for YouTube downloader."""
    parser = argparse.ArgumentParser(description='YouTube Video Downloader with Subtitle Extraction')
    
    # Required arguments
    parser.add_argument('url', help='YouTube video URL')
    
    # Output options
    parser.add_argument('--output-dir', '-o', default='./downloads', 
                       help='Output directory for downloaded files (default: ./downloads)')
    parser.add_argument('--output-name', help='Custom name for output files (without extension)')
    
    # Subtitle options
    parser.add_argument('--languages', '-l', nargs='+', default=['en'], 
                       help='Preferred subtitle languages (default: en)')
    parser.add_argument('--no-auto-subtitles', action='store_true', 
                       help='Skip auto-generated subtitles')
    parser.add_argument('--no-manual-subtitles', action='store_true', 
                       help='Skip manual subtitles')
    parser.add_argument('--subtitles-only', action='store_true', 
                       help='Download only subtitles, not the video')
    
    # Processing options
    parser.add_argument('--transcribe', action='store_true', 
                       help='Also transcribe the video using Whisper')
    parser.add_argument('--model', '-m', default='whisper-medium',
                       choices=['whisper-base', 'whisper-small', 'whisper-medium', 'whisper-large'],
                       help='Whisper model for transcription (default: whisper-medium)')
    parser.add_argument('--language', default='auto',
                       help='Language for transcription (default: auto-detect)')
    
    # Format options
    parser.add_argument('--convert-to-markdown', action='store_true',
                       help='Convert subtitles to markdown format')
    parser.add_argument('--include-timestamps', action='store_true',
                       help='Include timestamps in markdown output')
    
    args = parser.parse_args()
    
    # Initialize YouTube extractor
    try:
        extractor = YouTubeExtractor()
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("Please install yt-dlp: pip install yt-dlp")
        sys.exit(1)
    
    # Get video info first
    print(f"🔍 Getting video information...")
    video_info = extractor.get_video_info(args.url)
    
    if 'error' in video_info:
        print(f"❌ Failed to get video info: {video_info['error']}")
        sys.exit(1)
    
    print(f"📹 Title: {video_info['title']}")
    print(f"👤 Uploader: {video_info['uploader']}")
    print(f"⏱️  Duration: {video_info['duration']} seconds")
    print(f"🌍 Available subtitle languages: {video_info['available_subtitles']}")
    print(f"🤖 Available auto-caption languages: {video_info['available_auto_captions']}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download video and subtitles
    print(f"\n📥 Downloading video and subtitles...")
    
    results = extractor.download_video_with_subtitles(
        video_url=args.url,
        output_dir=str(output_dir),
        include_auto_subtitles=not args.no_auto_subtitles,
        include_manual_subtitles=not args.no_manual_subtitles,
        preferred_languages=args.languages
    )
    
    if not results['success']:
        print(f"❌ Download failed: {results['error']}")
        sys.exit(1)
    
    print(f"✅ Download completed!")
    
    if results['video_file']:
        print(f"📹 Video: {Path(results['video_file']).name}")
    
    if results['subtitle_files']:
        print(f"📝 Subtitles: {len(results['subtitle_files'])} files")
        for sub_file in results['subtitle_files']:
            print(f"   - {Path(sub_file).name}")
    
    # Convert subtitles to markdown if requested
    if args.convert_to_markdown and results['subtitle_files']:
        print(f"\n📝 Converting subtitles to markdown...")
        
        for i, subtitle_file in enumerate(results['subtitle_files']):
            # Generate output filename
            if args.output_name:
                base_name = args.output_name
            else:
                base_name = Path(results['video_file']).stem if results['video_file'] else f"video_{i}"
            
            markdown_file = output_dir / f"{base_name}_subtitles_{i+1}.md"
            
            success = extractor.convert_subtitle_to_markdown(
                subtitle_file=str(subtitle_file),
                output_file=str(markdown_file),
                include_timestamps=args.include_timestamps
            )
            
            if success:
                print(f"✅ Converted: {markdown_file.name}")
            else:
                print(f"❌ Failed to convert: {Path(subtitle_file).name}")
    
    # Transcribe video if requested
    if args.transcribe and results['video_file']:
        print(f"\n🎤 Transcribing video with Whisper...")
        
        # Create transcription config
        config = ProcessingConfig(
            language=args.language,
            model=TranscriptionModel(args.model),
            audio_format=AudioFormat('wav'),
            include_timestamps=True,
            include_confidence=True
        )
        
        # Generate output filename
        if args.output_name:
            base_name = args.output_name
        else:
            base_name = Path(results['video_file']).stem
        
        transcript_file = output_dir / f"{base_name}_transcript.md"
        
        # Create pipeline and process
        pipeline = TranscribePipeline(config)
        
        try:
            result = pipeline.process(
                input_path=results['video_file'],
                output_path=str(transcript_file),
                config=config
            )
            
            if result.status.value == "completed":
                print(f"✅ Transcription completed: {transcript_file.name}")
            else:
                print(f"❌ Transcription failed: {result.errors}")
        
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
        
        finally:
            pipeline.cleanup()
    
    print(f"\n🎉 All done! Files saved to: {output_dir}")


if __name__ == '__main__':
    main()
