"""
Command Line Interface for Movie Audio Transcription Tool.
"""

import argparse
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        Progress,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from ..core.pipeline import TranscribePipeline
from ..core.types import ProcessingConfig, ProcessingStatus, TranscriptionModel, AudioFormat


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(description='Movie Audio Transcription Tool')
    
    # Input/output arguments
    parser.add_argument('--input', '-i', help='Input video file path')
    parser.add_argument('--output', '-o', help='Output markdown file path')
    parser.add_argument('--input-dir', help='Input directory containing video files')
    parser.add_argument('--output-dir', help='Output directory for markdown files')
    
    # Processing configuration
    parser.add_argument('--language', '-l', default='auto', help='Language code or "auto" to detect (default: auto)')
    parser.add_argument('--model', '-m', default='whisper-medium', 
                       choices=['whisper-base', 'whisper-small', 'whisper-medium', 'whisper-large'],
                       help='Transcription model (default: whisper-medium)')
    parser.add_argument('--audio-format', default='wav', 
                       choices=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
                       help='Audio format for extraction (default: wav)')
    parser.add_argument('--sample-rate', type=int, default=16000, help='Audio sample rate (default: 16000)')
    parser.add_argument('--chunk-duration', type=float, default=30.0, help='Audio chunk duration in seconds (default: 30)')
    
    # Output options
    parser.add_argument('--no-timestamps', action='store_true', help='Exclude timestamps from output')
    parser.add_argument('--no-confidence', action='store_true', help='Exclude confidence scores from output')
    parser.add_argument('--template', default='default', 
                       choices=['default', 'minimal', 'detailed', 'timeline'],
                       help='Markdown template (default: default)')
    
    # Processing options
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum number of workers (default: 4)')
    parser.add_argument('--timeout', type=float, default=300.0, help='Processing timeout in seconds (default: 300)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.input and not args.input_dir:
        parser.error("Either --input or --input-dir must be specified")
    
    if args.input and not args.output:
        parser.error("--output must be specified when using --input")
    
    if args.input_dir and not args.output_dir:
        parser.error("--output-dir must be specified when using --input-dir")
    
    # Create configuration
    config = ProcessingConfig(
        language=args.language,
        model=TranscriptionModel(args.model),
        audio_format=AudioFormat(args.audio_format),
        sample_rate=args.sample_rate,
        chunk_duration=args.chunk_duration,
        include_timestamps=not args.no_timestamps,
        include_confidence=not args.no_confidence,
        max_workers=args.max_workers,
        timeout=args.timeout
    )
    # Add template to config
    if not hasattr(config, 'config'):
        config.config = {}
    config.config['template'] = args.template
    
    # Create pipeline
    pipeline = TranscribePipeline(config)

    def make_progress_callback(progress: "Progress", task_id: int):
        def progress_callback(msg: str, step: float, total: float) -> None:
            progress.update(task_id, completed=step, total=total, description=msg)
        return progress_callback

    def run_single_file():
        if RICH_AVAILABLE:
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=32, complete_style="dim green", finished_style="green"),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                expand=False,
            ) as progress:
                task = progress.add_task("Starting…", total=4.0, completed=0)
                cb = make_progress_callback(progress, task)
                return pipeline.process(args.input, args.output, config, progress_callback=cb)
        else:
            def simple_cb(msg: str, step: float, total: float) -> None:
                pct = int(100 * step / total) if total else 0
                print(f"  [{pct:3d}%] {msg}", flush=True)
            return pipeline.process(args.input, args.output, config, progress_callback=simple_cb)

    try:
        if args.input:
            if RICH_AVAILABLE and Console:
                Console().print(f"\n[bold]Processing:[/bold] {args.input}\n")
            else:
                print(f"Processing: {args.input}", flush=True)
            result = run_single_file()

            if result.status == ProcessingStatus.COMPLETED:
                if RICH_AVAILABLE and Console:
                    Console().print(f"\n[bold green]✅[/bold green] Transcription completed: {args.output}")
                else:
                    print(f"✅ Transcription completed: {args.output}")
            else:
                if RICH_AVAILABLE and Console:
                    Console().print(f"\n[bold red]❌[/bold red] Transcription failed: {result.errors}")
                else:
                    print(f"❌ Transcription failed: {result.errors}")
                sys.exit(1)
        
        elif args.input_dir:
            # Process batch
            input_dir = Path(args.input_dir)
            video_files = []
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm']:
                video_files.extend(input_dir.glob(ext))
            if not video_files:
                print(f"No video files found in {args.input_dir}")
                sys.exit(1)
            paths = [str(f) for f in video_files]
            n_files = len(paths)

            if RICH_AVAILABLE:
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(bar_width=28, complete_style="dim green", finished_style="green"),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    expand=False,
                ) as progress:
                    file_task = progress.add_task("Files", total=n_files, completed=0)
                    step_task = progress.add_task("  …", total=4.0, completed=0)
                    for i, input_path in enumerate(paths):
                        progress.update(file_task, description=f"File {i + 1}/{n_files}", completed=i)
                        progress.update(step_task, description="  Starting…", completed=0)

                        def batch_step_cb(msg: str, step: float, total: float) -> None:
                            progress.update(step_task, completed=step, total=total, description=f"  {msg}")

                        pipeline.process(
                            input_path,
                            str(Path(args.output_dir) / f"{Path(input_path).stem}.md"),
                            config,
                            progress_callback=batch_step_cb,
                        )
                        progress.update(step_task, completed=4.0, description="  Done")
                        progress.update(file_task, completed=i + 1)
                results = pipeline.completed_documents + pipeline.failed_documents
            else:
                def simple_cb(msg: str, step: float, total: float) -> None:
                    pct = int(100 * step / total) if total else 0
                    print(f"  [{pct:3d}%] {msg}", flush=True)
                results = pipeline.process_batch(paths, args.output_dir, config, progress_callback=simple_cb)

            completed = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
            failed = len(results) - completed
            if RICH_AVAILABLE and Console:
                Console().print(f"\n✅ Batch: {completed} done, {failed} failed")
            else:
                print(f"✅ Batch processing completed: {completed} successful, {failed} failed")
            
            if failed > 0:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")
        sys.exit(1)
    
    finally:
        pipeline.cleanup()


if __name__ == '__main__':
    main()
