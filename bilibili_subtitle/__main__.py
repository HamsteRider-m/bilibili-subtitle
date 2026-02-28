"""
CLI entry point for bilibili-subtitle skill.

Usage:
    pixi run python -m bilibili_subtitle "BV1234567890"
    pixi run python -m bilibili_subtitle --check
    pixi run python -m bilibili_subtitle "URL" --skip-proofread --skip-summary
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import re

from .contract import ExitCode, ExecutionResult, SubtitleOutput
from .errors import (
    ASRConfigError,
    BBDownAuthError,
    BBDownDownloadError,
    FFmpegNotFoundError,
    InvalidURLError,
    NoSubtitleError,
    SkillError,
    VideoNotFoundError,
    exit_code_for_error,
)
from .preflight import run_preflight
from .url_parser import parse_bilibili_ref


_WINDOWS_ILLEGAL_RE = re.compile(r'[/\\:*?"<>|]')
_CONTROL_CHAR_RE = re.compile(r'[\x00-\x1f]')


def _sanitize_filename(name: str) -> str:
    """Remove Windows-illegal characters and control chars from a filename."""
    name = _CONTROL_CHAR_RE.sub("", name)
    name = _WINDOWS_ILLEGAL_RE.sub("_", name)
    name = name.strip().strip("_").strip()
    return name or "untitled"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bilibili_subtitle",
        description="Extract Bilibili subtitles with ASR fallback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "BV1234567890"
  %(prog)s "https://www.bilibili.com/video/BV1234567890"
  %(prog)s "BV1234567890" --skip-proofread --skip-summary
  %(prog)s --check
        """,
    )

    parser.add_argument("url", nargs="?", help="Bilibili URL or BV ID")
    parser.add_argument(
        "-o", "--output-dir", default="./output", help="Output directory"
    )
    parser.add_argument("--output-lang", choices=["zh", "en", "zh+en"], default="zh")
    parser.add_argument(
        "--skip-proofread", action="store_true", help="Skip AI proofreading"
    )
    parser.add_argument(
        "--skip-summary", action="store_true", help="Skip AI summarization"
    )
    parser.add_argument("--cache-dir", default="./.cache", help="Cache directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--check", action="store_true", help="Run preflight checks")
    parser.add_argument("--check-json", action="store_true", help="Preflight as JSON")
    parser.add_argument(
        "--skip-auth-check", action="store_true", help="Skip auth check"
    )
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")
    return parser


