# Movie Audio Transcription Tool

A modular system for extracting audio from movies and transcribing it to markdown files.

## Features

- **Audio Extraction**: Extract audio from various video formats (MP4, AVI, MOV, etc.)
- **Direct Audio Processing**: Process audio files directly (WAV, MP3, FLAC, M4A, etc.)
- **YouTube Integration**: Download YouTube videos and extract their subtitles
- **Subtitle Conversion**: Convert SRT/VTT subtitles to markdown format
- **Transcription**: Convert speech to text using advanced speech recognition
- **Markdown Output**: Generate well-formatted markdown files with timestamps
- **Modular Design**: Each component handles a specific responsibility
- **Error Handling**: Comprehensive error handling with informative feedback
- **Batch Processing**: Process multiple files efficiently
- **Automatic Format Detection**: Automatically detects video vs audio files

## MCP Server (path-based transcription)

A **Python MCP server** exposes transcription by path for AI assistants (single runtime, no subprocess):

- **`transcribe_file`**: Path to an audio/video file → creates a markdown transcription (runs the existing Python pipeline).
- **`read_transcription`**: Path to a transcription file → returns its content (so the LLM can read through the transcript).
- **`get_supported_formats`**: Returns supported formats and options.

See **[docs/MCP_SERVER.md](docs/MCP_SERVER.md)** for setup, tools, and Cursor/MCP client config.

```bash
pip install -r requirements.txt
python mcp_server.py   # Start MCP server (stdio)
```

## Project Structure

```
transcribe/
├── mcp_server.py        # MCP server (Python, FastMCP, stdio)
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies (includes mcp)
├── setup.py             # Package setup
├── scripts/
│   └── init_project.sh  # One-time setup (venv, pip install)
├── transcribe/          # Python package
│   ├── core/            # Core interfaces, types, and pipeline
│   ├── extractors/      # Audio extraction modules
│   ├── transcribers/    # Speech-to-text modules
│   ├── formatters/      # Output formatting modules
│   ├── utils/           # Utility functions
│   ├── cli/             # Command line interface
│   └── config.json      # Default configuration
├── tests/               # Test files
├── docs/                # Documentation
├── examples/            # Example scripts
├── input/               # Input audio/video (optional)
├── output/              # Generated transcripts (optional)
└── downloads/           # Downloaded media (optional)
```

## Installation

### Prerequisites

1. **Python 3.8+** - Make sure you have Python installed
2. **FFmpeg** - Required for audio extraction

### Quick Setup

**macOS/Linux:**
```bash
# Make the script executable
chmod +x scripts/init_project.sh

# Run the initialization script (from repo root)
./scripts/init_project.sh
```

**Windows:** Create a venv and install manually:
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate.bat
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg:**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

4. **Verify installation:**
   ```bash
   python main.py --help
   ```

## Usage

### Basic Usage

```python
from transcribe import TranscribePipeline

# Create pipeline
pipeline = TranscribePipeline()

# Process a single file
result = pipeline.process("path/to/movie.mp4", "output.md")

# Process multiple files
results = pipeline.process_batch([
    "movie1.mp4",
    "movie2.avi"
], "output_directory/")
```

### Command Line Interface

```bash
# Transcribe a video file
python main.py --input movie.mp4 --output transcript.md

# Transcribe an audio file
python main.py --input recording.wav --output transcript.md

# Process multiple files (video and audio)
python main.py --input-dir ./recordings/ --output-dir ./transcripts/

# With custom settings
python main.py --input recording.mp3 --output transcript.md --language en --model large
```

### YouTube Video Downloader

```bash
# Download YouTube video with subtitles
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Download with subtitle conversion to markdown
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --convert-to-markdown

# Download and transcribe with Whisper
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --transcribe

# Download subtitles only
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --subtitles-only
```

## Configuration

The system uses a modular configuration approach:

- **Audio Extraction**: Configurable quality, format, and chunk size
- **Transcription**: Multiple speech recognition engines (Whisper, Google Speech, etc.)
- **Output Format**: Customizable markdown templates and formatting options

## Architecture

This project follows a modular design with clear separation of concerns:

1. **Document Interface**: All data flows through a consistent document format
2. **Modular Components**: Each tool handles one specific responsibility
3. **Error Handling**: Comprehensive error handling with informative feedback
4. **State Management**: Tracks processing context and progress
5. **Flexible Memory**: Supports both short-term and long-term storage

## Contributing

1. Follow the modular architecture principles
2. Implement proper error handling
3. Add comprehensive tests
4. Update documentation

## License

MIT License 