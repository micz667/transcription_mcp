# YouTube Video Downloader with Subtitle Extraction

This tool extends the transcription pipeline with YouTube video downloading capabilities, including automatic subtitle extraction and conversion to markdown format.

## Features

- **Video Download**: Download YouTube videos in various formats
- **Subtitle Extraction**: Extract both manual and auto-generated subtitles
- **Multiple Languages**: Support for multiple subtitle languages
- **Format Conversion**: Convert SRT/VTT subtitles to markdown
- **Integration**: Works with the existing transcription pipeline
- **Batch Processing**: Download multiple videos at once

## Installation

Make sure you have the required dependencies:

```bash
pip install yt-dlp
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Basic Usage

```bash
# Download video with subtitles
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Download to specific directory
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir ./my_videos

# Download with specific languages
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --languages en pl es
```

#### Advanced Options

```bash
# Download only subtitles (no video)
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --subtitles-only

# Convert subtitles to markdown
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --convert-to-markdown

# Include timestamps in markdown
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --convert-to-markdown --include-timestamps

# Also transcribe with Whisper
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --transcribe --model whisper-large

# Custom output name
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-name "my_video"
```

### Python API

```python
from transcribe.extractors.youtube_extractor import YouTubeExtractor

# Initialize extractor
extractor = YouTubeExtractor()

# Get video information
video_info = extractor.get_video_info("https://www.youtube.com/watch?v=VIDEO_ID")
print(f"Title: {video_info['title']}")
print(f"Available subtitles: {video_info['available_subtitles']}")

# Download video and subtitles
results = extractor.download_video_with_subtitles(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir="./downloads",
    include_auto_subtitles=True,
    include_manual_subtitles=True,
    preferred_languages=['en', 'pl']
)

# Convert subtitles to markdown
for subtitle_file in results['subtitle_files']:
    extractor.convert_subtitle_to_markdown(
        subtitle_file=subtitle_file,
        output_file=f"{subtitle_file}.md",
        include_timestamps=True
    )
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `url` | YouTube video URL (required) |
| `--output-dir`, `-o` | Output directory (default: ./downloads) |
| `--output-name` | Custom name for output files |
| `--languages`, `-l` | Preferred subtitle languages (default: en) |
| `--no-auto-subtitles` | Skip auto-generated subtitles |
| `--no-manual-subtitles` | Skip manual subtitles |
| `--subtitles-only` | Download only subtitles, not video |
| `--transcribe` | Also transcribe with Whisper |
| `--model`, `-m` | Whisper model (base/small/medium/large) |
| `--language` | Language for transcription |
| `--convert-to-markdown` | Convert subtitles to markdown |
| `--include-timestamps` | Include timestamps in markdown |

## Supported Subtitle Formats

- **SRT** (SubRip Subtitle)
- **VTT** (WebVTT)
- **ASS/SSA** (Advanced SubStation Alpha)

## Output Files

The downloader creates the following files:

```
downloads/
├── video_title.mp4          # Downloaded video
├── video_title.en.srt       # English subtitles
├── video_title.pl.vtt       # Polish subtitles
├── video_title_subtitles.md # Converted markdown
└── video_title_transcript.md # Whisper transcription (if --transcribe)
```

## Integration with Transcription Pipeline

The YouTube downloader integrates seamlessly with the existing transcription pipeline:

```python
from transcribe import TranscribePipeline
from transcribe.extractors.youtube_extractor import YouTubeExtractor

# Download video
extractor = YouTubeExtractor()
results = extractor.download_video_with_subtitles(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir="./downloads"
)

# Transcribe with existing pipeline
pipeline = TranscribePipeline()
result = pipeline.process(
    input_path=results['video_file'],
    output_path="./transcript.md"
)
```

## Examples

### Example 1: Download with Subtitles

```bash
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
    --output-dir ./rick_roll \
    --languages en \
    --convert-to-markdown \
    --include-timestamps
```

### Example 2: Subtitles Only

```bash
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
    --subtitles-only \
    --languages en pl es \
    --convert-to-markdown
```

### Example 3: Full Processing

```bash
python examples/youtube_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
    --transcribe \
    --model whisper-large \
    --convert-to-markdown \
    --output-name "my_video"
```

## Troubleshooting

### Common Issues

1. **yt-dlp not found**
   ```bash
   pip install yt-dlp
   ```

2. **No subtitles available**
   - Check if the video has subtitles: `--languages en pl es`
   - Try auto-generated subtitles: remove `--no-auto-subtitles`

3. **Download fails**
   - Check if the URL is correct
   - Try updating yt-dlp: `pip install --upgrade yt-dlp`

4. **Permission errors**
   - Make sure you have write permissions to the output directory
   - Try a different output directory

### Debug Mode

For detailed logging, you can modify the script to enable debug mode:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Limitations

- YouTube's terms of service apply
- Some videos may not have subtitles available
- Download speed depends on your internet connection
- Large videos may take significant time to download

## Legal Notice

Please respect YouTube's terms of service and copyright laws. Only download videos you have permission to download, such as:
- Your own videos
- Videos with appropriate licenses
- Videos for educational purposes (check local laws)

## Future Enhancements

- [ ] Playlist download support
- [ ] Batch download from text file
- [ ] Subtitle quality assessment
- [ ] Automatic language detection
- [ ] Integration with cloud storage
- [ ] Web interface for easier use
