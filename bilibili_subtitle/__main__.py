from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents.proofread_agent import ProofreadAgent
from .agents.summarize_agent import SummarizeAgent
from .agents.translate_agent import TranslateAgent
from .audio_extractor import extract_audio
from .cache import Cache
from .chunker import chunk_audio_ffmpeg
from .detector import detect_subtitles
from .merger import ChunkTranscript, merge_chunk_transcripts
from .renderers.markdown import render_transcript_markdown
from .renderers.srt import render_srt
from .renderers.vtt import render_vtt
from .subtitle_loader import load_segments_from_subtitle_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bilibili-subtitle")
    parser.add_argument("url", help="Bilibili video URL, BV id, or av id")
    parser.add_argument("--output-dir", default="./output")
    parser.add_argument("--output-lang", default="zh", choices=["zh", "en", "zh+en"])
    parser.add_argument("--skip-proofread", action="store_true")
    parser.add_argument("--skip-summary", action="store_true")
    parser.add_argument("--cache-dir", default="./.cache")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache = Cache(args.cache_dir)

    ref, meta = detect_subtitles(args.url, output_dir)
    if args.verbose:
        print(f"Video: {meta.video_id}, Title: {meta.title}")
        print(f"Has subtitle: {meta.has_subtitle}, AI subtitle: {meta.has_ai_subtitle}")

    video_id = meta.video_id or ref.video_id or "unknown"

    if meta.has_subtitle:
        cached = cache.load_segments(video_id, "segments.zh")
        if cached is None:
            if not meta.subtitle_files:
                raise RuntimeError(
                    "Subtitle detection succeeded but no SRT file found."
                )
            segments = load_segments_from_subtitle_file(meta.subtitle_files[0])
            cache.save_segments(video_id, "segments.zh", segments)
        else:
            segments = cached
    else:
        audio_path = extract_audio(args.url, output_dir)
        chunks = chunk_audio_ffmpeg(audio_path, output_dir / "chunks")

        from .agents.transcribe_agent import TranscribeAgent

        transcriber = TranscribeAgent()
        transcripts: list[ChunkTranscript] = []
        for chunk in chunks:
            result = transcriber.transcribe(str(chunk.path))
            transcripts.append(
                ChunkTranscript(chunk_start_ms=chunk.start_ms, segments=result.segments)
            )
        segments = merge_chunk_transcripts(
            transcripts, overlap_ms=2000, similarity_threshold=0.8
        )
        cache.save_segments(video_id, "segments.zh", segments)

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

    _render_outputs(
        output_dir, video_id, meta.title, args.output_lang, segments_zh, segments_en
    )

    if not args.skip_summary:
        _generate_summary(output_dir, video_id, meta.title, segments_zh)

    return 0


def _render_outputs(
    output_dir: Path,
    video_id: str,
    title: str | None,
    output_lang: str,
    segments_zh: list,
    segments_en: list | None,
) -> None:
    if output_lang == "zh":
        (output_dir / f"{video_id}.zh.srt").write_text(
            render_srt(segments_zh), encoding="utf-8"
        )
        (output_dir / f"{video_id}.zh.vtt").write_text(
            render_vtt(segments_zh), encoding="utf-8"
        )
        (output_dir / f"{video_id}.transcript.md").write_text(
            render_transcript_markdown(segments_zh, title=title), encoding="utf-8"
        )
    elif output_lang == "en":
        assert segments_en is not None
        (output_dir / f"{video_id}.en.srt").write_text(
            render_srt(segments_en), encoding="utf-8"
        )
        (output_dir / f"{video_id}.en.vtt").write_text(
            render_vtt(segments_en), encoding="utf-8"
        )
        (output_dir / f"{video_id}.transcript.en.md").write_text(
            render_transcript_markdown(segments_en, title=title), encoding="utf-8"
        )
    else:  # zh+en
        assert segments_en is not None
        (output_dir / f"{video_id}.zh+en.srt").write_text(
            render_srt(segments_zh, segments_en=segments_en), encoding="utf-8"
        )
        (output_dir / f"{video_id}.zh+en.vtt").write_text(
            render_vtt(segments_zh, segments_en=segments_en), encoding="utf-8"
        )
        (output_dir / f"{video_id}.transcript.zh+en.md").write_text(
            render_transcript_markdown(
                segments_zh, segments_en=segments_en, title=title
            ),
            encoding="utf-8",
        )


def _generate_summary(
    output_dir: Path, video_id: str, title: str | None, segments_zh: list
) -> None:
    summary_agent = SummarizeAgent()
    summary = summary_agent.summarize(segments_zh, title=title).summary
    (output_dir / f"{video_id}.summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = ["# Summary", ""]
    for kp in summary.get("key_points", []) or []:
        md.append(f"- {kp}")
    md.append("")
    (output_dir / f"{video_id}.summary.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
