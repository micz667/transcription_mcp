#!/usr/bin/env python3
"""
Example script showing how to use the YouTube downloader.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import transcribe package
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcribe.extractors.youtube_extractor import YouTubeExtractor


def main():
    """Example usage of YouTube downloader."""
    
    # Example YouTube URL (replace with actual URL)
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for demo
    
    print("🎬 YouTube Video Downloader Example")
    print("=" * 50)
    
    # Initialize extractor
    try:
        extractor = YouTubeExtractor()
        print("✅ YouTube extractor initialized")
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("Please install yt-dlp: pip install yt-dlp")
        return
    
    # Get video information
    print(f"\n🔍 Getting video information...")
    video_info = extractor.get_video_info(video_url)
    
    if 'error' in video_info:
        print(f"❌ Failed to get video info: {video_info['error']}")
        return
    
    print(f"📹 Title: {video_info['title']}")
    print(f"👤 Uploader: {video_info['uploader']}")
    print(f"⏱️  Duration: {video_info['duration']} seconds")
    print(f"🌍 Available subtitle languages: {video_info['available_subtitles']}")
    print(f"🤖 Available auto-caption languages: {video_info['available_auto_captions']}")
    
    # Ask user if they want to proceed
    response = input(f"\nDo you want to download this video? (y/n): ").lower().strip()
    if response != 'y':
        print("Download cancelled.")
        return
    
    # Download video and subtitles
    output_dir = "./downloads"
    print(f"\n📥 Downloading to: {output_dir}")
    
    results = extractor.download_video_with_subtitles(
        video_url=video_url,
        output_dir=output_dir,
        include_auto_subtitles=True,
        include_manual_subtitles=True,
        preferred_languages=['en', 'pl']  # English and Polish
    )
    
    if not results['success']:
        print(f"❌ Download failed: {results['error']}")
        return
    
    print(f"✅ Download completed!")
    
    if results['video_file']:
        print(f"📹 Video: {Path(results['video_file']).name}")
    
    if results['subtitle_files']:
        print(f"📝 Subtitles: {len(results['subtitle_files'])} files")
        for sub_file in results['subtitle_files']:
            print(f"   - {Path(sub_file).name}")
    
    # Convert first subtitle to markdown
    if results['subtitle_files']:
        print(f"\n📝 Converting first subtitle to markdown...")
        
        subtitle_file = results['subtitle_files'][0]
        markdown_file = os.path.join(output_dir, "subtitles.md")
        
        success = extractor.convert_subtitle_to_markdown(
            subtitle_file=subtitle_file,
            output_file=markdown_file,
            include_timestamps=True
        )
        
        if success:
            print(f"✅ Converted to markdown: {markdown_file}")
        else:
            print(f"❌ Failed to convert to markdown")
    
    print(f"\n🎉 All done! Check the '{output_dir}' directory for downloaded files.")


if __name__ == '__main__':
    main()
