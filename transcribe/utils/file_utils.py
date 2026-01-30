"""
File utility functions for the transcription tool.
"""

import os
from pathlib import Path
from typing import List, Tuple


def get_video_files(directory: str) -> List[str]:
    """
    Get list of video files from directory.
    
    Args:
        directory: Directory to search for video files
        
    Returns:
        List of video file paths
    """
    video_extensions = [
        '*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm',
        '*.m4v', '*.3gp', '*.ogv', '*.ts', '*.mts', '*.m2ts', '*.vob', '*.asf'
    ]
    
    video_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return video_files
    
    for ext in video_extensions:
        video_files.extend([str(f) for f in directory_path.glob(ext)])
    
    return sorted(video_files)


def get_audio_files(directory: str) -> List[str]:
    """
    Get list of audio files from directory.
    
    Args:
        directory: Directory to search for audio files
        
    Returns:
        List of audio file paths
    """
    audio_extensions = [
        '*.wav', '*.mp3', '*.flac', '*.m4a', '*.ogg', '*.aac', '*.wma',
        '*.opus', '*.aiff', '*.au', '*.ra', '*.amr', '*.ac3', '*.dts'
    ]
    
    audio_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return audio_files
    
    for ext in audio_extensions:
        audio_files.extend([str(f) for f in directory_path.glob(ext)])
    
    return sorted(audio_files)


def validate_video_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate if a file is a valid video file.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"Path is not a file: {file_path}"
    
    # Check file extension
    video_extensions = [
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm',
        '.m4v', '.3gp', '.ogv', '.ts', '.mts', '.m2ts', '.vob', '.asf'
    ]
    
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in video_extensions:
        return False, f"Unsupported video format: {file_ext}"
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "File is empty"
    
    return True, ""


def validate_audio_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate if a file is a valid audio file.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"Path is not a file: {file_path}"
    
    # Check file extension
    audio_extensions = [
        '.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac', '.wma',
        '.opus', '.aiff', '.au', '.ra', '.amr', '.ac3', '.dts'
    ]
    
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in audio_extensions:
        return False, f"Unsupported audio format: {file_ext}"
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "File is empty"
    
    return True, ""


def get_file_info(file_path: str) -> dict:
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        return {"error": "File does not exist"}
    
    stat = os.stat(file_path)
    path_obj = Path(file_path)
    
    return {
        "name": path_obj.name,
        "stem": path_obj.stem,
        "suffix": path_obj.suffix,
        "size": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified": stat.st_mtime,
        "is_file": os.path.isfile(file_path),
        "is_dir": os.path.isdir(file_path)
    }


def ensure_directory(directory_path: str) -> bool:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_safe_filename(filename: str) -> str:
    """
    Get a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    safe_filename = filename
    
    for char in invalid_chars:
        safe_filename = safe_filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    safe_filename = safe_filename.strip(' .')
    
    # Ensure it's not empty
    if not safe_filename:
        safe_filename = "unnamed_file"
    
    return safe_filename
