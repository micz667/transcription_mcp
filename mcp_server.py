#!/usr/bin/env python3
"""
MCP Transcribe Server – starts transcription in the background and returns immediately.

Flow: User asks for transcription → agent asks for file name → user gives path →
agent calls transcribe_file → tool launches CLI in a new terminal (progress there)
and returns right away with success and the path to the .md file. Agent replies
to the user with that path; transcription keeps running in the other window.
Output is saved under transcriptions/ by default (new name = input stem + .md).
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Project root = directory containing this file (mcp_server.py)
PROJECT_ROOT = Path(__file__).resolve().parent
# Default directory for transcription outputs (user-visible path)
TRANSCRIPTIONS_DIR = PROJECT_ROOT / "transcriptions"

mcp = FastMCP(
    "mcp-transcribe",
    instructions="""
MCP Transcribe Server – starts transcription in the background and returns immediately.

Flow:
1) User asks for transcription → you ask for the file name/path.
2) User gives the file name → you call transcribe_file with that path.
3) transcribe_file starts the job in a separate terminal (progress shown there)
   and returns immediately with success and the path where the .md will be saved.
4) You reply to the user right away: success and path to the .md file. The tool
   keeps running in the other window; do not wait or call read_transcription yet.
5) When the user later asks to read the transcript, call read_transcription with
   that path (only after they indicate the process has finished, or they ask to read it).

Available tools:
- transcribe_file: Start transcribing an audio/video file. Saves output to the
  transcriptions folder with a new name (input stem + .md). Launches progress in
  a new terminal; returns immediately with success and output_path (the .md path).
  Optionally: output_path, language, model.
- read_transcription: Read the content of a transcription file (.md). Use when the
  user asks to read the transcript (after the background job has finished).
- get_supported_formats: Returns supported audio/video formats and options.

