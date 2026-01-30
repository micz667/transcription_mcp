# Quick Start Guide

Get up and running with the Movie Audio Transcription Tool in minutes!

## Prerequisites

1. **Python 3.8+** - Make sure you have Python installed
2. **FFmpeg** - Required for audio extraction

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd transcribe
   ```

2. **Set up Python environment:**
   ```bash
   # macOS/Linux
   chmod +x scripts/init_project.sh
   ./scripts/init_project.sh
   
   # Windows
   python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
   ```

3. **Activate virtual environment:**
   ```bash
   # macOS/Linux
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate.bat
   ```

4. **Verify installation:**
   ```bash
   python main.py --help
   ```

## Quick Examples

### Transcribe a single video file

```bash
python main.py --input movie.mp4 --output transcript.md
```

### Transcribe with custom settings

```bash
python main.py \
  --input movie.mp4 \
  --output transcript.md \
  --language en \
  --model whisper-medium \
  --template detailed
```

### Process multiple files

```bash
python main.py \
  --input-dir ./videos/ \
  --output-dir ./transcripts/ \
  --language en \
  --model whisper-large
```

### Minimal output (no timestamps)

```bash
python main.py \
  --input movie.mp4 \
  --output transcript.md \
  --no-timestamps \
  --no-confidence \
  --template minimal
```

## Python API Usage

```python
from src.main import TranscribePipeline
from src.core.types import ProcessingConfig

# Create configuration
config = ProcessingConfig(
    language="en",
    model="whisper-medium",
    include_timestamps=True,
    include_confidence=True
)

# Create pipeline
pipeline = TranscribePipeline(config)

# Process video
result = pipeline.process("movie.mp4", "transcript.md", config)

if result.status.value == "completed":
    print("✅ Transcription completed!")
    print(f"📄 Output: {result.output_path}")
    print(f"⏱️  Time: {result.processing_time:.2f}s")
    print(f"📊 Segments: {len(result.transcription_segments)}")
else:
    print(f"❌ Failed: {result.errors}")
```

## Configuration Options

### Audio Extraction
- `--audio-format`: Output audio format (wav, mp3, flac, m4a, ogg)
- `--sample-rate`: Audio sample rate (default: 16000)
- `--chunk-duration`: Audio chunk duration in seconds (default: 30)

### Transcription
- `--language`: Language code (default: en)
- `--model`: Whisper model size (base, small, medium, large)
- `--task`: Task type (transcribe or translate)

### Output Formatting
- `--template`: Markdown template (default, minimal, detailed, timeline)
- `--no-timestamps`: Exclude timestamps from output
- `--no-confidence`: Exclude confidence scores from output

### Processing
- `--max-workers`: Maximum number of workers (default: 4)
- `--timeout`: Processing timeout in seconds (default: 300)

## Supported Video Formats

- MP4, AVI, MOV, MKV, WMV, FLV, WebM
- M4V, 3GP, OGV, TS, MTS, M2TS
- VOB, ASF

## Troubleshooting

### Common Issues

1. **FFmpeg not found:**
   ```bash
   # Check if FFmpeg is installed
   ffmpeg -version
   
   # If not found, install it (see Prerequisites)
   ```

2. **CUDA/GPU issues:**
   ```bash
   # Install CPU-only version
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

3. **Memory issues with large files:**
   ```bash
   # Use smaller model and chunk duration
   python main.py --input large_movie.mp4 --output transcript.md \
     --model whisper-small --chunk-duration 15
   ```

4. **Slow processing:**
   - Use smaller model (`whisper-base` or `whisper-small`)
   - Reduce chunk duration
   - Use GPU if available

### Getting Help

- Check the logs: `transcribe.log`
- Run with verbose output: Add `--verbose` flag
- Check file permissions and disk space
- Ensure video file is not corrupted

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples/](examples/) for more usage examples
- Explore the [src/](src/) directory to understand the architecture
- Customize templates and add new features

Happy transcribing! 🎬📝 