def run_extraction(
    url: str,
    output_dir: Path,
    *,
    output_lang: str = "zh",
    skip_proofread: bool = False,
    skip_summary: bool = False,
    cache_dir: Path = Path("./.cache"),
    verbose: bool = False,
) -> ExecutionResult:
    warnings: list[str] = []
    errors: list[dict] = []

    try:
        ref = parse_bilibili_ref(url)
        video_id = ref.video_id or "unknown"
        canonical_url = ref.canonical_url or ref.input_value
    except Exception:
        raise InvalidURLError(url)

    cache_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    from .bbdown_client import BBDownClient
    from .segment import Segment
    from .subtitle_loader import load_segments_from_subtitle_file, check_title_relevance

    client = BBDownClient()

    if verbose:
        print(f"[INFO] Processing: {video_id}")
        print(f"[INFO] Output directory: {output_dir}")

    try:
        info = client.get_video_info(canonical_url, cache_dir)
    except Exception as e:
        if "login" in str(e).lower() or "auth" in str(e).lower():
            raise BBDownAuthError(str(e))
        if "not found" in str(e).lower() or "不存在" in str(e).lower():
            raise VideoNotFoundError(video_id or "unknown")
        raise BBDownDownloadError(canonical_url, str(e))

    if verbose:
        print(f"[INFO] Title: {info.title}")
        print(f"[INFO] Has subtitle: {info.subtitle_info.has_subtitle}")

    segments: list[Segment] = []

    if info.subtitle_files:
        max_crosstalk_retries = 2
        for attempt in range(max_crosstalk_retries + 1):
            sub_file = info.subtitle_files[0]
            if verbose:
                print(f"[INFO] Loading subtitle: {sub_file.name}")
            load_result = load_segments_from_subtitle_file(sub_file, title=info.title)
            segments = load_result.segments

            if load_result.relevant:
                break

            # Crosstalk detected — subtitle may belong to a different video
            if attempt < max_crosstalk_retries:
                warnings.append(
                    f"Crosstalk suspected (attempt {attempt + 1}), re-downloading..."
                )
                if verbose:
                    print(f"[WARN] Subtitle may not match title, retrying ({attempt + 1}/{max_crosstalk_retries})")
                # Delete stale file and re-fetch
                sub_file.unlink(missing_ok=True)
                try:
                    info = client.get_video_info(canonical_url, cache_dir)
                except Exception:
                    break  # Can't retry, use what we have
                if not info.subtitle_files:
                    break
            else:
                warnings.append(
                    "Subtitle content may not match video title (crosstalk); proceeding anyway"
                )
    elif not info.subtitle_info.has_subtitle:
        warnings.append("No subtitles found, attempting ASR transcription")

        import shutil

        if not shutil.which("ffmpeg"):
            raise FFmpegNotFoundError()

        from .audio_extractor import extract_audio
        from .agents.transcribe_agent import TranscribeAgent

        try:
            audio_path = extract_audio(canonical_url, cache_dir)
            if verbose:
                print(f"[INFO] Audio extracted: {audio_path}")

            transcriber = TranscribeAgent(mode="qwen")
            result = transcriber.transcribe(str(audio_path))
            segments = result.segments

            if audio_path.exists():
                audio_path.unlink()
        except Exception as e:
            if "DASHSCOPE_API_KEY" in str(e):
                raise ASRConfigError()
            raise

    if not segments:
        raise NoSubtitleError(video_id)

    if not skip_proofread:
        import os

        if not os.environ.get("ANTHROPIC_API_KEY"):
            warnings.append("ANTHROPIC_API_KEY not set, skipping proofreading")
        else:
            if verbose:
                print("[INFO] Proofreading...")
            from .agents.proofread_agent import ProofreadAgent

            proofer = ProofreadAgent()
            try:
                segments = proofer.proofread_segments(segments)
            except Exception as e:
                warnings.append(f"Proofreading failed: {e}")

    from .renderers.srt import render_srt
    from .renderers.vtt import render_vtt
    from .renderers.markdown import render_transcript_markdown

    srt_content = render_srt(segments)
    vtt_content = render_vtt(segments)
    md_content = render_transcript_markdown(segments, title=info.title)

    lang_suffix = "" if output_lang == "zh" else f".{output_lang}"
    safe_title = _sanitize_filename(info.title or video_id)
    srt_path = output_dir / f"{safe_title}{lang_suffix}.srt"
    vtt_path = output_dir / f"{safe_title}{lang_suffix}.vtt"
    md_path = output_dir / f"{safe_title}.transcript.md"

    srt_path.write_text(srt_content, encoding="utf-8")
    vtt_path.write_text(vtt_content, encoding="utf-8")
    md_path.write_text(md_content, encoding="utf-8")

    if verbose:
        print(f"[INFO] Generated: {srt_path.name}")
        print(f"[INFO] Generated: {md_path.name}")

    summary_json_path = None
    summary_md_path = None

    if not skip_summary:
        import os

        if not os.environ.get("ANTHROPIC_API_KEY"):
            warnings.append("ANTHROPIC_API_KEY not set, skipping summarization")
        else:
            if verbose:
                print("[INFO] Summarizing...")
            from .agents.summarize_agent import SummarizeAgent

            summarizer = SummarizeAgent()
            try:
                result = summarizer.summarize(segments, title=info.title)
                summary_json_path = output_dir / f"{safe_title}.summary.json"
                summary_md_path = output_dir / f"{safe_title}.summary.md"
                summary_json_path.write_text(
                    json.dumps(result.summary, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                summary_md_path.write_text(result.raw_text or "", encoding="utf-8")
            except Exception as e:
                warnings.append(f"Summarization failed: {e}")

    output = SubtitleOutput(
        video_id=video_id,
        title=info.title,
        transcript_md=md_path,
        srt_file=srt_path,
        vtt_file=vtt_path,
        summary_json=summary_json_path,
        summary_md=summary_md_path,
    )

    return ExecutionResult(
        exit_code=ExitCode.SUCCESS if not errors else ExitCode.PARTIAL_SUCCESS,
        output=output,
        errors=errors,
        warnings=warnings,
        metadata={"url": canonical_url},
    )


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.check or args.check_json:
        report = run_preflight(include_auth=not args.skip_auth_check)
        if args.check_json:
            print(report.to_json())
        else:
            report.print_report()
        return 0 if report.can_proceed else 1

    if not args.url:
        parser.error("URL is required (unless using --check)")

    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)

    try:
        result = run_extraction(
            args.url,
            output_dir,
            output_lang=args.output_lang,
            skip_proofread=args.skip_proofread,
            skip_summary=args.skip_summary,
            cache_dir=cache_dir,
            verbose=args.verbose,
        )

        if args.json_output:
            print(result.to_json())
        else:
            if result.output:
                print(
                    f"✅ {result.output.video_id}: {result.output.title or 'No title'}"
                )
                if result.output.transcript_md:
                    print(f"   Transcript: {result.output.transcript_md}")
            for w in result.warnings:
                print(f"⚠️  {w}")

        return result.exit_code.value

    except SkillError as e:
        if args.json_output:
            print(
                json.dumps(
                    {
                        "exit_code": exit_code_for_error(e),
                        "error": e.to_json(),
                    },
                    indent=2,
                )
            )
        else:
            print(str(e), file=sys.stderr)
        return exit_code_for_error(e)

    except Exception as e:
        if args.json_output:
            print(
                json.dumps(
                    {
                        "exit_code": 1,
                        "error": {"code": "E999", "message": str(e)},
                    },
                    indent=2,
                )
            )
        else:
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