Language: default "auto" (detect). Use a code (e.g. "pl", "en") only when the user
explicitly requests a language.
""".strip(),
)


def _shell_quote(s: str) -> str:
    """Quote a string for safe use in a shell command."""
    return json.dumps(s)


def _resolve_path(path: str, base_dir: str | None = None) -> str:
    base = base_dir or os.getcwd()
    p = Path(path).expanduser().resolve()
    if not p.is_absolute():
        p = (Path(base) / p).resolve()
    return str(p)


def _launch_in_terminal(
    project_root: Path,
    python_exe: str,
    input_path: str,
    output_path: str,
    language: str,
    model: str,
) -> tuple[bool, str]:
    """
    Launch the transcribe CLI in a new terminal window. Returns (success, message).
    """
    cmd_args = [
        python_exe,
        "-m",
        "transcribe.cli.main",
        "--input", input_path,
        "--output", output_path,
        "--language", language,
        "--model", model,
    ]
    project_root_str = str(project_root)
    system = platform.system()

    if system == "Darwin":
        # macOS: create a .command file and open it in Terminal.app
        # Quote each arg for safe shell execution
        cmd_shell = " ".join(_shell_quote(a) for a in cmd_args)
        script_lines = [
            "#!/bin/bash",
            f"cd {_shell_quote(project_root_str)}",
            "echo 'Transcribing... (progress below)'",
            "echo ''",
            cmd_shell,
            "echo ''",
            "echo 'Done. Press Enter to close this window.'",
            "read",
        ]
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".command",
            delete=False,
            newline="\n",
        ) as f:
            f.write("\n".join(script_lines))
            script_path = f.name
        try:
            os.chmod(script_path, 0o755)
            subprocess.Popen(
                ["open", "-a", "Terminal", script_path],
                start_new_session=True,
            )
            return True, "Transcription started in a new Terminal window. Stop here—do not call read_transcription now. The file is not ready until the process in that window finishes. Tell the user to watch the terminal and ask you to read the transcript when it's done."
        except Exception as e:
            return False, f"Failed to open Terminal: {e}"
        # Do not unlink script_path here; Terminal may not have read it yet.
        # Temp file will be cleaned by the OS.

    if system == "Windows":
        # Windows: start a new cmd window that runs the command and waits
        cmd_flat = " ".join(f'"{a}"' if " " in a else a for a in cmd_args)
        batch = f'cd /d {json.dumps(project_root_str)} && {cmd_flat} && echo. && pause'
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", batch],
                cwd=project_root_str,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                start_new_session=True,
            )
            return True, "Transcription started in a new console window. Stop here—do not call read_transcription now. The file is not ready until the process in that window finishes. Tell the user to watch the console and ask you to read the transcript when it's done."
        except Exception as e:
            return False, f"Failed to open console: {e}"

    # Linux and others: try gnome-terminal, then xterm, else run in background
    try:
        cmd_shell = " ".join(_shell_quote(a) for a in cmd_args)
        run_script = f"cd {_shell_quote(project_root_str)} && {cmd_shell} ; echo '' ; echo 'Press Enter to close.' ; read"
        if subprocess.run(["which", "gnome-terminal"], capture_output=True).returncode == 0:
            subprocess.Popen(
                ["gnome-terminal", "--", "bash", "-c", run_script],
                start_new_session=True,
            )
            return True, "Transcription started in a new terminal. Stop here—do not call read_transcription now. The file is not ready until the process in that window finishes. Tell the user to watch the terminal and ask you to read the transcript when it's done."
        if subprocess.run(["which", "xterm"], capture_output=True).returncode == 0:
            subprocess.Popen(
                ["xterm", "-e", f"bash -c {json.dumps(run_script)}"],
                start_new_session=True,
            )
            return True, "Transcription started in a new xterm. Stop here—do not call read_transcription now. The file is not ready until the process in that window finishes. Tell the user to watch the terminal and ask you to read the transcript when it's done."
    except Exception as e:
        pass
    # Fallback: run in background (no new window)
    try:
        subprocess.Popen(
            cmd_args,
            cwd=project_root_str,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True, "Transcription started in the background (no new window). Stop here—do not call read_transcription now. The file is not ready until the process finishes. Tell the user to ask you to read the transcript when it's done."
    except Exception as e:
        return False, str(e)


@mcp.tool()
def transcribe_file(
    input_path: str,
    output_path: str | None = None,
    language: str = "auto",
    model: str = "whisper-medium",
) -> str:
    """Start transcribing an audio or video file. Returns immediately with success and output path.

    Saves to the project transcriptions folder with a new name (input stem + .md)
    unless output_path is given. Launches progress in a new terminal; returns right
    away so the agent can respond with success and the .md path. Transcription runs
    in the background. Do not call read_transcription in the same turn.

    Language: "auto" (default) to detect; or ISO 639-1 (e.g. "en", "pl") if requested.
    """
    base = os.getcwd()
    resolved_input = _resolve_path(input_path, base)

    if not os.path.isfile(resolved_input):
        return json.dumps(
            {"success": False, "error": f"Input file not found: {resolved_input}"},
            indent=2,
        )

    if output_path is None:
        TRANSCRIPTIONS_DIR.mkdir(parents=True, exist_ok=True)
        stem = Path(resolved_input).stem
        output_path_resolved = str(TRANSCRIPTIONS_DIR / f"{stem}.md")
    else:
        output_path_resolved = _resolve_path(output_path, base)

    valid_models = ["whisper-base", "whisper-small", "whisper-medium", "whisper-large"]
    if model not in valid_models:
        model = "whisper-medium"

    python_exe = sys.executable
    success, message = _launch_in_terminal(
        PROJECT_ROOT,
        python_exe,
        resolved_input,
        output_path_resolved,
        language,
        model,
    )

    if not success:
        return json.dumps(
            {"success": False, "error": message, "output_path": output_path_resolved},
            indent=2,
        )

    return json.dumps(
        {
            "success": True,
            "output_path": output_path_resolved,
            "message": "Transcription started in the background. Output will be saved to the path above. Progress is shown in the other window. Tell the user they can ask you to read the transcript when it's done.",
        },
        indent=2,
    )


@mcp.tool()
def read_transcription(path: str) -> str:
    """Read the content of a transcription file (e.g. a .md file produced by the transcription tool).

    Call this only when the user asks to read the transcript, and only after
    the transcription process has finished (terminal window shows completion).
    Do not call this in the same turn as transcribe_file—the file is not ready yet.
    """
    resolved = _resolve_path(path, os.getcwd())
    if not os.path.isfile(resolved):
        return json.dumps({"error": f"File not found: {resolved}"}, indent=2)
    try:
        with open(resolved, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_supported_formats() -> str:
    """Returns supported audio/video formats and transcription options (models, languages)."""
    data = {
        "video_formats": [
            "mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v",
            "3gp", "ogv", "ts", "mts", "m2ts", "vob", "asf",
        ],
        "audio_formats": [
            "wav", "mp3", "flac", "m4a", "ogg", "aac", "wma", "opus",
            "aiff", "au", "ra", "amr", "ac3", "dts",
        ],
        "models": ["whisper-base", "whisper-small", "whisper-medium", "whisper-large"],
        "language": "Default: 'auto' (detect). Or ISO 639-1 code (e.g. en, pl, de).",
    }
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
