#!/bin/bash
# Movie Audio Transcription Tool - Project Initialization Script
# Run from anywhere; uses repo root (parent of scripts/).

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "🎬 Initializing Movie Audio Transcription Tool..."
echo "================================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if FFmpeg is installed
echo "🎵 Checking FFmpeg installation..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is installed"
    ffmpeg -version | head -n 1
else
    echo "⚠️  FFmpeg is not installed. Please install it:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "   Windows: Download from https://ffmpeg.org/download.html"
fi

# Run basic test
echo "🧪 Running basic tests..."
python tests/test_basic.py

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate:"
echo "  deactivate"
echo ""
echo "To run the transcription tool:"
echo "  python main.py --input video.mp4 --output transcript.md"
echo ""
echo "To run the MCP server:"
echo "  python mcp_server.py"
echo ""
echo "For more examples, see docs/QUICKSTART.md"
