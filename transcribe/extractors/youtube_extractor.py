"""
YouTube video downloader and subtitle extractor.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

from ..core.interfaces import AudioExtractor
from ..core.types import Document, ProcessingConfig, ProcessingStatus


class YouTubeExtractor(AudioExtractor):
    """YouTube video downloader and subtitle extractor."""
    
    def __init__(self):
        """Initialize YouTube extractor."""
        self.logger = logging.getLogger(__name__)
        self._check_yt_dlp()
    
    def _check_yt_dlp(self):
        """Check if yt-dlp is available."""
        if not YT_DLP_AVAILABLE:
            raise RuntimeError("yt-dlp not available. Please install yt-dlp: pip install yt-dlp")
    
    def download_video_with_subtitles(self, video_url: str, output_dir: str, 
                                    include_auto_subtitles: bool = True,
                                    include_manual_subtitles: bool = True,
                                    preferred_languages: List[str] = None) -> Dict[str, Any]:
        """
        Download YouTube video and extract available subtitles.
        
        Args:
            video_url: YouTube video URL
            output_dir: Directory to save files
            include_auto_subtitles: Whether to include auto-generated subtitles
            include_manual_subtitles: Whether to include manual subtitles
            preferred_languages: List of preferred language codes (e.g., ['en', 'pl'])
            
        Returns:
            Dictionary with download results
        """
        if preferred_languages is None:
            preferred_languages = ['en']
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[height<=720]',  # Download best quality up to 720p
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'writesubtitles': True,
            'writeautomaticsub': include_auto_subtitles,
            'subtitleslangs': preferred_languages,
            'subtitlesformat': 'srt/vtt/best',
            'skip_download': False,
            'quiet': False,
            'no_warnings': False,
        }
        
        # If we only want subtitles, not the video
        if not include_manual_subtitles and not include_auto_subtitles:
            ydl_opts['skip_download'] = True
            ydl_opts['writesubtitles'] = False
            ydl_opts['writeautomaticsub'] = False
        
        results = {
            'video_file': None,
            'subtitle_files': [],
            'available_languages': [],
            'video_info': {},
            'success': False,
            'error': None
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(video_url, download=False)
                results['video_info'] = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', '')[:500] + '...' if info.get('description') else ''
                }
                
                # Check available subtitles
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})
                
                available_langs = set()
                if include_manual_subtitles and subtitles:
                    available_langs.update(subtitles.keys())
                if include_auto_subtitles and automatic_captions:
                    available_langs.update(automatic_captions.keys())
                
                results['available_languages'] = list(available_langs)
                
                self.logger.info(f"Available subtitle languages: {results['available_languages']}")
                
                # Download video and subtitles
                ydl.download([video_url])
                
                # Find downloaded files
                video_files = []
                subtitle_files = []
                
                for file in os.listdir(output_dir):
                    file_path = os.path.join(output_dir, file)
                    if os.path.isfile(file_path):
                        if file.endswith(('.mp4', '.webm', '.mkv', '.avi')):
                            video_files.append(file_path)
                        elif file.endswith(('.srt', '.vtt', '.ass', '.ssa')):
                            subtitle_files.append(file_path)
                
                results['video_file'] = video_files[0] if video_files else None
                results['subtitle_files'] = subtitle_files
                results['success'] = True
                
                self.logger.info(f"Downloaded video: {results['video_file']}")
                self.logger.info(f"Downloaded subtitles: {len(results['subtitle_files'])} files")
                
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(f"YouTube download failed: {str(e)}")
        
        return results
    
    def extract_audio(self, document: Document, config: ProcessingConfig) -> Document:
        """
        Extract audio from YouTube video (this method is for compatibility with AudioExtractor interface).
        For YouTube videos, use download_video_with_subtitles instead.
        
        Args:
            document: Document containing source and output paths
            config: Processing configuration
            
        Returns:
            Document with extracted audio path
        """
        # This method is not typically used for YouTube videos
        # Use download_video_with_subtitles instead
        document.add_error("Use download_video_with_subtitles method for YouTube videos")
        return document
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported YouTube formats."""
        return ['youtube', 'youtu.be']
    
    def validate_input(self, document: Document) -> bool:
        """Validate input document for YouTube extraction."""
        if not hasattr(document, 'source_path') or not document.source_path:
            return False
        
        # Check if it's a YouTube URL
        source_path = document.source_path.lower()
        return 'youtube.com' in source_path or 'youtu.be' in source_path
    
    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        Get information about a YouTube video without downloading.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Dictionary with video information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'available_subtitles': list(info.get('subtitles', {}).keys()),
                    'available_auto_captions': list(info.get('automatic_captions', {}).keys()),
                    'formats': [f.get('format_id', 'unknown') for f in info.get('formats', [])]
                }
        except Exception as e:
            self.logger.error(f"Failed to get video info: {str(e)}")
            return {'error': str(e)}
    
    def convert_subtitle_to_markdown(self, subtitle_file: str, output_file: str, 
                                   include_timestamps: bool = True) -> bool:
        """
        Convert subtitle file (SRT/VTT) to markdown format.
        
        Args:
            subtitle_file: Path to subtitle file
            output_file: Path for output markdown file
            include_timestamps: Whether to include timestamps
            
        Returns:
            True if conversion successful
        """
        try:
            import re
            
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT format
            if subtitle_file.endswith('.srt'):
                # Remove SRT formatting and extract text
                srt_pattern = r'\d+\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\n*$)'
                matches = re.findall(srt_pattern, content, re.DOTALL)
                
                markdown_content = "# YouTube Video Subtitles\n\n"
                
                for timestamp, text in matches:
                    # Clean up text
                    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
                    text = text.strip().replace('\n', ' ')
                    
                    if include_timestamps:
                        markdown_content += f"**{timestamp}**\n{text}\n\n"
                    else:
                        markdown_content += f"{text}\n\n"
            
            # Parse VTT format
            elif subtitle_file.endswith('.vtt'):
                # Remove VTT header and formatting
                lines = content.split('\n')
                markdown_content = "# YouTube Video Subtitles\n\n"
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Look for timestamp lines
                    if '-->' in line:
                        timestamp = line
                        # Get the next non-empty line as text
                        i += 1
                        while i < len(lines) and not lines[i].strip():
                            i += 1
                        
                        if i < len(lines):
                            text = lines[i].strip()
                            # Clean up text
                            text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
                            
                            if include_timestamps:
                                markdown_content += f"**{timestamp}**\n{text}\n\n"
                            else:
                                markdown_content += f"{text}\n\n"
                    i += 1
            
            # Write markdown file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Converted subtitles to markdown: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to convert subtitles: {str(e)}")
            return False
