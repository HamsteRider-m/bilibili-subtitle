from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="bilibili_subtitle",
        description="Extract subtitles from Bilibili videos",
    )
    parser.add_argument("url", help="Bilibili URL or BV ID")
    parser.add_argument("--output-dir", "-o", default="./output", help="Output directory")
    parser.add_argument("--output-lang", default="zh", choices=["zh", "en", "zh+en"])
    parser.add_argument("--skip-proofread", action="store_true", help="Skip proofreading")
    parser.add_argument("--skip-summary", action="store_true", help="Skip summarization")
    parser.add_argument("--cache-dir", default="./.cache", help="Cache directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Detect subtitles
    if args.verbose:
        print(f"⏳ 检测视频字幕: {args.url}")

    from .detector import detect_subtitles
    ref, meta = detect_subtitles(args.url, cache_dir)

    if args.verbose:
        print(f"✅ 视频ID: {meta.video_id}")
        print(f"   标题: {meta.title}")
        print(f"   有字幕: {meta.has_subtitle}")
        print(f"   AI字幕: {meta.has_ai_subtitle}")

    # Step 2: Get segments
    from .segment import Segment
    segments: list[Segment] = []

    if meta.has_subtitle and meta.subtitle_files:
        if args.verbose:
            print(f"⏳ 加载字幕文件: {meta.subtitle_files[0]}")
        from .subtitle_loader import load_segments_from_subtitle_file
        segments = load_segments_from_subtitle_file(meta.subtitle_files[0])
        if args.verbose:
            print(f"✅ 加载 {len(segments)} 个字幕段落")
    else:
        if args.verbose:
            print("⏳ 无字幕，下载音频进行转录...")
        from .audio_extractor import extract_audio
        audio_path = extract_audio(args.url, cache_dir)
        if args.verbose:
            print(f"✅ 音频下载完成: {audio_path}")
            print("⏳ ASR 转录中...")
        from .agents.transcribe_agent import TranscribeAgent
        agent = TranscribeAgent(mode="qwen")
        result = agent.transcribe(str(audio_path))
        segments = result.segments
        if args.verbose:
            print(f"✅ 转录完成，{len(segments)} 个段落")

    if not segments:
        print("❌ 未获取到任何字幕内容", file=sys.stderr)
        return 1

    # Step 3: Proofread (optional)
    if not args.skip_proofread:
        if args.verbose:
            print("⏳ 校对字幕...")
        from .agents.proofread_agent import ProofreadAgent
        proofreader = ProofreadAgent(mode="anthropic")
        pr_result = proofreader.proofread(segments)
        segments = pr_result.segments
        if args.verbose:
            print(f"✅ 校对完成，修改 {len(pr_result.changes)} 处")

    # Step 4: Render outputs
    video_id = meta.video_id
    if args.verbose:
        print("⏳ 生成输出文件...")

    from .renderers.srt import render_srt
    from .renderers.vtt import render_vtt
    from .renderers.markdown import render_markdown

    srt_path = output_dir / f"{video_id}.zh.srt"
    srt_path.write_text(render_srt(segments), encoding="utf-8")

    vtt_path = output_dir / f"{video_id}.zh.vtt"
    vtt_path.write_text(render_vtt(segments), encoding="utf-8")

    md_path = output_dir / f"{video_id}.transcript.md"
    md_path.write_text(render_markdown(segments, title=meta.title), encoding="utf-8")

    if args.verbose:
        print(f"✅ SRT: {srt_path}")
        print(f"✅ VTT: {vtt_path}")
        print(f"✅ MD:  {md_path}")

    # Step 5: Summarize (optional)
    if not args.skip_summary:
        if args.verbose:
            print("⏳ 生成摘要...")
        from .agents.summarize_agent import SummarizeAgent
        summarizer = SummarizeAgent(mode="anthropic")
        sum_result = summarizer.summarize(segments, title=meta.title)

        json_path = output_dir / f"{video_id}.summary.json"
        json_path.write_text(
            json.dumps(sum_result.summary, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        summary_md = _summary_to_markdown(sum_result.summary, meta.title)
        summary_md_path = output_dir / f"{video_id}.summary.md"
        summary_md_path.write_text(summary_md, encoding="utf-8")

        if args.verbose:
            print(f"✅ Summary JSON: {json_path}")
            print(f"✅ Summary MD:   {summary_md_path}")

    print(f"\n✅ Done! 输出目录: {output_dir}")
    return 0


def _summary_to_markdown(summary: dict, title: str | None) -> str:
    lines = []
    if title:
        lines.append(f"# {title}\n")

    if kp := summary.get("key_points"):
        lines.append("## 要点\n")
        for p in kp:
            lines.append(f"- {p}")
        lines.append("")

    if outline := summary.get("outline"):
        lines.append("## 大纲\n")
        for item in outline:
            if isinstance(item, dict):
                lines.append(f"- {item.get('title', item)}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
