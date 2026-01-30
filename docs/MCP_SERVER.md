# MCP Server for Transcription Tool

This project includes an **MCP (Model Context Protocol) server** written in **Python** using the official MCP Python SDK (FastMCP). It exposes transcription by **path**: the user (or LLM) provides a path to an audio/video file; the LLM calls a tool to create a transcription, then reads through it with another tool. The server uses the existing Python pipeline directly (no subprocess, single runtime).

## Why Python?

The transcription pipeline (Whisper, FFmpeg, etc.) is already in Python. Running the MCP server in Python keeps one runtime, avoids spawning subprocesses, and makes the server a thin wrapper over the pipeline—ideal for a small set of tools (transcribe, read, get formats).

## What is MCP?

MCP allows AI assistants to use external tools and resources over a standard protocol. This server lets assistants:

- **Transcribe** an audio/video file by path (runs the existing Python pipeline with Whisper).
- **Read** a transcription file by path (so the LLM can read through the transcript).
- **List** supported formats and options.

## Available Tools

### 1. `transcribe_file`

Transcribe a single audio or video file to markdown.

**Parameters:**

- `input_path` (required): Path to input audio/video file (absolute or relative to cwd).
- `output_path` (optional): Path for output markdown file. If omitted, output is written next to the input with the same name and `.md` extension.
- `language` (optional): `auto` (default) to detect spoken language, or ISO 639-1 code (e.g. `en`, `pl`, `de`) when the user explicitly requests a language.
- `model` (optional): `whisper-base` | `whisper-small` | `whisper-medium` | `whisper-large`. Default: `whisper-medium`.

**Returns:** JSON with `success`, `output_path`, and status. On success, the transcription runs in a separate terminal; the agent must **stop** and not call `read_transcription` in the same turn. The user should watch the terminal and later ask the agent to read the transcript when it's done.

### 2. `read_transcription`

Read the content of a transcription file (e.g. the `.md` file produced by `transcribe_file`).

**Parameters:**

- `path` (required): Path to the transcription file.

**Returns:** The file content (markdown text). Call this **only when the user asks** to read the transcript, and **only after** the transcription process has finished. Do not call this in the same turn as `transcribe_file`—the file is not ready until the process in the terminal finishes.

### 3. `get_supported_formats`

Returns supported audio/video formats and transcription options (models, languages). No parameters.

## Setup

### 1. Python environment

From the project root (this repo):

```bash
python3 -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Ensure the transcribe package is installed (e.g. `pip install -e .` or the project is on `PYTHONPATH` when you run the server).

### 2. Run the MCP server

```bash
python mcp_server.py
```

The server uses **stdio** transport by default (reads from stdin, writes to stdout). MCP clients (Cursor, Claude Desktop, etc.) spawn this process and communicate over stdio.

### 3. Configure MCP client (e.g. Cursor)

Add the server to your MCP config. Example for Cursor (project root = transcribe repo):

```json
{
  "mcpServers": {
    "transcription": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/transcribe",
      "env": {
        "PYTHONPATH": "/path/to/transcribe"
      }
    }
  }
}
```

- **command**: `python` or `python3` (or full path to your venv Python: `venv/bin/python`).
- **args**: `["mcp_server.py"]`.
- **cwd**: Must be the **transcribe repo root** so that `transcribe` is importable and paths resolve correctly.
- **env**: Set `PYTHONPATH` to the repo root if the transcribe package is not installed in the environment.

Using a venv:

```json
{
  "mcpServers": {
    "transcription": {
      "command": "/path/to/transcribe/venv/bin/python",
      "args": ["/path/to/transcribe/mcp_server.py"],
      "cwd": "/path/to/transcribe"
    }
  }
}
```

## Usage flow

1. User asks the assistant to transcribe a file (e.g. “Transcribe `/path/to/meeting.m4a`”).
2. Assistant calls **`transcribe_file`** with `input_path: "/path/to/meeting.m4a"` (and optional `output_path`, `language`, `model`).
3. Server launches the Python pipeline in a new terminal and returns immediately with `output_path` (e.g. `/path/to/meeting.md`). **Assistant must stop here**—do not call `read_transcription` in the same turn. Tell the user transcription has started and they should watch the terminal; when it finishes, they can ask to read the transcript.
4. Later, when the user asks to read the transcript (e.g. "read it", "show the transcript"), the assistant calls **`read_transcription`** with `path: "/path/to/meeting.md"` to read the transcript.
5. Assistant uses the transcript content in the conversation (summarize, answer questions, etc.).

## Supported formats

Same as the Python pipeline: see main README. Summary:

- **Video:** MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V, 3GP, OGV, TS, MTS, M2TS, VOB, ASF.
- **Audio:** WAV, MP3, FLAC, M4A, OGG, AAC, WMA, OPUS, AIFF, AU, RA, AMR, AC3, DTS.

## Troubleshooting

- **“No module named 'transcribe'”:** Run the server with `cwd` set to the repo root and `PYTHONPATH` set to the repo root, or install the package: `pip install -e .` from the repo.
- **“Input file not found”:** Paths are resolved against the current working directory (cwd) of the server process. Use absolute paths or paths relative to the repo root. Set `cwd` in the MCP config to the repo root.
- **FFmpeg / Whisper errors:** Same as the standalone Python tool; see main README (FFmpeg, Whisper, dependencies).

## Development

```bash
# Run server (stdio)
python mcp_server.py

# With MCP Inspector (test tools)
uv run --with mcp mcp_server.py
# or: npx @modelcontextprotocol/inspector (then connect to your server)
```

