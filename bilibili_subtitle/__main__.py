from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .agents.proofread_agent import ProofreadAgent
from .agents.summarize_agent import SummarizeAgent
from .agents.translate_agent import TranslateAgent
from .audio_extractor import extract_audio_with_ytdlp
from .cache import Cache
from .chunker import chunk_audio_ffmpeg
from .detector import extract_metadata, select_best_track
from .merger import ChunkTranscript, merge_chunk_transcripts
from .renderers.markdown import render_transcript_markdown
from .renderers.srt import render_srt
from .renderers.vtt import render_vtt
from .subtitle_downloader import download_best_subtitle
from .subtitle_loader import load_segments_from_subtitle_file


def _build_ydl_opts(args: argparse.Namespace) -> dict[str, Any]:
    opts: dict[str, Any] = {}
    if args.cookies_file:
        opts["cookiefile"] = args.cookies_file
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = args.cookies_from_browser
    return opts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bilibili-subtitle")
    parser.add_argument("url", help="Bilibili video URL, BV id, or av id")
    parser.add_argument("--output-dir", default="./output")
    parser.add_argument("--output-lang", default="zh", choices=["zh", "en", "zh+en"])
    parser.add_argument("--cookies-from-browser", dest="cookies_from_browser")
    parser.add_argument("--cookies-file", dest="cookies_file")
    parser.add_argument("--skip-proofread", action="store_true")
    parser.add_argument("--skip-summary", action="store_true")
    parser.add_argument("--cache-dir", default="./.cache")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache = Cache(args.cache_dir)

    ydl_opts = _build_ydl_opts(args)

    ref, meta = extract_metadata(args.url, ydl_opts=ydl_opts)
    best = select_best_track(meta.available_tracks)
    if args.verbose:
        print(json.dumps([t.__dict__ for t in meta.available_tracks], ensure_ascii=False, indent=2))

    video_id = meta.video_id or ref.video_id or "unknown"

    # Path A: subtitle extraction if any track exists.
    if best is not None:
        cached = cache.load_segments(video_id, "segments.zh")
        if cached is None:
            downloaded = download_best_subtitle(args.url, output_dir, ydl_opts=ydl_opts)
            segments = load_segments_from_subtitle_file(downloaded.file_path)
            cache.save_segments(video_id, "segments.zh", segments)
        else:
            segments = cached
    else:
        # Path B: audio transcription
        audio_path = extract_audio_with_ytdlp(args.url, output_dir, ydl_opts=ydl_opts)
        chunks = chunk_audio_ffmpeg(audio_path, output_dir / "chunks")

        from .agents.transcribe_agent import TranscribeAgent

        transcriber = TranscribeAgent()
        transcripts: list[ChunkTranscript] = []
        for chunk in chunks:
            result = transcriber.transcribe(str(chunk.path))
            transcripts.append(ChunkTranscript(chunk_start_ms=chunk.start_ms, segments=result.segments))
        segments = merge_chunk_transcripts(transcripts, overlap_ms=2000, similarity_threshold=0.8)
        cache.save_segments(video_id, "segments.zh", segments)

    # Proofread (zh)
    if not args.skip_proofread:
        proofreader = ProofreadAgent()
        segments = proofreader.proofread_segments(segments)
        cache.save_segments(video_id, "segments.zh.proofread", segments)

    segments_zh = segments
    segments_en = None

    if args.output_lang in {"en", "zh+en"}:
        cached_en = cache.load_segments(video_id, "segments.en")
        if cached_en is None:
            translator = TranslateAgent()
            segments_en = translator.translate_segments(segments_zh)
            cache.save_segments(video_id, "segments.en", segments_en)
        else:
            segments_en = cached_en

    # Render outputs
    if args.output_lang == "zh":
        (output_dir / f"{video_id}.zh.srt").write_text(render_srt(segments_zh), encoding="utf-8")
        (output_dir / f"{video_id}.zh.vtt").write_text(render_vtt(segments_zh), encoding="utf-8")
        (output_dir / f"{video_id}.transcript.md").write_text(
            render_transcript_markdown(segments_zh, title=meta.title), encoding="utf-8"
        )
    elif args.output_lang == "en":
        assert segments_en is not None
        (output_dir / f"{video_id}.en.srt").write_text(render_srt(segments_en), encoding="utf-8")
        (output_dir / f"{video_id}.en.vtt").write_text(render_vtt(segments_en), encoding="utf-8")
        (output_dir / f"{video_id}.transcript.en.md").write_text(
            render_transcript_markdown(segments_en, title=meta.title), encoding="utf-8"
        )
    else:  # zh+en
        assert segments_en is not None
        (output_dir / f"{video_id}.zh+en.srt").write_text(render_srt(segments_zh, segments_en=segments_en), encoding="utf-8")
        (output_dir / f"{video_id}.zh+en.vtt").write_text(render_vtt(segments_zh, segments_en=segments_en), encoding="utf-8")
        (output_dir / f"{video_id}.transcript.zh+en.md").write_text(
            render_transcript_markdown(segments_zh, segments_en=segments_en, title=meta.title), encoding="utf-8"
        )

    # Summary
    if not args.skip_summary:
        summary_agent = SummarizeAgent()
        summary = summary_agent.summarize(segments_zh, title=meta.title).summary
        (output_dir / f"{video_id}.summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md = ["# Summary", ""]
        for kp in summary.get("key_points", []) or []:
            md.append(f"- {kp}")
        md.append("")
        (output_dir / f"{video_id}.summary.md").write_text("\n".join(md), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

